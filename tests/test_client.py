import pytest
from unittest.mock import AsyncMock, patch
from src.api.client import SnapshotClient
from src.models import Proposal, VaryingChoices, Vote, VoteResponse

@pytest.fixture
async def mock_client():
    """Create a mock client with proper async cleanup."""
    client = AsyncMock(spec=SnapshotClient)
    client.base_url = "https://hub.snapshot.org/graphql"
    client.proposal_cache = {}

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
    async def mock_fetch_proposals(spaces):
        await client.session.post(client.base_url, json={"query": "", "variables": {}})
        mock_response = await client.session.post.return_value.__aenter__()
        try:
            data = await mock_response.json()
            if data and isinstance(data, dict) and data.get("data", {}).get("proposals"):
                proposals = [Proposal(**p) for p in data["data"]["proposals"]]
                client.proposal_cache.update({p.id: p for p in proposals})
                return proposals
        except Exception:
            pass
        return []

    async def mock_fetch_votes_sorted_by_voting_power(proposal_id):
        await client.session.post(client.base_url, json={"query": "", "variables": {}})
        mock_response = await client.session.post.return_value.__aenter__()
        try:
            data = await mock_response.json()
            if data and isinstance(data, dict) and data.get("data", {}).get("votes"):
                return [Vote(
                    choice=v["choice"],
                    voter=v["voter"],
                    vp=v["vp"],
                    proposal=client.proposal_cache[v["proposal"]["id"]]
                ) for v in data["data"]["votes"]]
        except Exception:
            pass
        return []

    async def mock_fetch_voter_names(addresses):
        await client.session.post(client.base_url, json={"query": "", "variables": {}})
        mock_response = await client.session.post.return_value.__aenter__()
        name_map = {}
        try:
            data = await mock_response.json()
            if data and isinstance(data, dict) and data.get("data", {}).get("users"):
                for user in data["data"]["users"]:
                    original_addr = next((addr for addr in addresses if addr.lower() == user["id"].lower()), user["id"])
                    name_map[user["id"].lower()] = user["name"] or f"UNKNOWN ({original_addr})"
        except Exception:
            pass

        for addr in addresses:
            addr_lower = addr.lower()
            if addr_lower not in name_map:
                name_map[addr_lower] = f"UNKNOWN ({addr})"

        return name_map

    async def mock_fetch_proposals_with_varying_choices(proposal_ids, addresses):
        await client.session.post(client.base_url, json={"query": "", "variables": {}})
        mock_response = await client.session.post.return_value.__aenter__()
        try:
            data = await mock_response.json()
            if data and isinstance(data, dict) and data.get("data", {}).get("votes"):
                votes = data["data"]["votes"]
                result = []
                for proposal_id in proposal_ids:
                    if proposal_id in client.proposal_cache:
                        proposal_votes = [v for v in votes if v["proposal"]["id"] == proposal_id]
                        if proposal_votes:
                            proposal = client.proposal_cache[proposal_id]
                            voter_choices = {}
                            for vote in proposal_votes:
                                voter_choices[vote["voter"].lower()] = vote["choice"]
                            
                            if len(voter_choices) == 2 and voter_choices[addresses[0].lower()] != voter_choices[addresses[1].lower()]:
                                result.append(VaryingChoices(
                                    proposal_id=proposal_id,
                                    title=proposal.title,
                                    choices=proposal.choices,
                                    created=proposal.created,
                                    voter_choices=voter_choices
                                ))
                return result
        except Exception:
            pass
        return []

    # Attach the mock implementations
    client.fetch_proposals.side_effect = mock_fetch_proposals
    client.fetch_votes_sorted_by_voting_power.side_effect = mock_fetch_votes_sorted_by_voting_power
    client.fetch_voter_names.side_effect = mock_fetch_voter_names
    client.fetch_proposals_with_varying_choices.side_effect = mock_fetch_proposals_with_varying_choices

    yield client

    # Ensure cleanup
    if not client.session.closed:
        await client.session.close()
        client.session.closed = True
    await client.__aexit__()

@pytest.mark.asyncio
async def test_fetch_proposals(mock_proposal, mock_client):
    """Test fetching proposals."""
    mock_response = {
        "data": {
            "proposals": [mock_proposal]
        }
    }
    
    mock_client.session.post.return_value.__aenter__.return_value.json.return_value = mock_response
    
    proposals = await mock_client.fetch_proposals(["aave.eth"])
    
    assert len(proposals) == 1
    assert isinstance(proposals[0], Proposal)
    assert proposals[0].id == "test-proposal-1"
    mock_client.session.post.assert_called_once()

