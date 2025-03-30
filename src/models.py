from typing import List, Dict
from pydantic import BaseModel

class Proposal(BaseModel):
    """Represents a Snapshot proposal.
    
    Attributes:
        id: The unique identifier of the proposal
        choices: List of available voting choices (e.g., ["For", "Against", "Abstain"])
    """
    id: str
    choices: List[str]

class VaryingChoices(BaseModel):
    """Represents different voting choices for a proposal.
    
    Attributes:
        proposal_id: The unique identifier of the proposal
        voter_choices: Dictionary mapping voter addresses to their choices
        choices: List of available voting choices from the proposal
    """
    proposal_id: str
    voter_choices: Dict[str, int]
    choices: List[str]

    @classmethod
    def from_votes(
        cls, 
        proposal_id: str, 
        voter_choices: Dict[str, int], 
        proposal_choices: List[str]
    ) -> 'VaryingChoices':
        """Creates a VaryingChoices instance from vote data.
        
        Args:
            proposal_id: The ID of the proposal
            voter_choices: Dictionary of voter addresses to their choices
            proposal_choices: List of available choices for the proposal
            
        Returns:
            A new VaryingChoices instance
        """
        return cls(
            proposal_id=proposal_id,
            voter_choices=voter_choices,
            choices=proposal_choices
        ) 