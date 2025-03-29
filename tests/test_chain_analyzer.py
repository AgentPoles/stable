import pytest
from unittest.mock import Mock, patch
import json
from src.chain_analyzer import ChainAnalyzer

@pytest.fixture
def mock_stablelab_addresses():
    return {
        "addresses": [
            "0x123",
            "0x456"
        ]
    }

@pytest.fixture
def chain_analyzer(mock_stablelab_addresses):
    with patch('builtins.open', create=True) as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(mock_stablelab_addresses)
        with patch('src.chain_analyzer.TallyClient') as mock_tally:
            mock_client = Mock()
            mock_tally.return_value = mock_client
            analyzer = ChainAnalyzer()
            return analyzer

def test_analyze_chain(chain_analyzer):
    # Mock whale votes with pagination
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
        ],
        "pageInfo": {
            "hasNextPage": False,
            "endCursor": "cursor1"
        }
    }
    
    # Mock proposal details
    mock_proposal_1 = {
        "id": "1",
        "title": "Proposal 1",
        "votes": [
            {
                "voter": {"address": "0x123"},
                "type": "against",
                "amount": "500000000000000000"
            }
        ]
    }
    
    mock_proposal_2 = {
        "id": "2",
        "title": "Proposal 2",
        "votes": [
            {
                "voter": {"address": "0x456"},
                "type": "for",
                "amount": "500000000000000000"
            }
        ]
    }
    
    chain_analyzer.tally_client.get_votes_by_address.return_value = whale_votes
    chain_analyzer.tally_client.get_proposal_details.side_effect = [mock_proposal_1, mock_proposal_2]
    
    results = chain_analyzer.analyze_chain("ethereum")
    
    assert len(results) == 2
    assert all("chain" in vote for vote in results)
    assert all(vote["chain"] == "ethereum" for vote in results)

def test_no_opposing_votes(chain_analyzer):
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
            }
        ],
        "pageInfo": {
            "hasNextPage": False,
            "endCursor": "cursor1"
        }
    }
    
    mock_proposal = {
        "id": "1",
        "title": "Proposal 1",
        "votes": [
            {
                "voter": {"address": "0x123"},
                "type": "for",
                "amount": "500000000000000000"
            }
        ]
    }
    
    chain_analyzer.tally_client.get_votes_by_address.return_value = whale_votes
    chain_analyzer.tally_client.get_proposal_details.return_value = mock_proposal
    
    results = chain_analyzer.analyze_chain("ethereum")
    assert len(results) == 0

def test_error_handling(chain_analyzer):
    chain_analyzer.tally_client.get_votes_by_address.side_effect = Exception("API Error")
    
    results = chain_analyzer.analyze_chain("ethereum")
    assert isinstance(results, list)
    assert len(results) == 0

def test_analyze_all_chains(chain_analyzer):
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
            }
        ],
        "pageInfo": {
            "hasNextPage": False,
            "endCursor": "cursor1"
        }
    }
    
    mock_proposal = {
        "id": "1",
        "title": "Proposal 1",
        "votes": [
            {
                "voter": {"address": "0x123"},
                "type": "against",
                "amount": "500000000000000000"
            }
        ]
    }
    
    chain_analyzer.tally_client.get_votes_by_address.return_value = whale_votes
    chain_analyzer.tally_client.get_proposal_details.return_value = mock_proposal
    
    results = chain_analyzer.analyze_all_chains()
    assert isinstance(results, list)
    
    # Verify that get_votes_by_address was called for each chain
    assert chain_analyzer.tally_client.get_votes_by_address.call_count == len(chain_analyzer.chains) 