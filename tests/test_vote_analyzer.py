import pytest
from unittest.mock import Mock, patch
from src.vote_analyzer import VoteAnalyzer
from src.tally_client import TallyClient

@pytest.fixture
def vote_analyzer():
    mock_client = Mock(spec=TallyClient)
    return VoteAnalyzer(mock_client)

def test_find_opposing_votes(vote_analyzer):
    # Mock whale votes
    whale_votes = {
        "edges": [
            {
                "node": {
                    "id": "vote1",
                    "proposal": {
                        "id": "1",
                        "title": "Test Proposal"
                    },
                    "type": "for",
                    "amount": "1000000000000000000"
                }
            }
        ]
    }
    
    # Mock proposal details with opposing StableLab vote
    mock_proposal = {
        "id": "1",
        "title": "Test Proposal",
        "votes": [
            {
                "voter": {"address": "0x123"},
                "type": "against",
                "amount": "500000000000000000"
            }
        ]
    }
    
    vote_analyzer.tally_client.get_proposal_details.return_value = mock_proposal
    
    stablelab_addresses = ["0x123"]
    results = vote_analyzer.find_opposing_votes(whale_votes, stablelab_addresses)
    
    assert len(results) == 1
    assert results[0]["proposal_id"] == "1"
    assert results[0]["whale_vote"] == "for"
    assert results[0]["stablelab_vote"] == "against"

def test_no_opposing_votes(vote_analyzer):
    # Mock whale votes
    whale_votes = {
        "edges": [
            {
                "node": {
                    "id": "vote1",
                    "proposal": {
                        "id": "1",
                        "title": "Test Proposal"
                    },
                    "type": "for",
                    "amount": "1000000000000000000"
                }
            }
        ]
    }
    
    # Mock proposal details with same vote type
    mock_proposal = {
        "id": "1",
        "title": "Test Proposal",
        "votes": [
            {
                "voter": {"address": "0x123"},
                "type": "for",
                "amount": "500000000000000000"
            }
        ]
    }
    
    vote_analyzer.tally_client.get_proposal_details.return_value = mock_proposal
    
    stablelab_addresses = ["0x123"]
    results = vote_analyzer.find_opposing_votes(whale_votes, stablelab_addresses)
    
    assert len(results) == 0

def test_different_proposals(vote_analyzer):
    # Mock whale votes for multiple proposals
    whale_votes = {
        "edges": [
            {
                "node": {
                    "id": "vote1",
                    "proposal": {
                        "id": "1",
                        "title": "Proposal 1"
                    },
                    "type": "for",
                    "amount": "1000000000000000000"
                }
            },
            {
                "node": {
                    "id": "vote2",
                    "proposal": {
                        "id": "2",
                        "title": "Proposal 2"
                    },
                    "type": "against",
                    "amount": "1000000000000000000"
                }
            }
        ]
    }
    
    # Mock proposal details with different votes
    mock_proposals = [
        {
            "id": "1",
            "title": "Proposal 1",
            "votes": [
                {
                    "voter": {"address": "0x123"},
                    "type": "against",
                    "amount": "500000000000000000"
                }
            ]
        },
        {
            "id": "2",
            "title": "Proposal 2",
            "votes": [
                {
                    "voter": {"address": "0x123"},
                    "type": "for",
                    "amount": "500000000000000000"
                }
            ]
        }
    ]
    
    vote_analyzer.tally_client.get_proposal_details.side_effect = mock_proposals
    
    stablelab_addresses = ["0x123"]
    results = vote_analyzer.find_opposing_votes(whale_votes, stablelab_addresses)
    
    assert len(results) == 2
    assert results[0]["proposal_id"] == "1"
    assert results[0]["whale_vote"] == "for"
    assert results[0]["stablelab_vote"] == "against"
    assert results[1]["proposal_id"] == "2"
    assert results[1]["whale_vote"] == "against"
    assert results[1]["stablelab_vote"] == "for" 