"""
Service for generating reports about voting relationships between parties.
Uses DiscordFinder to find different votes and SentimentAnalyzer to determine relationships.
"""

from typing import List
from src.api.client import SnapshotClient
from src.services.discord_finder import DiscordFinder
from src.services.sentiment import SentimentAnalyzer, ChoiceRelationship
from src.models import VaryingChoices
from src.config import PARTIES, SPACES

class Reporter:
    """Service for generating reports about voting relationships."""
    
    def __init__(self, client: SnapshotClient):
        """Initialize the reporter with a SnapshotClient."""
        self.client = client
        self.finder = DiscordFinder(client)
        self.analyzer = SentimentAnalyzer()
        
    def _get_party_name(self, address: str) -> str:
        """Get party name from address."""
        for party in PARTIES:
            if party["address"].lower() == address.lower():
                return party["name"]
        return address
        
    def _get_space_name(self, space_id: str) -> str:
        """Get space name from space_id."""
        for space in SPACES:
            if space["space_id"] == space_id:
                return space["name"]
        return space_id
        
    def _generate_report(self, discord: VaryingChoices, space_id: str) -> str:
        """Generate a report for a single discord."""
        party1, party2 = list(discord.voter_choices.keys())
        choice1, choice2 = discord.voter_choices[party1], discord.voter_choices[party2]
        
        party1_name = self._get_party_name(party1)
        party2_name = self._get_party_name(party2)
        
        choice1_text = discord.choices[choice1 - 1]
        choice2_text = discord.choices[choice2 - 1]
        
        relationship, description = self.analyzer.analyze_choices(choice1_text, choice2_text)
        
        sentiment_emoji = {
            ChoiceRelationship.DIRECT_OPPOSITION: "😠",
            ChoiceRelationship.PARTIAL_OPPOSITION: "🤔",
            ChoiceRelationship.INCONCLUSIVE: "🤷",
            ChoiceRelationship.DIFFERENT: "😐"
        }.get(relationship, "😐")
        
        if relationship == ChoiceRelationship.DIRECT_OPPOSITION:
            return (
                f"\n📋 {discord.title}\n"
                f"─────────────────────────────\n"
                f"{party1_name} voted {choice1_text}, while {party2_name} voted {choice2_text}\n"
                f"SENTIMENT [{sentiment_emoji}]: votes are clearly opposing\n"
            )
        elif relationship == ChoiceRelationship.PARTIAL_OPPOSITION:
            return (
                f"\n📋 {discord.title}\n"
                f"─────────────────────────────\n"
                f"{party1_name} voted {choice1_text}, while {party2_name} voted {choice2_text}\n"
                f"SENTIMENT [{sentiment_emoji}]: one party took a clear position while the other remained neutral\n"
            )
        elif relationship == ChoiceRelationship.INCONCLUSIVE:
            return (
                f"\n📋 {discord.title}\n"
                f"─────────────────────────────\n"
                f"{party1_name} voted {choice1_text}, while {party2_name} voted {choice2_text}\n"
                f"SENTIMENT [{sentiment_emoji}]: it is not clear if the votes are opposing or not\n"
            )
        else:
            return (
                f"\n📋 {discord.title}\n"
                f"─────────────────────────────\n"
                f"{party1_name} voted {choice1_text}, while {party2_name} voted {choice2_text}\n"
                f"SENTIMENT [{sentiment_emoji}]: votes are different but not directly opposing\n"
            )
            
    async def generate_reports(self) -> List[str]:
        """
        Generate reports for all spaces and parties.
        
        Returns:
            List of report strings, one for each discord found
        """
        reports = []
        voter_addresses = [party["address"] for party in PARTIES]
        
        reports.append("\n\nPROPOSALS IN PROCESSED BATCH WITH DIFFERENT VOTE CHOICES\n\n")
        
        for space in SPACES:
            space_id = space["space_id"]
            discords = await self.finder.find_discords([space_id], voter_addresses)
            
            for discord in discords:
                report = self._generate_report(discord, space_id)
                reports.append(report)
                
        return reports 