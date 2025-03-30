import pytest
from unittest.mock import AsyncMock, patch
from src.services.discord_finder import DiscordFinder
from src.api.client import SnapshotClient
from src.models import Proposal, VaryingChoices

@pytest.mark.asyncio
async def test_find_discords(mock_proposal, mock_varying_choices):
    """Test finding discords between parties."""
    mock_client = AsyncMock(spec=SnapshotClient)
    mock_client.fetch_proposals.return_value = [Proposal(**mock_proposal)]
    mock_client.fetch_proposals_with_varying_choices.return_value = [
        VaryingChoices(**mock_varying_choices)
    ]
    
    finder = DiscordFinder(mock_client)
    discords = await finder.find_discords(
        space_ids=["aave.eth"],
        parties=["0x123", "0x456"]
    )
    
    assert len(discords) == 1
    assert isinstance(discords[0], VaryingChoices)
    assert discords[0].proposal_id == "test-proposal-1"
    assert discords[0].voter_choices == {"0x123": 1, "0x456": 2}

@pytest.mark.asyncio
async def test_find_discords_no_results():
    """Test finding discords when no results are found."""
    mock_client = AsyncMock(spec=SnapshotClient)
    mock_client.fetch_proposals.return_value = []
    mock_client.fetch_proposals_with_varying_choices.return_value = []
    
    finder = DiscordFinder(mock_client)
    discords = await finder.find_discords(
        space_ids=["aave.eth"],
        parties=["0x123", "0x456"]
    )
    
    assert len(discords) == 0

@pytest.mark.asyncio
async def test_find_discords_error_handling():
    """Test error handling in find_discords."""
    mock_client = AsyncMock(spec=SnapshotClient)
    mock_client.fetch_proposals.side_effect = Exception("API Error")
    
    finder = DiscordFinder(mock_client)
    with pytest.raises(Exception):
        await finder.find_discords(
            space_ids=["aave.eth"],
            parties=["0x123", "0x456"]
        ) 