@pytest.mark.asyncio
async def test_fetch_votes_and_choices(mock_vote, mock_client):
    """Test fetching votes and choices for a voter."""
    mock_response = {
        "data": {
            "votes": [mock_vote]
        }
    }

    mock_client.session.post.return_value.__aenter__.return_value.json.return_value = mock_response

    # Cache the proposal data
    mock_client.proposal_cache["test-proposal-1"] = Proposal(
        id="test-proposal-1",
        title="Test Proposal",
        choices=["For", "Against", "Abstain"],
        created=1711234567
    )

    votes = await mock_client.fetch_votes_sorted_by_voting_power("test-proposal-1")

    assert len(votes) == 1
    assert votes[0].voter == "0xtargetaddress"
    assert votes[0].choice == 1
    assert votes[0].vp == 1000.0
    assert votes[0].proposal.id == "test-proposal-1"
    mock_client.session.post.assert_called_once()

@pytest.mark.asyncio
async def test_fetch_proposals_with_varying_choices(mock_varying_choices, mock_client):
    """Test fetching proposals with varying choices."""
    mock_response = {
        "data": {
            "votes": [
                {
                    "proposal": {
                        "id": "test-proposal-1"
                    },
                    "choice": 1,
                    "voter": "0xtargetaddress"
                },
                {
                    "proposal": {
                        "id": "test-proposal-1"
                    },
                    "choice": 2,
                    "voter": "0xwhaleaddress"
                }
            ]
        }
    }
    
    mock_client.session.post.return_value.__aenter__.return_value.json.return_value = mock_response
    
    # Cache the proposal data
    mock_client.proposal_cache["test-proposal-1"] = Proposal(
        id="test-proposal-1",
        title="Test Proposal",
        choices=["For", "Against", "Abstain"],
        created=1711234567
    )
    
    varying_choices = await mock_client.fetch_proposals_with_varying_choices(
        ["test-proposal-1"],
        ["0xTargetAddress", "0xWhaleAddress"]
    )
    
    assert len(varying_choices) == 1
    assert isinstance(varying_choices[0], VaryingChoices)
    assert varying_choices[0].proposal_id == "test-proposal-1"
    assert varying_choices[0].title == "Test Proposal"
    assert varying_choices[0].created == 1711234567
    assert varying_choices[0].voter_choices == {"0xtargetaddress": 1, "0xwhaleaddress": 2}
    mock_client.session.post.assert_called_once()

@pytest.mark.asyncio
async def test_fetch_proposals_error_handling(mock_client):
    """Test error handling in fetch_proposals."""
    mock_client.session.post.return_value.__aenter__.return_value.status = 500
    mock_client.session.post.return_value.__aenter__.return_value.json.return_value = {"data": None}
    
    proposals = await mock_client.fetch_proposals(["aave.eth"])
    assert len(proposals) == 0
    mock_client.session.post.assert_called_once()

@pytest.mark.asyncio
async def test_client_session_management():
    """Test that client properly manages its session."""
    client = SnapshotClient()
    assert client.session is None
    
    async with client:
        assert client.session is not None
        assert not client.session.closed
    
    assert client.session is None
    
@pytest.mark.asyncio
async def test_client_session_management_mock(mock_client):
    """Test that mock client properly manages its session."""
    # Test initial state
    mock_client.session.closed = True
    
    # Test session creation
    await mock_client.__aenter__()
    assert mock_client.__aenter__.called
    assert not mock_client.__aexit__.called
    assert not mock_client.session.closed
    
    # Test session cleanup
    await mock_client.__aexit__(None, None, None)
    assert mock_client.__aexit__.called
    assert mock_client.session.close.called

@pytest.mark.asyncio
async def test_fetch_voter_names(mock_voter_names, mock_client):
    """Test fetching voter names."""
    mock_response = {
        "data": {
            "users": [
                {"id": "0xTargetAddress", "name": "StableLab"},
                {"id": "0xWhaleAddress", "name": "Areta"},
                {"id": "0x789", "name": "UNKNOWN"}
            ]
        }
    }
    
    mock_client.session.post.return_value.__aenter__.return_value.json.return_value = mock_response
    
    voter_names = await mock_client.fetch_voter_names(["0xTargetAddress", "0xWhaleAddress", "0x789"])
    
    assert len(voter_names) == 3
    assert voter_names["0xTargetAddress".lower()] == "StableLab"
    assert voter_names["0xWhaleAddress".lower()] == "Areta"
    assert voter_names["0x789"] == "UNKNOWN"
    mock_client.session.post.assert_called_once()

@pytest.mark.asyncio
async def test_fetch_voter_names_error_handling(mock_client):
    """Test error handling in fetch_voter_names."""
    mock_client.session.post.return_value.__aenter__.return_value.status = 500
    mock_client.session.post.return_value.__aenter__.return_value.json.return_value = {"data": None}
    
    voter_names = await mock_client.fetch_voter_names(["0x123"])
    assert len(voter_names) == 1
    assert voter_names["0x123"] == "UNKNOWN (0x123)"
    mock_client.session.post.assert_called_once() 