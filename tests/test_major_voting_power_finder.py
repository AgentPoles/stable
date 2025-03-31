import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.services.major_voting_power_finder import MajorVotingPowerFinder
from src.api.client import SnapshotClient
from src.models import Proposal

@pytest.fixture
async def mock_client():
    """Create a mock client with proper async cleanup."""
    client = AsyncMock(spec=SnapshotClient)
    
    # Create a mock session with proper state
    session = AsyncMock()
    session.closed = True
    session.close = AsyncMock()
    client.session = session

    # Setup context manager methods
    async def mock_aenter():
        client.session.closed = False
        return client

    async def mock_aexit(exc_type=None, exc_val=None, exc_tb=None):
        await client.session.close()
        client.session.closed = True
        return None

    client.__aenter__ = AsyncMock(side_effect=mock_aenter)
    client.__aexit__ = AsyncMock(side_effect=mock_aexit)

    # Setup real method implementations
    async def mock_fetch_proposals(spaces, skip=0):
        if isinstance(client.fetch_proposals.side_effect, list):
            if skip >= len(client.fetch_proposals.side_effect):
                return []
            result = client.fetch_proposals.side_effect[skip]
            return result if result is not None else []
        elif client.fetch_proposals.return_value is not None:
            return [] if skip > 0 else client.fetch_proposals.return_value
        return []

    async def mock_fetch_votes_sorted_by_voting_power(proposal_ids, skip=0, first=None):
        if isinstance(client.fetch_votes_sorted_by_voting_power.side_effect, list):
            if skip >= len(client.fetch_votes_sorted_by_voting_power.side_effect):
                return []
            result = client.fetch_votes_sorted_by_voting_power.side_effect[skip]
            return result if result is not None else []
        elif client.fetch_votes_sorted_by_voting_power.return_value is not None:
            return client.fetch_votes_sorted_by_voting_power.return_value
        return []

    async def mock_fetch_target_votes(proposal_ids, voter):
        if isinstance(client.fetch_target_votes.side_effect, list):
            return client.fetch_target_votes.side_effect[0] if client.fetch_target_votes.side_effect else []
        return client.fetch_target_votes.return_value if client.fetch_target_votes.return_value is not None else []

    # Attach the mock implementations
    client.fetch_proposals.side_effect = mock_fetch_proposals
    client.fetch_votes_sorted_by_voting_power.side_effect = mock_fetch_votes_sorted_by_voting_power
    client.fetch_target_votes.side_effect = mock_fetch_target_votes

    yield client

    # Ensure cleanup
    if not client.session.closed:
        await client.session.close()
        client.session.closed = True
    await client.__aexit__(None, None, None)

@pytest.mark.asyncio
async def test_find_votes_against_majority(mock_proposal, mock_client):
    """Test finding votes against majority."""
    # Mock proposal fetch
    mock_client.fetch_proposals.return_value = [Proposal(**mock_proposal)]
    
    # Mock target votes fetch with correct structure - this confirms target voted
    target_vote = {
        "voter": "0xtargetaddress",
        "vp": 1000.0,
        "choice": 1,
        "proposal": {
            "id": "test-proposal-1",
            "choices": ["For", "Against", "Abstain"]
        }
    }
    mock_client.fetch_target_votes.return_value = [target_vote]
    
    # Mock votes fetch - only need highest power vote since we know target voted
    highest_power_vote = {
        "voter": "0xwhaleaddress",
        "vp": 2000.0,
        "choice": 2,
        "proposal": {
            "id": "test-proposal-1",
            "choices": ["For", "Against", "Abstain"]
        }
    }
    mock_client.fetch_votes_sorted_by_voting_power.return_value = [highest_power_vote]
    
    finder = MajorVotingPowerFinder(mock_client)
    result = await finder.find_votes_against_majority(
        space_ids=["aave.eth"],
        target_voter="0xtargetaddress"
    )
    
    assert result is not None
    assert result["proposal_id"] == "test-proposal-1"
    assert result["proposal_title"] == "Test Proposal"
    assert result["proposal_created"] == 1711234567
    assert result["target_vote"]["voter"] == "0xtargetaddress"
    assert result["highest_power_vote"]["voter"] == "0xwhaleaddress"
    assert result["target_vote"]["vp"] == 1000.0
    assert result["highest_power_vote"]["vp"] == 2000.0

