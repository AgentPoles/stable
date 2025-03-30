import pytest
from unittest.mock import AsyncMock, patch
from src.api.client import SnapshotClient
from src.models import Proposal, VaryingChoices, Vote, VoteResponse

@pytest.mark.asyncio
async def test_fetch_proposals(mock_proposal, mock_session):
    """Test fetching proposals."""
    mock_response = {
        "data": {
            "proposals": [mock_proposal]
        }
    }
    
    mock_session.post.return_value.__aenter__.return_value.json.return_value = mock_response
    
    with patch("aiohttp.ClientSession", return_value=mock_session):
        async with SnapshotClient() as client:
            proposals = await client.fetch_proposals(["aave.eth"])
            
            assert len(proposals) == 1
            assert isinstance(proposals[0], Proposal)
            assert proposals[0].id == "test-proposal-1"
            mock_session.post.assert_called_once()

@pytest.mark.asyncio
async def test_fetch_votes_and_choices(mock_vote, mock_session):
    """Test fetching votes and choices for a voter."""
    mock_response = {
        "data": {
            "votes": [mock_vote]
        }
    }
    
    mock_session.post.return_value.__aenter__.return_value.json.return_value = mock_response
    
    with patch("aiohttp.ClientSession", return_value=mock_session):
        async with SnapshotClient() as client:
            vote_responses = await client.fetch_votes_and_choices(
                ["test-proposal-1"],
                "0x123"
            )
            
            assert len(vote_responses) == 1
            assert isinstance(vote_responses[0], VoteResponse)
            assert vote_responses[0].proposal_id == "test-proposal-1"
            assert vote_responses[0].choice == 1
            assert vote_responses[0].choices == ["For", "Against", "Abstain"]
            mock_session.post.assert_called_once()

@pytest.mark.asyncio
async def test_fetch_proposals_with_varying_choices(mock_varying_choices, mock_session):
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
    
    mock_session.post.return_value.__aenter__.return_value.json.return_value = mock_response
    
    with patch("aiohttp.ClientSession", return_value=mock_session):
        async with SnapshotClient() as client:
            varying_choices = await client.fetch_proposals_with_varying_choices(
                ["test-proposal-1"],
                ["0x123", "0x456"]
            )
            
            assert len(varying_choices) == 1
            assert isinstance(varying_choices[0], VaryingChoices)
            assert varying_choices[0].proposal_id == "test-proposal-1"
            assert varying_choices[0].voter_choices == {"0x123": 1, "0x456": 2}
            mock_session.post.assert_called_once()

@pytest.mark.asyncio
async def test_fetch_proposals_error_handling(mock_session):
    """Test error handling in fetch_proposals."""
    mock_session.post.return_value.__aenter__.return_value.status = 500
    mock_session.post.return_value.__aenter__.return_value.json.return_value = {"data": None}
    
    with patch("aiohttp.ClientSession", return_value=mock_session):
        async with SnapshotClient() as client:
            proposals = await client.fetch_proposals(["aave.eth"])
            assert len(proposals) == 0
            mock_session.post.assert_called_once()

@pytest.mark.asyncio
async def test_client_session_management():
    """Test that client properly manages its session."""
    client = SnapshotClient()
    assert client.session is None
    
    async with client:
        assert client.session is not None
        assert not client.session.closed
    
    assert client.session is None 