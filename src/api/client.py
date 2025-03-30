"""
Service for analyzing voting choices and determining their relationship.
Handles case-insensitive matching and various common voting choice formats.
"""

from typing import List, Dict, Optional, Tuple, Any
import aiohttp
from src.config import NUMBER_OF_PROPOSALS_PER_REQUEST, NUMBER_OF_VOTES_PER_REQUEST
from src.models import Proposal, VaryingChoices

class SnapshotClient:
    """Client for interacting with Snapshot API.
    
    Attributes:
        base_url: The base URL for Snapshot API
        session: aiohttp ClientSession for making requests
        proposal_cache: Cache of proposal data
    """
    def __init__(self):
        self.base_url = "https://hub.snapshot.org/graphql"
        self.session = None
        self.proposal_cache: Dict[str, Proposal] = {}

    async def __aenter__(self):
        """Initialize session when entering context manager."""
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up session when exiting context manager."""
        if self.session and not self.session.closed:
            await self.session.close()
        self.session = None

    async def _make_request(self, query: str, variables: Dict) -> Dict:
        """Make a GraphQL request to the API.
        
        Args:
            query: GraphQL query string
            variables: Query variables
            
        Returns:
            API response data
        """
        if not self.session:
            raise RuntimeError("Client session not initialized. Use async with context manager.")
            
        async with self.session.post(
            self.base_url,
            json={"query": query, "variables": variables}
        ) as response:
            if response.status == 200:
                return await response.json()
            return {"data": {}}

    async def fetch_proposals(self, space_ids: List[str], skip: int = 0) -> List[Proposal]:
        """
        Fetch closed proposals from specified Snapshot spaces.
        
        Process:
        1. Make GraphQL query for proposals
        2. Convert response to Proposal objects
        3. Cache proposal data
        4. Return list of proposals
        
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
                title
                choices
                created
            }
        }
        """
        
        variables = {
            "first": NUMBER_OF_PROPOSALS_PER_REQUEST,
            "skip": skip,
            "spaceIds": space_ids
        }

        data = await self._make_request(query, variables)
        if data.get("data", {}).get("proposals"):
            proposals = [Proposal(**proposal) for proposal in data["data"]["proposals"]]
            self.proposal_cache.update({p.id: p for p in proposals})
            return proposals
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
        4. Create VaryingChoices objects using cached proposal data
        
        Args:
            proposal_ids: List of proposal IDs to query
            voters: List of voter addresses to check
            skip: Number of votes to skip for pagination
            
        Returns:
            List of VaryingChoices objects containing proposals with different choices
        """
        if len(voters) != 2:
            raise ValueError("Exactly two voters must be specified")

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

        data = await self._make_request(query, variables)
        if not data.get("data", {}).get("votes"):
            return []

        votes = data["data"]["votes"]
        
        # Group votes by proposal
        proposal_votes: Dict[str, Dict[str, int]] = {}
        for vote in votes:
            proposal_id = vote["proposal"]["id"]
            voter = vote["voter"].lower()
            choice = vote["choice"]
            
            if proposal_id not in proposal_votes:
                proposal_votes[proposal_id] = {}
            proposal_votes[proposal_id][voter] = choice

        varying_choices = []
        for proposal_id, voter_choices in proposal_votes.items():
            # Skip if we don't have votes from both voters
            if len(voter_choices) != 2:
                continue
                
            # Skip if choices are the same
            if voter_choices[voters[0].lower()] == voter_choices[voters[1].lower()]:
                continue
                
            # Get cached proposal
            proposal = self.proposal_cache.get(proposal_id)
            if proposal:
                varying_choices.append(
                    VaryingChoices.from_votes(
                        proposal_id=proposal_id,
                        title=proposal.title,
                        voter_choices=voter_choices,
                        proposal_choices=proposal.choices,
                        created=proposal.created
                    )
                )

        return varying_choices

    async def fetch_votes_sorted_by_voting_power(
        self,
        proposal_id: str,
        skip: int = 0,
        first: int = NUMBER_OF_VOTES_PER_REQUEST
    ) -> List[Dict[str, Any]]:
        """
        Fetch votes for a proposal, sorted by voting power.
        
        Args:
            proposal_id: ID of the proposal to fetch votes for
            skip: Number of votes to skip (for pagination)
            first: Number of votes to fetch (defaults to config value)
            
        Returns:
            List of votes sorted by voting power (highest first)
        """
        query = """
        query Votes($proposal: String!, $skip: Int!, $first: Int!) {
            votes(
                first: $first,
                skip: $skip,
                where: { proposal: $proposal }
                orderBy: "vp",
                orderDirection: desc
            ) {
                id
                voter
                vp
                choice
                created
            }
        }
        """
        
        variables = {
            "proposal": proposal_id,
            "skip": skip,
            "first": first
        }
        
        response = await self._make_request(query, variables)
        votes = response.get("data", {}).get("votes", [])
        
        return votes

    async def fetch_voter_names(self, addresses: List[str]) -> Dict[str, str]:
        """
        Fetch voter names from Snapshot API for multiple addresses.
        
        Args:
            addresses: List of voter addresses
            
        Returns:
            Dictionary mapping addresses to names (or "UNKNOWN (address)" if not found)
        """
        query = """
        query GetUsers($addresses: [String]!) {
            users(first: 10, where: { id_in: $addresses }) {
                id
                name
            }
        }
        """
        
        variables = {"addresses": [addr.lower() for addr in addresses]}
        data = await self._make_request(query, variables)
        
        # Create mapping of addresses to names
        name_map = {}
        if data.get("data", {}).get("users"):
            for user in data["data"]["users"]:
                # Find the original address that matches this user's ID
                original_addr = next((addr for addr in addresses if addr.lower() == user["id"].lower()), user["id"])
                name_map[user["id"].lower()] = user["name"] or f"UNKNOWN ({original_addr})"
                
        # Add UNKNOWN for any addresses not found
        for addr in addresses:
            addr_lower = addr.lower()
            if addr_lower not in name_map:
                name_map[addr_lower] = f"UNKNOWN ({addr})"
                
        return name_map 