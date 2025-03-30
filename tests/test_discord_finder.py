import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.services.discord_finder import DiscordFinder, RateLimiter, DiscordFinderError
from src.api.client import SnapshotClient
from src.models import Proposal, VaryingChoices

@pytest.fixture
def mock_rate_limiter():
    """Create a mock rate limiter for testing."""
    limiter = MagicMock(spec=RateLimiter)
    limiter.acquire = AsyncMock()
    limiter.release = MagicMock()
    return limiter

@pytest.mark.asyncio
async def test_find_discords(mock_proposal, mock_varying_choices, mock_rate_limiter):
    """Test finding discords between parties."""
    mock_client = AsyncMock(spec=SnapshotClient)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    # Mock proposal fetch
    mock_client.fetch_proposals.return_value = [Proposal(**mock_proposal)]
    
    # Mock varying choices fetch with mock addresses
    mock_varying_choices_with_mock_addresses = {
        **mock_varying_choices,
        "voter_choices": {
            "0xTargetAddress": 1,
            "0xWhaleAddress": 2
        }
    }
    mock_client.fetch_proposals_with_varying_choices.return_value = [VaryingChoices(**mock_varying_choices_with_mock_addresses)]
    
    with patch('src.services.discord_finder.RateLimiter', return_value=mock_rate_limiter):
        finder = DiscordFinder(mock_client)
        discords = await finder.find_discords(
            space_ids=["aave.eth"],
            parties=["0xTargetAddress", "0xWhaleAddress"]
        )
        
        assert len(discords) == 1
        assert isinstance(discords[0], VaryingChoices)
        assert discords[0].proposal_id == "test-proposal-1"
        assert discords[0].voter_choices == {"0xTargetAddress": 1, "0xWhaleAddress": 2}
        # Verify rate limiter was called for both API calls
        assert mock_rate_limiter.acquire.call_count == 2
        assert mock_rate_limiter.release.call_count == 2

@pytest.mark.asyncio
async def test_find_discords_no_results(mock_proposal, mock_rate_limiter):
    """Test finding discords when no results are found."""
    mock_client = AsyncMock(spec=SnapshotClient)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    # Mock proposal fetch
    mock_client.fetch_proposals.return_value = [Proposal(**mock_proposal)]
    
    # Mock varying choices fetch with no results
    mock_client.fetch_proposals_with_varying_choices.return_value = []
    
    with patch('src.services.discord_finder.RateLimiter', return_value=mock_rate_limiter):
        finder = DiscordFinder(mock_client)
        discords = await finder.find_discords(
            space_ids=["aave.eth"],
            parties=["0xTargetAddress", "0xWhaleAddress"]
        )
        
        assert len(discords) == 0
        # Verify rate limiter was called for both API calls
        assert mock_rate_limiter.acquire.call_count == 2
        assert mock_rate_limiter.release.call_count == 2

@pytest.mark.asyncio
async def test_find_discords_error_handling(mock_rate_limiter):
    """Test error handling in find_discords."""
    mock_client = AsyncMock(spec=SnapshotClient)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.fetch_proposals.side_effect = Exception("API Error")
    
    with patch('src.services.discord_finder.RateLimiter', return_value=mock_rate_limiter):
        finder = DiscordFinder(mock_client)
        with pytest.raises(DiscordFinderError) as exc_info:
            await finder.find_discords(
                space_ids=["aave.eth"],
                parties=["0xTargetAddress", "0xWhaleAddress"],
                max_retries=3
            )
        
        assert "Failed to process batch after retries" in str(exc_info.value)
        assert mock_rate_limiter.acquire.call_count == 4  # Initial try + 3 retries
        assert mock_rate_limiter.release.call_count == 4 