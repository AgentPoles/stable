from typing import List, Dict, Set
import aiohttp
from config import NUMBER_OF_PROPOSALS_PER_REQUEST
from ..models import Vote, VoteResponse, Proposal, VaryingChoices

class SnapshotClient:
    """Client for interacting with Snapshot API.
    
    Attributes:
        base_url: The base URL for Snapshot API
        session: aiohttp ClientSession for making requests
    """
    def __init__(self):
        self.base_url = "https://hub.snapshot.org/graphql"
        self.session = None

    async def __aenter__(self):
        """Initialize session when entering context manager."""
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up session when exiting context manager."""
        if self.session:
            await self.session.close()
            self.session = None

    async def fetch_proposals(self, space_ids: List[str], skip: int = 0) -> List[Proposal]:
        """
        Fetch closed proposals from specified Snapshot spaces.
        
        Process:
        1. Make GraphQL query for proposals
        2. Convert response to Proposal objects
        3. Return list of proposals
        
        Args:
            space_ids: List of space IDs to query (e.g. ["aave.eth"])
            skip: Number of proposals to skip for pagination
            
        Returns:
            List of Proposal objects ordered by creation date (newest first)
        """
        query = """
        query GetProposals($first: Int!, $skip: Int!, $spaceIds: [String]!) {
            proposals(
                first: $first,
                skip: $skip,
                where: {
                    space_in: $spaceIds,
                    state: "closed"
                },
                orderBy: "created",
                orderDirection: desc
            ) {
                id
                choices
            }
        }
        """
        
        variables = {
            "first": NUMBER_OF_PROPOSALS_PER_REQUEST,
            "skip": skip,
            "spaceIds": space_ids
        }

        if not self.session:
            self.session = aiohttp.ClientSession()

        async with self.session.post(
            self.base_url,
            json={"query": query, "variables": variables}
        ) as response:
            if response.status == 200:
                data = await response.json()
                return [Proposal(**proposal) for proposal in data["data"]["proposals"]]
            return []

    async def fetch_votes_and_choices(self, proposal_ids: List[str], voter_address: str, skip: int = 0) -> List[VoteResponse]:
        """
        Fetches votes and choices for specific proposals from a voter.
        
        Args:
            proposal_ids: List of proposal IDs to query
            voter_address: Address of the voter
            skip: Number of votes to skip for pagination
            
        Returns:
            List of VoteResponse objects containing proposal_id, choice, and choices
        """
        query = """
        query GetVotes($first: Int!, $skip: Int!, $proposalIds: [String]!, $voter: String!) {
            votes(
                first: $first,
                skip: $skip,
                where: {
                    proposal_in: $proposalIds,
                    voter: $voter
                },
                orderBy: "created",
                orderDirection: desc
            ) {
                proposal {
                    id
                    choices
                }
                choice
            }
        }
        """
        
        variables = {
            "first": NUMBER_OF_PROPOSALS_PER_REQUEST,
            "skip": skip,
            "proposalIds": proposal_ids,
            "voter": voter_address.lower()
        }

        if not self.session:
            self.session = aiohttp.ClientSession()

        async with self.session.post(
            self.base_url,
            json={"query": query, "variables": variables}
        ) as response:
            if response.status == 200:
                data = await response.json()
                votes = [Vote(**vote) for vote in data["data"]["votes"]]
                return [VoteResponse.from_vote(vote) for vote in votes]
            return []

    async def fetch_proposals_with_varying_choices(
        self, 
        proposal_ids: List[str], 
        voters: List[str], 
        skip: int = 0
    ) -> List[VaryingChoices]:
        """
        Fetch proposals where voters have different choices.
        
        Process:
        1. Make GraphQL query for votes
        2. Process votes into proposal-voter mapping
        3. Filter for proposals with different choices
        4. Create VaryingChoices objects
        
        Args:
            proposal_ids: List of proposal IDs to query
            voters: List of voter addresses to check
            skip: Number of votes to skip for pagination
            
        Returns:
            List of VaryingChoices objects containing proposals with different choices
        """
        query = """
        query GetVotes($first: Int!, $skip: Int!, $proposalIds: [String]!, $voters: [String]!) {
            votes(
                first: $first,
                skip: $skip,
                where: {
                    proposal_in: $proposalIds,
                    voter_in: $voters
                },
                orderBy: "created",
                orderDirection: desc
            ) {
                proposal {
                    id
                    choices
                }
                choice
                voter
            }
        }
        """
        
        variables = {
            "first": NUMBER_OF_PROPOSALS_PER_REQUEST,
            "skip": skip,
            "proposalIds": proposal_ids,
            "voters": [v.lower() for v in voters]
        }

        if not self.session:
            self.session = aiohttp.ClientSession()

        async with self.session.post(
            self.base_url,
            json={"query": query, "variables": variables}
        ) as response:
            if response.status != 200:
                return []

            data = await response.json()
            votes = data["data"]["votes"]
            
            proposal_votes: Dict[str, Dict[str, int]] = {}
            proposal_choices: Dict[str, List[str]] = {}
            
            for vote in votes:
                proposal_id = vote["proposal"]["id"]
                voter = vote["voter"]
                choice = vote["choice"]
                
                if proposal_id not in proposal_votes:
                    proposal_votes[proposal_id] = {}
                    proposal_choices[proposal_id] = vote["proposal"]["choices"]
                
                proposal_votes[proposal_id][voter] = choice
            
            return [
                VaryingChoices.from_votes(
                    proposal_id=proposal_id,
                    voter_choices=choices,
                    proposal_choices=proposal_choices[proposal_id]
                )
                for proposal_id, choices in proposal_votes.items()
                if len(set(choices.values())) > 1
            ] 