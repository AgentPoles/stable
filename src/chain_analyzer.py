"""
Analyzes votes across different chains using the Tally API.
"""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from tally_client import TallyClient
from config import MULTICHAIN, GOVERNOR_IDS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChainAnalyzer:
    def __init__(self, tally_client: TallyClient):
        self.tally_client = tally_client
        # Only use ethereum chain if MULTICHAIN is False
        self.chains = ["ethereum"] if not MULTICHAIN else ["ethereum", "arbitrum", "optimism", "base", "polygon"]
        logger.info(f"Initialized ChainAnalyzer with chains: {self.chains}")

    async def analyze_chain(self, chain: str) -> Dict:
        """Analyze votes for a specific chain."""
        try:
            logger.info(f"Starting analysis for chain: {chain}")
            governor_id = GOVERNOR_IDS.get(chain)
            if not governor_id:
                logger.error(f"No governor ID found for chain: {chain}")
                return {}

            # Update the existing client's governor ID
            self.tally_client.governor_id = governor_id
            
            # Get votes for the chain
            result = await self.tally_client.find_opposing_vote()
            
            if result:
                result["chain"] = chain
                return result
            return {}

        except Exception as e:
            logger.error(f"Error analyzing chain {chain}: {str(e)}")
            return {}

    async def analyze_all_chains(self) -> Dict[str, List[Dict]]:
        """Analyze votes across all configured chains."""
        results = {}
        for chain in self.chains:
            results[chain] = await self.analyze_chain(chain)
        return results

    async def get_recent_votes(self, days: int = 7) -> List[Dict]:
        """Get recent votes across all chains within the specified number of days."""
        all_votes = []
        cutoff_date = datetime.now() - timedelta(days=days)
        
        chain_results = await self.analyze_all_chains()
        
        for chain, result in chain_results.items():
            if result:
                start_time = datetime.fromisoformat(result.get("startTime", "").replace("Z", "+00:00"))
                if start_time >= cutoff_date:
                    all_votes.append(result)
        
        return all_votes

async def main():
    """Main function to demonstrate usage."""
    async with TallyClient() as tally_client:
        analyzer = ChainAnalyzer(tally_client)
        
        # Example: Get recent votes from all chains
        recent_votes = await analyzer.get_recent_votes(days=7)
        print(f"Found {len(recent_votes)} recent votes across all chains")
        
        for vote in recent_votes:
            print(f"Chain: {vote['chain']}, Proposal ID: {vote['proposalId']}")

if __name__ == "__main__":
    asyncio.run(main())
