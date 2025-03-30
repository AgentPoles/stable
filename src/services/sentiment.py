"""
Service for analyzing voting choices and determining their relationship.
Handles case-insensitive matching and various common voting choice formats.
"""

from enum import Enum
from typing import Set, Tuple

class ChoiceType(Enum):
    """Enumeration of possible choice types."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    UNKNOWN = "unknown"

class ChoiceRelationship(Enum):
    """Enumeration of possible relationships between choices."""
    DIRECT_OPPOSITION = "direct_opposition"
    PARTIAL_OPPOSITION = "partial_opposition"
    INCONCLUSIVE = "inconclusive"
    DIFFERENT = "different"
    SAME = "same"

class SentimentAnalyzer:
    """Analyzes voting choices to determine their relationship."""
    
    POSITIVE_CHOICES: Set[str] = {
        "for", "yae", "yay", "yes"
    }
    
    NEGATIVE_CHOICES: Set[str] = {
        "against", "nay", "nae", "no"
    }
    
    NEUTRAL_CHOICES: Set[str] = {
        "abstain", "neutral", "nothing"
    }
    
    @classmethod
    def _normalize_choice(cls, choice: str) -> str:
        """Convert choice to lowercase and remove whitespace."""
        return choice.lower().strip()
    
    @classmethod
    def _get_choice_type(cls, choice: str) -> ChoiceType:
        """Determine the type of a voting choice."""
        normalized = cls._normalize_choice(choice)
        
        if normalized in cls.POSITIVE_CHOICES:
            return ChoiceType.POSITIVE
        elif normalized in cls.NEGATIVE_CHOICES:
            return ChoiceType.NEGATIVE
        elif normalized in cls.NEUTRAL_CHOICES:
            return ChoiceType.NEUTRAL
        else:
            return ChoiceType.UNKNOWN
    
    @classmethod
    def analyze_choices(cls, choice1: str, choice2: str) -> Tuple[ChoiceRelationship, str]:
        """
        Analyze two voting choices and determine their relationship.
        Results are prioritized in the following order:
        1. Direct opposition (positive vs negative)
        2. Partial opposition (with neutral)
        3. Inconclusive (with unknown)
        4. Different (not opposing)
        5. Same
        
        Args:
            choice1: First voting choice
            choice2: Second voting choice
            
        Returns:
            Tuple of (relationship, description)
        """
        norm1 = cls._normalize_choice(choice1)
        norm2 = cls._normalize_choice(choice2)
        
        if norm1 == norm2:
            return ChoiceRelationship.SAME, "Both parties voted the same way"
            
        type1 = cls._get_choice_type(choice1)
        type2 = cls._get_choice_type(choice2)
        
        # Priority 1: Direct opposition
        if (type1 == ChoiceType.POSITIVE and type2 == ChoiceType.NEGATIVE) or \
           (type1 == ChoiceType.NEGATIVE and type2 == ChoiceType.POSITIVE):
            return ChoiceRelationship.DIRECT_OPPOSITION, "Direct opposition in voting choices"
            
        # Priority 2: Partial opposition with neutral
        if (type1 in [ChoiceType.POSITIVE, ChoiceType.NEGATIVE] and type2 == ChoiceType.NEUTRAL) or \
           (type2 in [ChoiceType.POSITIVE, ChoiceType.NEGATIVE] and type1 == ChoiceType.NEUTRAL):
            return ChoiceRelationship.PARTIAL_OPPOSITION, "One party neutral while other took a position"
            
        # Priority 3: Inconclusive (with unknown)
        if type1 == ChoiceType.UNKNOWN or type2 == ChoiceType.UNKNOWN:
            return ChoiceRelationship.INCONCLUSIVE, "One or both choices not in knowledge base"
            
        # Priority 4: Different but not opposing
        return ChoiceRelationship.DIFFERENT, "Different voting choices but not directly opposing" 