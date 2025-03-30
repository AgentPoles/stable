import asyncio
import logging
from src.api.client import SnapshotClient
from src.services.discord_finder import DiscordFinder
from src.config import AAVE_SNAPSHOT_SPACE_ID, STABLE_LABS, WHALE

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    datefmt='%H:%M:%S'
)

async def main():
    """Main entry point for the application.
    
    Process:
    1. Initialize clients
    2. Find discords between parties
    3. Display results
    """
    parties = [STABLE_LABS, WHALE]
    
    # Log initial setup
    logging.info(f"Checking space: {AAVE_SNAPSHOT_SPACE_ID}")
    logging.info(f"Comparing addresses: {', '.join(parties)}")
    
    async with SnapshotClient() as client:
        finder = DiscordFinder(client)
        discords = await finder.find_discords([AAVE_SNAPSHOT_SPACE_ID], parties)
        
        if not discords:
            logging.info("No discords found between the parties.")
            return
            
        logging.info(f"\nFound {len(discords)} proposals with different voting choices:")
        for discord in discords:
            logging.info(f"\nProposal ID: {discord.proposal_id}")
            logging.info("Voting Choices:")
            for voter, choice in discord.voter_choices.items():
                logging.info(f"  {voter}: {discord.choices[choice-1]}")

if __name__ == "__main__":
    asyncio.run(main()) 