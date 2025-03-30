"""
Service for finding cases where a voter didn't vote with the majority voting power.
"""

from typing import List, Optional, Dict, Any
import logging
from src.api.client import SnapshotClient
from src.config import NUMBER_OF_PROPOSALS_PER_REQUEST, NUMBER_OF_VOTES_PER_REQUEST

class MajorVotingPowerFinder:
    """Service for finding cases where a voter didn't vote with the majority."""
    
    def __init__(self, client: SnapshotClient):
        """Initialize the finder with a SnapshotClient."""
        self.client = client
        
        
    async def find_votes_against_majority(
        self, space_ids: List[str], target_voter: str
    ) -> Optional[Dict[str, Any]]:
        """
        Find proposals where the target voter voted but was not the voter with highest voting power.
        Returns the first case found or None if no cases found.
        """
        logging.info("\n🔍 Searching for proposals in batches...\n")
        
        offset = 0
        while True:
            logging.info(f"[Batch {offset+1}-{offset+NUMBER_OF_PROPOSALS_PER_REQUEST}] Getting proposals...")
            proposals = await self.client.fetch_proposals(space_ids, offset)
            
            if not proposals:
                logging.info(f"[Batch {offset+1}-{offset+NUMBER_OF_PROPOSALS_PER_REQUEST}] No more proposals found")
                break
                
            logging.info(f"[Batch {offset+1}-{offset+NUMBER_OF_PROPOSALS_PER_REQUEST}] Found {len(proposals)} proposals")
            
            for proposal in proposals:
                # Shorten proposal ID for logging
                short_id = f"{proposal.id[:8]}...{proposal.id[-4:]}"
                logging.info(f"\n  [Proposal {short_id}] Checking votes...")
                votes_offset = 0
                voter_addresses = set()
                highest_power_vote = None
                
                while True:
                    logging.info(f"    [Votes {votes_offset+1}-{votes_offset+NUMBER_OF_VOTES_PER_REQUEST}] Checking votes...")
                    votes = await self.client.fetch_votes_sorted_by_voting_power(
                        proposal.id, votes_offset, NUMBER_OF_VOTES_PER_REQUEST
                    )
                    
                    if not votes:
                        break
                        
                    # Track highest power vote across all batches
                    if highest_power_vote is None or votes[0]['vp'] > highest_power_vote['vp']:
                        highest_power_vote = votes[0]
                    
                    # Check first vote in first batch to see if target is highest power voter
                    if votes_offset == 0:
                        if highest_power_vote['voter'].lower() == target_voter.lower():
                            logging.info(f"    [Proposal {short_id}] Target is highest power voter, skipping...")
                            break
                    
                    # Add all voter addresses to set for O(1) lookup
                    for vote in votes:
                        voter_addresses.add(vote['voter'].lower())
                    
                    # Check if target voted
                    if target_voter.lower() in voter_addresses:
                        # Found target's vote and we know they're not highest power
                        logging.info(f"    [Proposal {short_id}] Found target vote!")
                        logging.info("🕵️  Found case where target is not highest power voter")
                        logging.info("✨ Stopping further search\n")
                        return {
                            'proposal_id': proposal.id,
                            'proposal_title': proposal.title,
                            'proposal_created': proposal.created,
                            'target_vote': next(v for v in votes if v['voter'].lower() == target_voter.lower()),
                            'highest_power_vote': highest_power_vote
                        }
                    
                    votes_offset += NUMBER_OF_VOTES_PER_REQUEST
            
            offset += NUMBER_OF_PROPOSALS_PER_REQUEST
        
        logging.info("\n✨ finished searching all proposals")
        return None 