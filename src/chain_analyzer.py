import json
from typing import Dict, List
from tally_client import TallyClient
from vote_analyzer import VoteAnalyzer

GOVERNOR_IDS_BY_CHAIN = {
    "ethereum": "0xEC568fffba86c094cf06b22134B23074DFE2252c",
    "arbitrum": "0x9aa7fEc87CA69695Dd1f879567CcF49F3ba417E2",
    "optimism": "0x8D4E5E61B2d3f28937d104D8a2289A82085C2F99",
    "base": "0xC1eB8F723D4F46AC52f3Cc4137Afe0c0387B4e47",
    "polygon": "0x8164Cc65827dcFe994AB23944CBC90e0aa80bFcb"
}

class ChainAnalyzer:
    def __init__(self, tally_client: TallyClient, vote_analyzer: VoteAnalyzer):
        self.tally_client = tally_client
        self.vote_analyzer = vote_analyzer
        self.whale_address = "0x8b37a5af68d315cf5a64097d96621f64b5502a22"

        with open("../stablelab_addresses.json", "r") as f:
            data = json.load(f)
            self.stablelab_addresses = data.get("addresses", [])

        self.chains = ["ethereum", "arbitrum", "optimism", "base", "polygon"]

    async def analyze_chain(self, chain: str) -> List[Dict]:
        results = []

        governor_id = GOVERNOR_IDS_BY_CHAIN.get(chain)
        if not governor_id:
            print(f"Unsupported chain: {chain}")
            return results

        proposals = await self.tally_client.get_proposals_by_governor(governor_id)
        whale_votes = await self.tally_client.get_votes_by_address(self.whale_address, proposals)

        if not whale_votes:
            return results

        for vote in whale_votes:
            proposal_id = vote["proposal_id"]
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
        all_results = []

        for chain in self.chains:
            try:
                print(f"Analyzing chain: {chain}...")
                chain_results = await self.analyze_chain(chain)
                all_results.extend(chain_results)
            except Exception as e:
                print(f"Error analyzing chain {chain}: {str(e)}")

        return all_results
