import asyncio
from src.api.client import SnapshotClient
from src.services.discord_finder import DiscordFinder
from src.config import AAVE_SNAPSHOT_SPACE_ID, STABLE_LABS, WHALE

async def main():
    """Main entry point for the application.
    
    Process:
    1. Initialize clients
    2. Find discords between parties
    3. Display results
    """
    parties = [STABLE_LABS, WHALE]
    
    async with SnapshotClient() as client:
        finder = DiscordFinder(client)
        discords = await finder.find_discords([AAVE_SNAPSHOT_SPACE_ID], parties)
        
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