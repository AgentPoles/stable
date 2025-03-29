import os
from dotenv import load_dotenv
from typing import Dict, List, Optional
import aiohttp
import time
import asyncio

# Load environment variables
load_dotenv()

class TallyClient:
    def __init__(self):
        self.api_key = os.getenv("TALLY_API_KEY")
        if not self.api_key:
            raise ValueError("TALLY_API_KEY environment variable is not set")
        self.base_url = "https://api.tally.xyz/query"
        self.headers = {
            "Content-Type": "application/json",
            "Api-Key": self.api_key
        }

    async def _make_request(self, query: str, variables: Dict) -> Optional[Dict]:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.base_url,
                headers=self.headers,
                json={"query": query, "variables": variables}
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"API request failed: {response.status} {response.reason} for url: {self.base_url}")
                    try:
                        print("Response:", await response.text())
                    except:
                        pass
                    return None

    async def get_proposals_by_governor(self, governor_id: str) -> List[Dict]:
        query = """
        query GetProposals($input: ProposalsInput!) {
          proposals(input: $input) {
            pageInfo {
              hasNextPage
              endCursor
            }
            nodes {
              id
              title
              createdAt
              governor {
                chainId
              }
              votes {
                voter {
                  address
                }
                support
                weight
              }
            }
          }
        }
        """

        all_proposals = []
        has_next_page = True
        cursor = None

        while has_next_page:
            variables = {
                "input": {
                    "filters": {
                        "governorId": governor_id
                    },
                    "pagination": {
                        "limit": 50
                    }
                }
            }
            if cursor:
                variables["input"]["pagination"]["after"] = cursor

            response = await self._make_request(query, variables)
            if not response or "errors" in response:
                print(f"Error getting proposals: {response}")
                break

            data = response.get("data", {}).get("proposals", {})
            proposals = data.get("nodes", [])
            page_info = data.get("pageInfo", {})

            all_proposals.extend(proposals)
            has_next_page = page_info.get("hasNextPage", False)
            cursor = page_info.get("endCursor")

            await asyncio.sleep(0.5)

        return all_proposals

    async def get_votes_by_address(self, address: str, proposals: List[Dict]) -> List[Dict]:
        address = address.lower()
        results = []
        for proposal in proposals:
            for vote in proposal.get("votes", []):
                if vote.get("voter", {}).get("address", "").lower() == address:
                    results.append({
                        "proposal_id": proposal["id"],
                        "title": proposal.get("title"),
                        "createdAt": proposal.get("createdAt"),
                        "vote": vote["support"],
                        "weight": vote["weight"]
                    })
        return results

if __name__ == "__main__":
    async def main():
        AAVE_GOVERNOR_ID = "0xEC568fffba86c094cf06b22134B23074DFE2252c"
        WHALE_ADDRESS = "0x8b37a5Af68D315cf5A64097D96621F64b5502a22"
        client = TallyClient()
        proposals = await client.get_proposals_by_governor(AAVE_GOVERNOR_ID)
        votes = await client.get_votes_by_address(WHALE_ADDRESS, proposals)
        print(f"Fetched {len(votes)} votes by whale")
        for vote in votes:
            print(vote)

    asyncio.run(main())
