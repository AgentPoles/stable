import pytest
from unittest.mock import AsyncMock, patch
from src.api.client import SnapshotClient
from src.models import Proposal, VaryingChoices

@pytest.mark.asyncio
async def test_fetch_proposals(mock_proposal):
    """Test fetching proposals."""
    mock_response = {
        "data": {
            "proposals": [mock_proposal]
        }
    }
    
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_post.return_value.__aenter__.return_value.status = 200
        mock_post.return_value.__aenter__.return_value.json = AsyncMock(return_value=mock_response)
        
        async with SnapshotClient() as client:
            proposals = await client.fetch_proposals(["aave.eth"])
            
            assert len(proposals) == 1
            assert isinstance(proposals[0], Proposal)
            assert proposals[0].id == "test-proposal-1"

@pytest.mark.asyncio
async def test_fetch_proposals_with_varying_choices(mock_varying_choices):
    """Test fetching proposals with varying choices."""
    mock_response = {
        "data": {
            "votes": [
                {
                    "proposal": {
                        "id": "test-proposal-1",
                        "choices": ["For", "Against", "Abstain"]
                    },
                    "choice": 1,
                    "voter": "0x123"
                },
                {
                    "proposal": {
                        "id": "test-proposal-1",
                        "choices": ["For", "Against", "Abstain"]
                    },
                    "choice": 2,
                    "voter": "0x456"
                }
            ]
        }
    }
    
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_post.return_value.__aenter__.return_value.status = 200
        mock_post.return_value.__aenter__.return_value.json = AsyncMock(return_value=mock_response)
        
        async with SnapshotClient() as client:
            varying_choices = await client.fetch_proposals_with_varying_choices(
                ["test-proposal-1"],
                ["0x123", "0x456"]
            )
            
            assert len(varying_choices) == 1
            assert isinstance(varying_choices[0], VaryingChoices)
            assert varying_choices[0].proposal_id == "test-proposal-1"
            assert varying_choices[0].voter_choices == {"0x123": 1, "0x456": 2}

@pytest.mark.asyncio
async def test_fetch_proposals_error_handling():
    """Test error handling in fetch_proposals."""
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_post.return_value.__aenter__.return_value.status = 500
        
        async with SnapshotClient() as client:
            proposals = await client.fetch_proposals(["aave.eth"])
            assert len(proposals) == 0 