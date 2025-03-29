import pytest
from unittest.mock import patch, Mock
import os
from src.tally_client import TallyClient

@pytest.fixture
def tally_client():
    with patch.dict(os.environ, {"TALLY_API_KEY": "test_api_key"}):
        return TallyClient()

def test_tally_client_initialization(tally_client):
    assert tally_client.api_key == 'test_api_key'
    assert tally_client.base_url == "https://api.tally.so/graphql"
    assert tally_client.headers == {
        "Authorization": "Bearer test_api_key",
        "Content-Type": "application/json"
    }

def test_format_address(tally_client):
    assert tally_client._format_address("0x123") == "0x123"
    assert tally_client._format_address("0X123") == "0x123"
    assert tally_client._format_address("0x123ABC") == "0x123abc"

def test_get_votes_by_address(tally_client):
    mock_response = Mock()
    mock_response.json.return_value = {
        "data": {
            "votes": {
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
                ],
                "pageInfo": {
                    "hasNextPage": False,
                    "endCursor": "cursor1"
                }
            }
        }
    }
    mock_response.raise_for_status = Mock()

    with patch('requests.post', return_value=mock_response):
        result = tally_client.get_votes_by_address("0x123")
        assert result["edges"][0]["node"]["proposal"]["id"] == "1"

def test_get_proposal_details(tally_client):
    mock_response = Mock()
    mock_response.json.return_value = {
        "data": {
            "proposal": {
                "id": "1",
                "title": "Test Proposal",
                "votes": [
                    {
                        "voter": {"address": "0x123"},
                        "type": "for",
                        "amount": "1000000000000000000"
                    }
                ]
            }
        }
    }
    mock_response.raise_for_status = Mock()

    with patch('requests.post', return_value=mock_response):
        result = tally_client.get_proposal_details("1")
        assert result["id"] == "1"

def test_error_handling(tally_client):
    with patch('requests.post') as mock_post:
        mock_post.side_effect = Exception("Test Error")

        with pytest.raises(Exception) as exc_info:
            tally_client.get_votes_by_address("0x123")
        assert str(exc_info.value) == "API request failed: Test Error" 