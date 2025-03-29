from typing import Dict, List
from tally_client import TallyClient

class VoteAnalyzer:
    def __init__(self, tally_client: TallyClient):
        self.tally_client = tally_client

    def find_opposing_votes(self, whale_votes: List[Dict], stable_votes: List[Dict]) -> List[Dict]:
        opposing_votes = []
        
        # Create a map of proposal IDs to whale votes
        whale_vote_map = {
            vote["proposal"]["id"]: vote 
            for vote in whale_votes
        }
        
        # Create a map of proposal IDs to stable votes
        stable_vote_map = {
            vote["proposal"]["id"]: vote 
            for vote in stable_votes
        }
        
        # Compare votes for each proposal
        for proposal_id, whale_vote in whale_vote_map.items():
            if proposal_id in stable_vote_map:
                stable_vote = stable_vote_map[proposal_id]
                if self._are_votes_opposing(whale_vote["type"], stable_vote["type"]):
                    opposing_votes.append({
                        "proposal_id": proposal_id,
                        "proposal_title": whale_vote["proposal"].get("title", "Unknown"),
                        "chain": whale_vote["proposal"]["governor"]["chainId"],
                        "whale_vote": whale_vote["type"],
                        "stablelab_vote": stable_vote["type"],
                        "whale_amount": whale_vote["amount"],
                        "stablelab_amount": stable_vote["amount"],
                        "timestamp": whale_vote["proposal"]["createdAt"]
                    })
        
        return opposing_votes
    
    def _are_votes_opposing(self, vote1: str, vote2: str) -> bool:
        return (vote1 == "for" and vote2 == "against") or (vote1 == "against" and vote2 == "for") 