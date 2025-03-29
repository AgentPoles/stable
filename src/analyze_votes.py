"""
Main script to analyze votes across different chains.
"""

import asyncio
import logging
from typing import Dict, List
from datetime import datetime, timedelta
from tally_client import TallyClient
from chain_analyzer import ChainAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def analyze_votes():
    """Main function to analyze votes."""
    try:
        async with TallyClient() as tally_client:
            chain_analyzer = ChainAnalyzer(tally_client)
            
            # Get recent votes from all chains
            recent_votes = await chain_analyzer.get_recent_votes(days=7)
            
            if not recent_votes:
                logger.info("No recent votes found")
                return
            
            logger.info(f"Found {len(recent_votes)} recent votes")
            
            # Process and display results
            for vote in recent_votes:
                logger.info(f"Chain: {vote['chain']}")
                logger.info(f"Proposal ID: {vote['proposalId']}")
                logger.info(f"Whale Vote: {vote['whaleVote']}")
                logger.info(f"StableLab Vote: {vote['stableLabVote']}")
                logger.info("---")
                
    except Exception as e:
        logger.error(f"Error analyzing votes: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(analyze_votes()) 