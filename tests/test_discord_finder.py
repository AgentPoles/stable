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
    # Simulate pagination: first call returns a proposal, second call returns empty list
    mock_client.fetch_proposals.side_effect = [
        [Proposal(**mock_proposal)],  # First page
        []  # Second page (empty)
    ]
    # Same for varying choices
    mock_client.fetch_proposals_with_varying_choices.side_effect = [
        [VaryingChoices(**mock_varying_choices)],  # First page
        []  # Second page (empty)
    ]
    
    with patch('src.services.discord_finder.RateLimiter', return_value=mock_rate_limiter):
        finder = DiscordFinder(mock_client)
        discords = await finder.find_discords(
            space_ids=["aave.eth"],
            parties=["0x123", "0x456"]
        )
        
        assert len(discords) == 1
        assert isinstance(discords[0], VaryingChoices)
        assert discords[0].proposal_id == "test-proposal-1"
        assert discords[0].voter_choices == {"0x123": 1, "0x456": 2}
        # Verify rate limiter was called for both API calls (2 calls each for pagination)
        assert mock_rate_limiter.acquire.call_count == 4
        assert mock_rate_limiter.release.call_count == 4

@pytest.mark.asyncio
async def test_find_discords_no_results(mock_rate_limiter):
    """Test finding discords when no results are found."""
    mock_client = AsyncMock(spec=SnapshotClient)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.fetch_proposals.return_value = []
    
    with patch('src.services.discord_finder.RateLimiter', return_value=mock_rate_limiter):
        finder = DiscordFinder(mock_client)
        discords = await finder.find_discords(
            space_ids=["aave.eth"],
            parties=["0x123", "0x456"]
        )
        
        assert len(discords) == 0
        mock_rate_limiter.acquire.assert_called_once()
        mock_rate_limiter.release.assert_called_once()

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
                parties=["0x123", "0x456"],
                max_retries=3
            )
        
        assert "Failed to fetch proposals after retries" in str(exc_info.value)
        assert mock_rate_limiter.acquire.call_count == 4  # Initial try + 3 retries
        assert mock_rate_limiter.release.call_count == 4 