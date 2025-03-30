import pytest
import aiohttp
from unittest.mock import AsyncMock

@pytest.fixture
def mock_session():
    """Create a mock aiohttp session for testing."""
    session = AsyncMock(spec=aiohttp.ClientSession)
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock()
    mock_response.__aenter__.return_value = mock_response
    session.post.return_value = mock_response
    return session

@pytest.fixture
def mock_proposal():
    """Create a mock proposal for testing."""
    return {
        "id": "test-proposal-1",
        "choices": ["For", "Against", "Abstain"]
    }

@pytest.fixture
def mock_vote():
    """Create a mock vote for testing."""
    return {
        "proposal": {
            "id": "test-proposal-1",
            "choices": ["For", "Against", "Abstain"]
        },
        "choice": 1,
        "voter": "0x123"
    }

@pytest.fixture
def mock_varying_choices():
    """Create mock varying choices for testing."""
    return {
        "proposal_id": "test-proposal-1",
        "voter_choices": {
            "0x123": 1,
            "0x456": 2
        },
        "choices": ["For", "Against", "Abstain"]
    } 