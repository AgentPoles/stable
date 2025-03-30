"""Data models for the application."""
from typing import Dict, List
from pydantic import BaseModel
from dataclasses import dataclass

@dataclass
class Proposal:
    """Model for a Snapshot proposal."""
    id: str
    title: str
    choices: List[str]
    created: int  # Unix timestamp

class Vote(BaseModel):
    """Model representing a vote on a proposal."""
    proposal: Proposal
    choice: int
    voter: str

class VoteResponse(BaseModel):
    """Model representing a vote response."""
    proposal_id: str
    choice: int
    choices: List[str]

    @classmethod
    def from_vote(cls, vote: Vote) -> 'VoteResponse':
        """Create VoteResponse from a Vote."""
        return cls(
            proposal_id=vote.proposal.id,
            choice=vote.choice,
            choices=vote.proposal.choices
        )

class VaryingChoices(BaseModel):
    """Model representing proposals with different voting choices."""
    proposal_id: str
    title: str
    voter_choices: Dict[str, int]
    choices: List[str]

    @classmethod
    def from_votes(cls, proposal_id: str, title: str, voter_choices: Dict[str, int], proposal_choices: List[str]):
        """Create VaryingChoices from vote data."""
        return cls(
            proposal_id=proposal_id,
            title=title,
            voter_choices=voter_choices,
            choices=proposal_choices
        ) 