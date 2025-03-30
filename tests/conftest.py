import pytest
import os
from dotenv import load_dotenv

@pytest.fixture(autouse=True)
def load_env():
    """Load environment variables for tests."""
    load_dotenv()

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