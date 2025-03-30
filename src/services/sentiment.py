"""
Service for analyzing the relationship between voting choices.
"""

from enum import Enum
from typing import Tuple

class ChoiceRelationship(Enum):
    """Enumeration of possible relationships between voting choices."""
    DIRECT_OPPOSITION = "direct_opposition"
    PARTIAL_OPPOSITION = "partial_opposition"
    INCONCLUSIVE = "inconclusive"
    DIFFERENT = "different"

class SentimentAnalyzer:
    """Service for analyzing voting choice relationships."""
    
    def analyze_choices(self, choice1: str, choice2: str) -> Tuple[ChoiceRelationship, str]:
        """
        Analyze the relationship between two voting choices.
        
        Args:
            choice1: First voting choice
            choice2: Second voting choice
            
        Returns:
            Tuple of (relationship, description)
        """
        choice1 = choice1.lower()
        choice2 = choice2.lower()
        
        if choice1 == choice2:
            return ChoiceRelationship.DIFFERENT, "Votes are identical"
            
        if choice1 == "yes" and choice2 == "no":
            return ChoiceRelationship.DIRECT_OPPOSITION, "Votes are directly opposing"
            
        if choice1 == "no" and choice2 == "yes":
            return ChoiceRelationship.DIRECT_OPPOSITION, "Votes are directly opposing"
            
        if choice1 == "abstain" or choice2 == "abstain":
            return ChoiceRelationship.PARTIAL_OPPOSITION, "One party took a clear position while the other remained neutral"
            
        return ChoiceRelationship.INCONCLUSIVE, "It is not clear if the votes are opposing or not" 