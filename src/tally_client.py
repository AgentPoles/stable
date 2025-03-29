import os
from typing import List, Dict, Optional, Tuple
import aiohttp
import asyncio
from dotenv import load_dotenv

load_dotenv()

class TallyClient:
    # Rate limiting constants
    MAX_RETRIES = 3
    INITIAL_RETRY_DELAY = 60  # seconds
    MAX_RETRY_DELAY = 300  # seconds
    RETRY_MULTIPLIER = 2  # Exponential backoff multiplier

    def __init__(self, governor_id: Optional[str] = None):
        self.api_key = os.getenv("TALLY_API_KEY")
        if not self.api_key:
            raise ValueError("TALLY_API_KEY not set in environment")
        self.base_url = "https://api.tally.xyz/query"
        self.headers = {
            "Content-Type": "application/json",
            "Api-Key": self.api_key
        }
        self.session: Optional[aiohttp.ClientSession] = None

        self.governor_id = governor_id or "eip155:1:0xEC568fffba86c094cf06b22134B23074DFE2252c"
        self.whale_address = "0x8b37a5Af68D315cf5A64097D96621F64b5502a22".lower()
        self.stablelab_addresses = [
            "0x74aa2213b7e4da722c56455bcbf5c2cde6e7c5f1"  # Add more if needed
        ]

    async def __aenter__(self):
        """Initialize the session when entering the context."""
        if not self.session:
            self.session = aiohttp.ClientSession(headers=self.headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close the session when exiting the context."""
        if self.session:
            await self.session.close()
            self.session = None

    async def _make_request(self, query: str, variables: Dict) -> Optional[Dict]:
        """Make a request to the Tally API with rate limit handling."""
        if not self.session:
            self.session = aiohttp.ClientSession(headers=self.headers)

        retry_count = 0
        retry_delay = self.INITIAL_RETRY_DELAY

        while retry_count < self.MAX_RETRIES:
            try:
                async with self.session.post(
                    self.base_url,
                    headers=self.headers,
                    json={"query": query, "variables": variables}
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 429:  # Rate limit hit
                        retry_count += 1
                        if retry_count >= self.MAX_RETRIES:
                            print(f"Max retries ({self.MAX_RETRIES}) reached. Giving up.")
                            return None
                        
                        # Get rate limit info from headers if available
                        retry_after = response.headers.get('Retry-After')
                        if retry_after:
                            try:
                                retry_delay = int(retry_after)
                            except ValueError:
                                pass  # Use exponential backoff if header is invalid
                        
                        print(f"Rate limit hit. Waiting {retry_delay} seconds before retry {retry_count}/{self.MAX_RETRIES}")
                        await asyncio.sleep(retry_delay)
                        retry_delay = min(retry_delay * self.RETRY_MULTIPLIER, self.MAX_RETRY_DELAY)
                    else:
                        print(f"Request failed: {response.status}")
                        try:
                            print(await response.text())
                        except:
                            pass
                        return None
            except Exception as e:
                print(f"Request error: {str(e)}")
                if retry_count >= self.MAX_RETRIES - 1:
                    return None
                retry_count += 1
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * self.RETRY_MULTIPLIER, self.MAX_RETRY_DELAY)

        return None

    async def fetch_proposal_batch(self, after_cursor: Optional[str] = None, limit: int = 100) -> Tuple[List[int], Optional[str]]:
        query = """
        query GetProposals($input: ProposalsInput!) {
          proposals(input: $input) {
            nodes {
              ... on Proposal {
                id
              }
            }
            pageInfo {
              lastCursor
            }
          }
        }
        """
        variables = {
            "input": {
                "filters": {
                    "governorId": self.governor_id
                },
                "page": {
                    "limit": limit
                },
                "sort": {
                    "sortBy": "id",
                    "isDescending": True
                }
            }
        }
        if after_cursor:
            variables["input"]["page"]["afterCursor"] = after_cursor

        data = await self._make_request(query, variables)
        if not data or "errors" in data:
            print("Error fetching proposals:", data)
            return [], None

        nodes = data["data"]["proposals"]["nodes"]
        last_cursor = data["data"]["proposals"]["pageInfo"].get("lastCursor")
        ids = [int(p["id"]) for p in nodes]

        return ids, last_cursor

    async def fetch_votes(self, address: str, proposal_ids: List[int]) -> Dict[int, str]:
        if not proposal_ids:
            return {}

        query = """
        query GetVotes($input: VotesInput!) {
          votes(input: $input) {
            nodes {
              ... on OnchainVote {
                proposal { id }
                type
              }
            }
          }
        }
        """
        variables = {
            "input": {
                "filters": {
                    "voter": address.lower(),
                    "proposalIds": proposal_ids
                }
            }
        }

        data = await self._make_request(query, variables)
        if not data or "errors" in data:
            print(f"Error fetching votes for {address}: {data}")
            return {}

        nodes = data["data"]["votes"]["nodes"]
        return {int(v["proposal"]["id"]): v["type"] for v in nodes}

    def compare_votes(self, whale_votes: Dict[int, str], stable_votes: Dict[int, str]) -> Optional[Dict]:
        for pid, whale_vote in whale_votes.items():
            if pid in stable_votes and stable_votes[pid] != whale_vote:
                return {
                    "proposalId": pid,
                    "whaleVote": whale_vote,
                    "stableLabVote": stable_votes[pid]
                }
        return None

    async def find_opposing_vote(self) -> Optional[Dict]:
        after_cursor = None
        batch = 1

        while True:
            print(f"\n📦 [Batch {batch}] Fetching proposals...")
            proposal_ids, after_cursor = await self.fetch_proposal_batch(after_cursor)
            print(f"✅ [Batch {batch}] Got {len(proposal_ids)} proposals.")

            if not proposal_ids:
                break

            whale_votes = await self.fetch_votes(self.whale_address, proposal_ids)
            print(f"🐋 [Batch {batch}] Whale voted on {len(whale_votes)} proposals.")

            if not whale_votes:
                batch += 1
                continue

            for addr in self.stablelab_addresses:
                stable_votes = await self.fetch_votes(addr, list(whale_votes.keys()))
                print(f"🏛 [Batch {batch}] StableLab ({addr}) voted on {len(stable_votes)} proposals.")

                if not stable_votes:
                    continue

                result = self.compare_votes(whale_votes, stable_votes)
                if result:
                    print("🎯 Opposing vote found!")
                    print(result)
                    return result

            if not after_cursor:
                break
            batch += 1

        print("❌ No opposing votes found.")
        return None

# Example run
if __name__ == "__main__":
    async def main():
        client = TallyClient()
        result = await client.find_opposing_vote()
        await client.close()
        print("Final Result:", result)

    loop = asyncio.get_event_loop()
    if loop.is_running():
        loop.create_task(main())
    else:
        loop.run_until_complete(main())
