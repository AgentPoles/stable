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
    """Convert Unix timestamp to human readable format in UTC."""
    dt = datetime.utcfromtimestamp(timestamp)
    return dt.strftime('%B %d, %Y %H:%M:%S')

class Reporter:
    """Service for generating reports about voting relationships."""
    
    def __init__(self, client: SnapshotClient):
        """Initialize the reporter with a SnapshotClient."""
        self.client = client
        self.finder = DiscordFinder(client)
        self.analyzer = SentimentAnalyzer()
        self.majority_finder = MajorVotingPowerFinder(client)
        
    def _get_space_name(self, space_id: str) -> str:
        """Get space name from space_id."""
        for space in SPACES:
            if space["space_id"] == space_id:
                return space["name"]
        return space_id
        
    async def _generate_report(self, discord: VaryingChoices, space_id: str) -> str:
        """Generate a report for a single discord."""
        party1, party2 = list(discord.voter_choices.keys())
        choice1, choice2 = discord.voter_choices[party1], discord.voter_choices[party2]
        
        # Get voter names
        voter_names = await self.client.fetch_voter_names([party1, party2])
        party1_name = voter_names[party1.lower()]
        party2_name = voter_names[party2.lower()]
        
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
            
    async def generate_reports(self) -> List[str]:
        """
        Generate reports for all spaces and parties.
        
        Returns:
            List of report strings, one for each discord found
        """
        reports = []
        voter_addresses = [PARTIES["target"], PARTIES["whale"]]
        
        # Get voter names for the header
        async with self.client as client:
            voter_names = await client.fetch_voter_names(voter_addresses)
            target_name = voter_names[PARTIES["target"].lower()]
            whale_name = voter_names[PARTIES["whale"].lower()]
        
        reports.append("\n\nPROPOSALS IN PROCESSED BATCH WITH DIFFERENT VOTE CHOICES\n\n")
        reports.append(
            f"🕵️  Found party names:\n"
            f"    Target ({PARTIES['target']}): {target_name}\n"
            f"    Whale ({PARTIES['whale']}): {whale_name}\n\n"
        )
        
        for space in SPACES:
            space_id = space["space_id"]
            discords = await self.finder.find_discords([space_id], voter_addresses)
            
            for discord in discords:
                async with self.client as client:
                    report = await self._generate_report(discord, space_id)
                    reports.append(report)
                
        return reports
        
    async def generate_majority_reports(self) -> List[str]:
        """
        Generate reports for votes against majority.
        
        Returns:
            List of report strings, one for each case found
        """
        reports = []
        target_voter = PARTIES["target"]  # StableLabs
        space_ids = [space["space_id"] for space in SPACES]
        
        # Find cases where target voted against majority
        result = await self.majority_finder.find_votes_against_majority(
            space_ids=space_ids,
            target_voter=target_voter
        )
        
        if result:
            # Get voter names for the result
            voter_addresses = [
                result['target_vote']['voter'],
                result['highest_power_vote']['voter']
            ]
            voter_names = await self.client.fetch_voter_names(voter_addresses)
            
            # Generate report header
            reports.append("\n\nPROPOSALS WHERE TARGET IS NOT THE HIGHEST VOTING POWER VOTER\n\n")
            
            # Generate report for the result
            target_name = voter_names[result['target_vote']['voter'].lower()]
            majority_name = voter_names[result['highest_power_vote']['voter'].lower()]
            
            reports.append(
                f"\n📋 Proposal: {result['proposal_title']}\n"
                f"─────────────────────────────\n"
                f"CREATED[⏰]: {format_timestamp(result['proposal_created'])}\n"
                f"\nTarget ({result['target_vote']['voter']}): {target_name} ({result['target_vote']['vp']})\n"
                f"Majority ({result['highest_power_vote']['voter']}): {majority_name} ({result['highest_power_vote']['vp']})\n\n"
            )
        else:
            reports.append("\n\nNo proposals found where target is not the highest voting power voter.\n\n")
        
        return reports 