@pytest.mark.asyncio
async def test_find_votes_against_majority_no_results(mock_proposal, mock_client):
    """Test finding votes when target is highest power voter."""
    # Mock proposal fetch with empty second page to stop pagination
    mock_client.fetch_proposals.side_effect = [
        [Proposal(**mock_proposal)],  # First page
        []  # Second page (empty)
    ]
    
    # Mock target votes fetch - this confirms target voted
    target_vote = {
        "voter": "0xtargetaddress",
        "vp": 2000.0,
        "choice": 1,
        "proposal": {
            "id": "test-proposal-1",
            "choices": ["For", "Against", "Abstain"]
        }
    }
    mock_client.fetch_target_votes.return_value = [target_vote]
    
    # Mock votes fetch - target is the highest power voter
    mock_client.fetch_votes_sorted_by_voting_power.return_value = [target_vote]
    
    finder = MajorVotingPowerFinder(mock_client)
    result = await finder.find_votes_against_majority(
        space_ids=["aave.eth"],
        target_voter="0xtargetaddress"
    )
    
    assert result is None  # Should return None when target is highest power voter
    assert mock_client.fetch_proposals.call_count == 2  # Two calls: first page and empty page
    assert mock_client.fetch_target_votes.call_count == 1  # One call to check votes
    assert mock_client.fetch_votes_sorted_by_voting_power.call_count == 1  # One call to check power

@pytest.mark.asyncio
async def test_find_votes_against_majority_error_handling(mock_client):
    """Test error handling in find_votes_against_majority."""
    # Mock fetch_proposals to raise an exception
    mock_client.fetch_proposals.side_effect = Exception("API Error")
    
    finder = MajorVotingPowerFinder(mock_client)
    
    # The implementation should handle the exception gracefully
    with pytest.raises(Exception) as exc_info:
        result = await finder.find_votes_against_majority(
            space_ids=["aave.eth"],
            target_voter="0xtargetaddress"
        )
    
    assert str(exc_info.value) == "API Error"
    mock_client.fetch_proposals.assert_called_once()

@pytest.mark.asyncio
async def test_find_votes_against_majority_pagination(mock_proposal, mock_client):
    """Test finding votes against majority with proposal pagination."""
    # Mock proposal fetch with pagination
    mock_client.fetch_proposals.side_effect = [
        [Proposal(**mock_proposal)],  # First page
        []  # Second page (empty to stop pagination)
    ]
    
    # Mock target votes fetch - this confirms target voted
    target_vote = {
        "voter": "0xtargetaddress",
        "vp": 1000.0,
        "choice": 1,
        "proposal": {
            "id": "test-proposal-1",
            "choices": ["For", "Against", "Abstain"]
        }
    }
    mock_client.fetch_target_votes.return_value = [target_vote]
    
    # Mock votes fetch - only need highest power vote since we know target voted
    highest_power_vote = {
        "voter": "0xwhaleaddress",
        "vp": 2000.0,
        "choice": 2,
        "proposal": {
            "id": "test-proposal-1",
            "choices": ["For", "Against", "Abstain"]
        }
    }
    mock_client.fetch_votes_sorted_by_voting_power.return_value = [highest_power_vote]
    
    finder = MajorVotingPowerFinder(mock_client)
    result = await finder.find_votes_against_majority(
        space_ids=["aave.eth"],
        target_voter="0xtargetaddress"
    )
    
    assert result is not None
    assert result["proposal_id"] == "test-proposal-1"
    assert result["target_vote"]["voter"] == "0xtargetaddress"
    assert result["highest_power_vote"]["voter"] == "0xwhaleaddress"
    assert mock_client.fetch_proposals.call_count == 1  # Only one page since we found result
    assert mock_client.fetch_target_votes.call_count == 1  # One batch of target votes
    assert mock_client.fetch_votes_sorted_by_voting_power.call_count == 1  # One batch of votes

@pytest.mark.asyncio
async def test_find_votes_against_majority_max_pagination(mock_proposal, mock_client):
    """Test pagination with no results found."""
    # Mock proposal fetch with multiple pages
    mock_client.fetch_proposals.side_effect = [
        [Proposal(**mock_proposal)],  # First page
        [Proposal(**mock_proposal)],  # Second page
        []  # Third page (empty to stop pagination)
    ]
    
    # Mock target votes fetch with no results
    mock_client.fetch_target_votes.return_value = []
    
    finder = MajorVotingPowerFinder(mock_client)
    result = await finder.find_votes_against_majority(
        space_ids=["aave.eth"],
        target_voter="0xtargetaddress"
    )
    
    assert result is None  # Should return None when no results found
    assert mock_client.fetch_proposals.call_count == 3  # Three pages of proposals
    assert mock_client.fetch_target_votes.call_count == 2  # Two attempts to find target votes
    assert mock_client.fetch_votes_sorted_by_voting_power.call_count == 0  # No votes fetched 