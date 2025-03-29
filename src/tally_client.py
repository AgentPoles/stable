import os
import time
import json
import requests
from dotenv import load_dotenv
from typing import Dict, List, Optional
import aiohttp

class TallyClient:
    def __init__(self):
        """Initialize the TallyClient with API key from environment variable."""
        load_dotenv()
        self.api_key = os.getenv("TALLY_API_KEY")
        if not self.api_key:
            raise ValueError("TALLY_API_KEY environment variable is not set")
            
        self.base_url = "https://api.tally.xyz/query"
        self.headers = {
            "Content-Type": "application/json",
            "Api-Key": self.api_key
        }
        self.last_request_time = 0

    def _format_address(self, address: str) -> str:
        """Format address to ensure it's in the correct case."""
        return address.lower()

    def _rate_limit(self):
        """Enforce rate limiting of ~1 request per second."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < 1:
            time.sleep(1 - time_since_last_request)
        self.last_request_time = time.time()

    async def _make_request(self, query: str, variables: Dict) -> Dict:
        """Make a request to the Tally API."""
        try:
            self._rate_limit()
            request_data = {"query": query, "variables": variables}
            print(f"Sending request to {self.base_url}")
            print(f"Headers: {json.dumps(self.headers, indent=2)}")
            print(f"Request data: {json.dumps(request_data, indent=2)}")
            
            response = requests.post(
                self.base_url,
                json=request_data,
                headers=self.headers
            )
            
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {json.dumps(dict(response.headers), indent=2)}")
            print(f"Response body: {response.text}")
            
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"API request failed: {str(e)}")

    async def get_votes_by_address(self, address: str, chain: str) -> List[Dict]:
        """Get all votes for a specific address on a chain."""
        thirty_days_ago = int(time.time()) - (30 * 24 * 60 * 60)
        now = int(time.time())
        
        # First, get all proposals from the last 30 days
        proposals_query = """
            query GetProposals($input: ProposalsInput!) {
                proposals(input: $input) {
                    nodes {
                        ... on Proposal {
                            id
                            governor {
                                chainId
                            }
                            createdAt
                        }
                    }
                }
            }
        """
        
        proposals_variables = {
            "input": {
                "filters": {
                    "chainId": chain,
                    "createdAt": {
                        "gte": thirty_days_ago,
                        "lte": now
                    }
                }
            }
        }
        
        try:
            proposals_response = await self._make_request(proposals_query, proposals_variables)
            if not proposals_response or 'data' not in proposals_response or 'proposals' not in proposals_response['data']:
                print(f"Error getting proposals for chain {chain}")
                return []
            
            proposals = proposals_response['data']['proposals']['nodes']
            proposal_ids = [p['id'] for p in proposals]
            
            if not proposal_ids:
                return []
            
            # Now get votes for these proposals
            votes_query = """
                query GetVotes($input: VotesInput!) {
                    votes(input: $input) {
                        nodes {
                            ... on OnchainVote {
                                id
                                proposal {
                                    id
                                    governor {
                                        chainId
                                    }
                                    createdAt
                                }
                                type
                                amount
                                voter {
                                    address
                                }
                            }
                        }
                    }
                }
            """
            
            votes_variables = {
                "input": {
                    "filters": {
                        "voter": address,
                        "proposalIds": proposal_ids
                    }
                }
            }
            
            votes_response = await self._make_request(votes_query, votes_variables)
            if votes_response and 'data' in votes_response and 'votes' in votes_response['data']:
                return votes_response['data']['votes']['nodes']
            return []
        except Exception as e:
            print(f"Error analyzing chain {chain}: {str(e)}")
            return []

    async def get_proposal_details(self, proposal_id: str) -> Dict:
        """Get details for a specific proposal."""
        query = """
        query GetProposalDetails($id: String!) {
            proposal(id: $id) {
                id
                title
                description
                startTime
                endTime
                votes {
                    nodes {
                        ... on OnchainVote {
                            id
                            type
                            amount
                            voter {
                                address
                            }
                        }
                    }
                }
            }
        }
        """
        
        variables = {
            "id": proposal_id
        }
        
        response = await self._make_request(query, variables)
        if not response or "errors" in response:
            print(f"Error getting proposal details: {response}")
            return {}
            
        return response.get("data", {}).get("proposal", {}) 