import pytest
from src.models import Proposal, VaryingChoices

def test_proposal_creation(mock_proposal):
    """Test Proposal model creation."""
    proposal = Proposal(**mock_proposal)
    assert proposal.id == "test-proposal-1"
    assert proposal.choices == ["For", "Against", "Abstain"]

def test_varying_choices_creation(mock_varying_choices):
    """Test VaryingChoices model creation."""
    varying_choices = VaryingChoices(**mock_varying_choices)
    assert varying_choices.proposal_id == "test-proposal-1"
    assert varying_choices.voter_choices == {"0x123": 1, "0x456": 2}
    assert varying_choices.choices == ["For", "Against", "Abstain"]

def test_varying_choices_from_votes():
    """Test VaryingChoices creation from votes."""
    proposal_id = "test-proposal-1"
    voter_choices = {"0x123": 1, "0x456": 2}
    proposal_choices = ["For", "Against", "Abstain"]
    
    varying_choices = VaryingChoices.from_votes(
        proposal_id=proposal_id,
        voter_choices=voter_choices,
        proposal_choices=proposal_choices
    )
    
    assert varying_choices.proposal_id == proposal_id
    assert varying_choices.voter_choices == voter_choices
    assert varying_choices.choices == proposal_choices 