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
        "title": "Test Proposal",
        "choices": ["For", "Against", "Abstain"],
        "created": 1711234567  # March 23, 2025
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
        "voter": "0xtargetaddress",  # Note: lowercase for case-insensitive comparison
        "vp": 1000.0
    }

@pytest.fixture
def mock_varying_choices():
    """Create mock varying choices for testing."""
    return {
        "proposal_id": "test-proposal-1",
        "title": "Test Proposal",
        "voter_choices": {
            "0xtargetaddress": 1,  # Note: lowercase for case-insensitive comparison
            "0xwhaleaddress": 2  # Note: lowercase for case-insensitive comparison
        },
        "choices": ["For", "Against", "Abstain"],
        "created": 1711234567  # March 23, 2025
    }

@pytest.fixture
def mock_majority_result():
    """Create a mock majority voting power result."""
    return {
        'proposal_id': 'test-proposal-1',
        'proposal_title': 'Test Proposal',
        'proposal_created': 1711234567,
        'target_vote': {
            'voter': '0xtargetaddress',  # Note: lowercase for case-insensitive comparison
            'vp': 1000.0,
            'choice': 1
        },
        'highest_power_vote': {
            'voter': '0xwhaleaddress',  # Note: lowercase for case-insensitive comparison
            'vp': 2000.0,
            'choice': 2
        }
    }

@pytest.fixture
def mock_voter_names():
    """Create mock voter names for testing."""
    return {
        "0xtargetaddress": "StableLab",  # Note: lowercase for case-insensitive comparison
        "0xwhaleaddress": "Areta",  # Note: lowercase for case-insensitive comparison
        "0x789": "UNKNOWN"
    } 