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

    async def mock_fetch_votes_sorted_by_voting_power(proposal_id, skip=0, first=None):
        if isinstance(client.fetch_votes_sorted_by_voting_power.side_effect, list):
            if skip >= len(client.fetch_votes_sorted_by_voting_power.side_effect):
                return []
            result = client.fetch_votes_sorted_by_voting_power.side_effect[skip]
            return result if result is not None else []
        return []

    # Attach the mock implementations
    client.fetch_proposals.side_effect = mock_fetch_proposals
    client.fetch_votes_sorted_by_voting_power.side_effect = mock_fetch_votes_sorted_by_voting_power

    yield client

    # Ensure cleanup
    if not client.session.closed:
        await client.session.close()
        client.session.closed = True
    await client.__aexit__(None, None, None)

@pytest.mark.asyncio
async def test_find_votes_against_majority(mock_proposal, mock_majority_result, mock_client):
    """Test finding votes against majority."""
    # Mock proposal fetch
    mock_client.fetch_proposals.return_value = [Proposal(**mock_proposal)]
    
    # Mock votes fetch with pagination
    mock_client.fetch_votes_sorted_by_voting_power.side_effect = [
        [mock_majority_result["highest_power_vote"], mock_majority_result["target_vote"]],  # First page
        []  # Second page (empty)
    ]
    
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
    # Mock proposal fetch with pagination
    mock_client.fetch_proposals.side_effect = [
        [Proposal(**mock_proposal)],  # First page
        []  # Second page (empty to stop pagination)
    ]
    
    # Mock votes fetch with target as highest power voter
    mock_client.fetch_votes_sorted_by_voting_power.side_effect = [
        [
            {"voter": "0xtargetaddress", "vp": 2000.0, "choice": 1},
            {"voter": "0xwhaleaddress", "vp": 1000.0, "choice": 2}
        ],
        []  # Empty page to stop pagination
    ]
    
    finder = MajorVotingPowerFinder(mock_client)
    result = await finder.find_votes_against_majority(
        space_ids=["aave.eth"],
        target_voter="0xtargetaddress"
    )
    
    assert result is None  # Should return None when target is highest power voter
    assert mock_client.fetch_proposals.call_count == 2  # Initial page + empty page
    assert mock_client.fetch_votes_sorted_by_voting_power.call_count == 1  # Only first page needed

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
    mock_client.fetch_proposals.assert_called_once()  # Only check if fetch_proposals was called

@pytest.mark.asyncio
async def test_find_votes_against_majority_pagination(mock_proposal, mock_majority_result, mock_client):
    """Test finding votes against majority when target is in a later page."""
    # Mock proposal fetch with pagination
    mock_client.fetch_proposals.side_effect = [
        [Proposal(**mock_proposal)],  # First page
        []  # Second page (empty to stop pagination)
    ]
    
    # Mock votes fetch with pagination - target found in second page
    mock_client.fetch_votes_sorted_by_voting_power.side_effect = [
        [{"voter": "0xwhaleaddress", "vp": 2000.0, "choice": 1}],  # First page with highest power
        [
            {"voter": "0xotheraddress", "vp": 1500.0, "choice": 1},
            {"voter": "0xtargetaddress", "vp": 1000.0, "choice": 2}
        ],  # Second page with target
        []  # Third page (empty to stop pagination)
    ]
    
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
    assert result["target_vote"]["vp"] == 1000.0
    assert result["highest_power_vote"]["voter"] == "0xwhaleaddress"
    assert result["highest_power_vote"]["vp"] == 2000.0
    
    # Verify that we called fetch_votes_sorted_by_voting_power twice (first page and target page)
    assert mock_client.fetch_votes_sorted_by_voting_power.call_count == 2
    # Verify that we called fetch_proposals once (found in first page)
    assert mock_client.fetch_proposals.call_count == 1

@pytest.mark.asyncio
async def test_find_votes_against_majority_max_pagination(mock_proposal, mock_client):
    """Test that pagination stops after a reasonable number of pages."""
    # Mock proposal fetch with a single page
    mock_client.fetch_proposals.side_effect = [
        [Proposal(**mock_proposal)],  # First page
        []  # Empty page to stop proposal pagination
    ]
    
    # Mock votes fetch to never find the target but stop after a few pages
    mock_client.fetch_votes_sorted_by_voting_power.side_effect = [
        [{"voter": "0xwhaleaddress", "vp": 2000.0, "choice": 1}],  # First page with highest power
        [{"voter": "0xvoter1", "vp": 1500.0, "choice": 1}],  # Second page
        [{"voter": "0xvoter2", "vp": 1200.0, "choice": 1}],  # Third page
        []  # Empty page to stop vote pagination
    ]
    
    finder = MajorVotingPowerFinder(mock_client)
    result = await finder.find_votes_against_majority(
        space_ids=["aave.eth"],
        target_voter="0xtargetaddress"
    )
    
    assert result is None  # Should return None when target not found
    # Verify that we check a reasonable number of pages
    assert mock_client.fetch_proposals.call_count == 2  # Initial page + empty page
    assert mock_client.fetch_votes_sorted_by_voting_power.call_count == 4  # Three pages of votes + empty page 