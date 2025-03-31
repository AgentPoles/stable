import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.services.reporter import Reporter, format_timestamp
from src.api.client import SnapshotClient
from src.models import Proposal, VaryingChoices
from src.services.sentiment import ChoiceRelationship

@pytest.fixture
async def mock_client():
    """Create a mock client with proper async cleanup."""
    client = AsyncMock(spec=SnapshotClient)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    yield client
    await client.__aexit__(None, None, None)

@pytest.mark.asyncio
async def test_generate_discord_reports(mock_client, mock_varying_choices):
    """Test generation of discord reports."""
    # Mock voter names with lowercase addresses
    mock_client.fetch_voter_names.return_value = {
        "0xtargetaddress": "Party1",
        "0xwhaleaddress": "Party2"
    }
    
    # Mock the finder to return a discord
    mock_finder = AsyncMock()
    mock_finder.find_discords.return_value = [VaryingChoices(**{
        **mock_varying_choices,
        "voter_choices": {"0xtargetaddress": 1, "0xwhaleaddress": 2}
    })]
    
    # Mock the sentiment analyzer
    mock_analyzer = MagicMock()
    mock_analyzer.analyze_choices.return_value = (ChoiceRelationship.DIRECT_OPPOSITION, "Direct opposition in voting choices")
    
    with patch('src.services.reporter.DiscordFinder', return_value=mock_finder), \
         patch('src.services.reporter.PARTIES', {"target": "0xtargetaddress", "whale": "0xwhaleaddress"}), \
         patch('src.services.reporter.SPACES', [{"space_id": "aave.eth", "name": "Aave"}]), \
         patch('src.services.reporter.SentimentAnalyzer', return_value=mock_analyzer):
        reporter = Reporter(mock_client)
        reports = await reporter.generate_reports()
        
        assert len(reports) >= 3  # Header, party names, and at least one report
        assert "PROPOSALS IN PROCESSED BATCH WITH DIFFERENT VOTE CHOICES" in reports[0]
        assert "Party1" in reports[1]
        assert "Party2" in reports[1]
        assert "target" in reports[1].lower()
        assert "whale" in reports[1].lower()
        assert "SENTIMENT" in reports[2]  # Check sentiment in the actual report
        assert "voted" in reports[2]  # Check voting details in the actual report
        assert mock_client.__aenter__.call_count == 2  # Called once for initial voter names and once for report generation
        assert mock_client.__aexit__.call_count == 2

@pytest.mark.asyncio
async def test_generate_majority_reports(mock_client, mock_majority_result):
    """Test generation of majority reports."""
    mock_client.fetch_voter_names.return_value = {
        "0xtargetaddress": "Target",
        "0xwhaleaddress": "Majority"
    }

    # Mock the finder to return a majority result
    mock_finder = AsyncMock()
    mock_finder.find_votes_against_majority.return_value = {
        'target_vote': {'voter': '0xtargetaddress', 'vp': 1000.0},
        'highest_power_vote': {'voter': '0xwhaleaddress', 'vp': 2000.0},
        'proposal_title': 'Test Proposal',
        'proposal_created': 1711234567
    }

    with patch('src.services.reporter.MajorVotingPowerFinder', return_value=mock_finder), \
         patch('src.services.reporter.PARTIES', {"target": "0xtargetaddress", "whale": "0xwhaleaddress"}), \
         patch('src.services.reporter.SPACES', [{"space_id": "aave.eth", "name": "Aave"}]):
        reporter = Reporter(mock_client)
        reports = await reporter.generate_majority_reports()

        assert len(reports) >= 2  # Should have header and at least one report
        assert "PROPOSALS WHERE TARGET IS NOT THE HIGHEST VOTING POWER VOTER" in reports[0]
        assert "Target" in reports[1]
        assert "Majority" in reports[1]
        assert "1000.0" in reports[1]  # Check for voting power values
        assert "2000.0" in reports[1]

@pytest.mark.asyncio
async def test_generate_reports_error_handling(mock_client):
    """Test error handling in report generation."""
    mock_client.fetch_voter_names.return_value = {
        "0xtargetaddress": "UNKNOWN",
        "0xwhaleaddress": "UNKNOWN"
    }
    
    # Mock the finder to return no results
    mock_finder = AsyncMock()
    mock_finder.find_discords.return_value = []
    
    with patch('src.services.reporter.DiscordFinder', return_value=mock_finder), \
         patch('src.services.reporter.PARTIES', {"target": "0xtargetaddress", "whale": "0xwhaleaddress"}), \
         patch('src.services.reporter.SPACES', [{"space_id": "aave.eth", "name": "Aave"}]):
        reporter = Reporter(mock_client)
        reports = await reporter.generate_reports()
        
        assert len(reports) >= 2  # Should have header and party names
        assert "PROPOSALS IN PROCESSED BATCH WITH DIFFERENT VOTE CHOICES" in reports[0]
        assert "UNKNOWN" in reports[1]  # Should show UNKNOWN for failed voter name fetch
        mock_client.__aenter__.assert_called_once()
        mock_client.__aexit__.assert_called_once()

def test_format_timestamp():
    """Test timestamp formatting."""
    timestamp = 1711234567  # March 23, 2024 UTC
    formatted = format_timestamp(timestamp)
    
    # Check that the date part is correct (in UTC)
    assert "March 23, 2024" in formatted
    
    # Check that the time part is in the correct format (HH:MM:SS)
    time_parts = formatted.split(" ")[-1].split(":")
    assert len(time_parts) == 3  # HH:MM:SS format
    assert all(part.isdigit() for part in time_parts)  # All parts should be digits
    assert 0 <= int(time_parts[0]) <= 23  # Hours should be between 0 and 23
    assert 0 <= int(time_parts[1]) <= 59  # Minutes should be between 0 and 59
    assert 0 <= int(time_parts[2]) <= 59  # Seconds should be between 0 and 59 