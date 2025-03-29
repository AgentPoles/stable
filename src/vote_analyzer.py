from typing import Dict, List
from tally_client import TallyClient

class VoteAnalyzer:
    def __init__(self, tally_client: TallyClient):
        self.tally_client = tally_client

    def find_opposing_votes(self, whale_votes: Dict, stablelab_addresses: List[str]) -> List[Dict]:
        if not whale_votes.get("edges"):
            return []

        opposing_votes = []
        for edge in whale_votes["edges"]:
            vote = edge["node"]
            proposal_id = vote["proposal"]["id"]

            # Get proposal details to check StableLab votes
            proposal = self.tally_client.get_proposal_details(proposal_id)
            
            # Check if any StableLab address voted oppositely
            for vote_data in proposal.get("votes", []):
                voter_address = vote_data.get("voter", {}).get("address")
                if voter_address in stablelab_addresses:
                    if vote_data["type"] != vote["type"]:
                        opposing_votes.append({
                            "proposal_id": proposal_id,
                            "proposal_title": proposal.get("title", "Unknown"),
                            "whale_vote": vote["type"],
                            "stablelab_vote": vote_data["type"],
                            "whale_amount": vote["amount"],
                            "stablelab_amount": vote_data["amount"]
                        })
                        break  # Found an opposing vote, no need to check other StableLab addresses

        return opposing_votes
    
    def _are_votes_opposing(self, vote1: str, vote2: str) -> bool:
        return (vote1 == "for" and vote2 == "against") or (vote1 == "against" and vote2 == "for") 