import json
from typing import Dict, List
from tally_client import TallyClient
from vote_analyzer import VoteAnalyzer

class ChainAnalyzer:
    def __init__(self, tally_client: TallyClient, vote_analyzer: VoteAnalyzer):
        """Initialize the ChainAnalyzer with a TallyClient and VoteAnalyzer."""
        self.tally_client = tally_client
        self.vote_analyzer = vote_analyzer
        self.whale_address = "0x8b37a5af68d315cf5a64097d96621f64b5502a22"
        
        # Load StableLab addresses from JSON file
        with open("../stablelab_addresses.json", "r") as f:
            data = json.load(f)
            self.stablelab_addresses = data.get("addresses", [])
        
        # Supported chains
        self.chains = ["ethereum", "arbitrum", "optimism", "base", "polygon"]

    async def analyze_chain(self, chain: str) -> List[Dict]:
        """Analyze votes for a specific chain."""
        results = []
        
        # Get all whale votes at once
        whale_votes = await self.tally_client.get_votes_by_address(
            self.whale_address,
            chain=chain
        )
        
        if not whale_votes:
            return results
            
        # Find opposing votes for each whale vote
        for vote in whale_votes:
            proposal_id = vote["proposal"]["id"]
            proposal_details = await self.tally_client.get_proposal_details(proposal_id)
            
            if not proposal_details:
                continue
                
            opposing_votes = self.vote_analyzer.find_opposing_votes(
                whale_vote=vote,
                proposal_details=proposal_details
            )
            
            if opposing_votes:
                results.extend(opposing_votes)
        
        return results

    async def analyze_all_chains(self) -> List[Dict]:
        """Analyze votes across all supported chains."""
        all_results = []
        
        for chain in self.chains:
            try:
                chain_results = await self.analyze_chain(chain)
                all_results.extend(chain_results)
            except Exception as e:
                print(f"Error analyzing chain {chain}: {str(e)}")
                
        return all_results 