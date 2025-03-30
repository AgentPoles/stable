"""
Service for generating reports about voting relationships between parties.
Uses DiscordFinder to find different votes and SentimentAnalyzer to determine relationships.
"""

from typing import List, Dict
from datetime import datetime
from src.api.client import SnapshotClient
from src.services.discord_finder import DiscordFinder
from src.services.sentiment import SentimentAnalyzer, ChoiceRelationship
from src.services.major_voting_power_finder import MajorVotingPowerFinder
from src.models import VaryingChoices
from src.config import PARTIES, SPACES

def format_timestamp(timestamp: int) -> str:
    """Convert Unix timestamp to human readable format."""
    return datetime.fromtimestamp(timestamp).strftime('%B %d, %Y')

class Reporter:
    """Service for generating reports about voting relationships."""
    
    def __init__(self, client: SnapshotClient):
        """Initialize the reporter with a SnapshotClient."""
        self.client = client
        self.finder = DiscordFinder(client)
        self.analyzer = SentimentAnalyzer()
        self.majority_finder = MajorVotingPowerFinder(client)
        
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
                f"\n📋 Proposal: {discord.title}\n"
                f"─────────────────────────────\n"
                f"CREATED[⏰]: {format_timestamp(discord.created)}\n"
                f"\n{party1_name} voted {choice1_text}, while {party2_name} voted {choice2_text}\n"
                f"SENTIMENT[{sentiment_emoji}]: votes are clearly opposing\n\n"
            )
        elif relationship == ChoiceRelationship.PARTIAL_OPPOSITION:
            return (
                f"\n📋 Proposal: {discord.title}\n"
                f"─────────────────────────────\n"
                f"CREATED[⏰]: {format_timestamp(discord.created)}\n"
                f"\n{party1_name} voted {choice1_text}, while {party2_name} voted {choice2_text}\n"
                f"SENTIMENT[{sentiment_emoji}]: one party took a clear position while the other remained neutral\n\n"
            )
        elif relationship == ChoiceRelationship.INCONCLUSIVE:
            return (
                f"\n📋 Proposal: {discord.title}\n"
                f"─────────────────────────────\n"
                f"CREATED[⏰]: {format_timestamp(discord.created)}\n"
                f"\n{party1_name} voted {choice1_text}, while {party2_name} voted {choice2_text}\n"
                f"SENTIMENT[{sentiment_emoji}]: it is not clear if the votes are opposing or not\n\n"
            )
        else:
            return (
                f"\n📋 Proposal: {discord.title}\n"
                f"─────────────────────────────\n"
                f"CREATED[⏰]: {format_timestamp(discord.created)}\n"
                f"\n{party1_name} voted {choice1_text}, while {party2_name} voted {choice2_text}\n"
                f"SENTIMENT[{sentiment_emoji}]: votes are different but not directly opposing\n\n"
            )
            
    def _generate_majority_report(self, proposal_id: str, target_vote: Dict, majority_vote: Dict) -> str:
        """Generate a report for a vote against majority."""
        proposal = self.client.proposal_cache.get(proposal_id)
        if not proposal:
            return ""
            
        return (
            f"\n📊 {proposal.title}\n"
            f"─────────────────────────────\n"
            f"{target_vote['name']} voted with voting power {target_vote['vp']}, "
            f"but majority voting power was {majority_vote['vp']} by {majority_vote['name']}\n"
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
        
    async def generate_majority_reports(self) -> List[str]:
        """
        Generate reports for votes against majority.
        
        Returns:
            List of report strings, one for each case found
        """
        reports = []
        target_voter = PARTIES[0]["address"]  # StableLabs
        
        # Get proposals from cache
        proposal_ids = list(self.client.proposal_cache.keys())
        
        # Find cases where target voted against majority
        result = await self.majority_finder.find_votes_against_majority(
            proposal_ids=proposal_ids,
            target_voter=target_voter
        )
        
        if result:
            proposal_id, target_vote, majority_vote = result
            report = self._generate_majority_report(proposal_id, target_vote, majority_vote)
            reports.append(report)
            
        return reports 