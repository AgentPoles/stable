"""
Service for finding cases where a voter didn't vote with the majority voting power.
"""

from typing import List, Optional, Dict, Any, Tuple
import logging
from src.api.client import SnapshotClient
from src.config import NUMBER_OF_PROPOSALS_PER_REQUEST, VOTE_COUNT_MULTIPLIER

class MajorVotingPowerFinder:
    """Service for finding cases where a voter didn't vote with the majority."""
    
    def __init__(self, client: SnapshotClient):
        """Initialize the finder with a SnapshotClient."""
        self.client = client
        
    async def _process_votes_batch(
        self,
        target_votes: List[Dict],
        proposals: List[Any],
        target_voter: str
    ) -> Optional[Dict[str, Any]]:
        """
        Process a batch of votes to find cases where target is not highest voter.
        Returns first case found or None.
        """
        voted_proposal_ids = [vote['proposal']['id'] for vote in target_votes]
        if not voted_proposal_ids:
            return None
            
        first_count = VOTE_COUNT_MULTIPLIER * len(voted_proposal_ids)
        logging.info(f"Fetching up to {first_count} highest VP votes...")
        
        highest_power_votes = await self.client.fetch_votes_sorted_by_voting_power(
            voted_proposal_ids,
            first=first_count
        )
        
        highest_votes: Dict[str, Dict] = {}
        for vote in highest_power_votes:
            proposal_id = vote['proposal']['id']
            if proposal_id not in highest_votes:
                highest_votes[proposal_id] = vote
                
        for target_vote in target_votes:
            proposal_id = target_vote['proposal']['id']
            
            if proposal_id not in highest_votes:
                continue
                
            highest_vote = highest_votes[proposal_id]
            highest_voter = highest_vote['voter'].lower()
            
            if highest_voter != target_voter.lower():
                proposal = next(p for p in proposals if p.id == proposal_id)
                
                logging.info(f"\n🎯 Found case where target is not highest power voter!")
                logging.info(f"    Proposal: {proposal.title}")
                logging.info(f"    Highest VP: {highest_vote['vp']} (Address: {highest_voter})")
                logging.info(f"    Target VP: {target_vote['vp']}")
                logging.info("\n✨ Stopping further search\n")
                
                return {
                    'proposal_id': proposal_id,
                    'proposal_title': proposal.title,
                    'proposal_created': proposal.created,
                    'target_vote': target_vote,
                    'highest_power_vote': highest_vote
                }
                
        return None
        
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
            proposals = await self.client.fetch_proposals(space_ids, skip=offset)
            if not proposals:
                logging.info("No more proposals found")
                break
                
            logging.info(f"Found {len(proposals)} proposals")
            
            proposal_ids = [p.id for p in proposals]
            target_votes = await self.client.fetch_target_votes(proposal_ids, target_voter)
            if not target_votes:
                logging.info("No target votes found in this batch")
                offset += NUMBER_OF_PROPOSALS_PER_REQUEST
                continue
                
            logging.info(f"Found {len(target_votes)} proposals with target votes")
            
            result = await self._process_votes_batch(target_votes, proposals, target_voter)
            if result:
                return result
                
            offset += NUMBER_OF_PROPOSALS_PER_REQUEST
            
        logging.info("\n✨ No cases found where target is not highest voter")
        return None 