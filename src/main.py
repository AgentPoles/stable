import asyncio
import os
from dotenv import load_dotenv
from api.client import SnapshotClient
from services.discord_finder import DiscordFinder

async def main():
    """Main entry point for the application.
    
    Process:
    1. Load environment variables
    2. Initialize clients
    3. Find discords between parties
    4. Display results
    """
    load_dotenv()
    
    space_id = os.getenv("AAVE_SPACE_ID")
    stable_labs = os.getenv("STABLE_LABS")
    areta_labs = os.getenv("ARETA_LABS")
    
    if not all([space_id, stable_labs, areta_labs]):
        raise ValueError("Missing required environment variables")
    
    parties = [stable_labs, areta_labs]
    
    async with SnapshotClient() as client:
        finder = DiscordFinder(client)
        discords = await finder.find_discords([space_id], parties)
        
        if not discords:
            print("No discords found between the parties.")
            return
            
        print(f"\nFound {len(discords)} proposals with different voting choices:")
        for discord in discords:
            print(f"\nProposal ID: {discord.proposal_id}")
            print("Voting Choices:")
            for voter, choice in discord.voter_choices.items():
                print(f"  {voter}: {discord.choices[choice-1]}")

if __name__ == "__main__":
    asyncio.run(main()) 