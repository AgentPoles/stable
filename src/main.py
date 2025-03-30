"""
Main entry point for the application.
Fetches and analyzes voting data from Snapshot.
"""

import asyncio
import logging
import argparse
from src.api.client import SnapshotClient
from src.services.reporter import Reporter
from src.services.major_voting_power_finder import MajorVotingPowerFinder
from src.config import PARTIES, SPACES
from src.utils.date_formatter import format_timestamp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    datefmt='%H:%M:%S'
)

async def run_discord_finder():
    """Run the discord finder to find proposals with different vote choices."""
    try:
        space = SPACES[0]
        
        logging.info(
            f"\nReceived Request to Find Proposals with Varying Vote Choices between "
            f"Target ({PARTIES['target']}) and Whale ({PARTIES['whale']}) "
            f"on {space['name']} ({space['space_id']}) Governance\n"
        )
        
        async with SnapshotClient() as client:
            # Initialize reporter
            reporter = Reporter(client)
            
            # First get proposals to populate cache
            proposals = await client.fetch_proposals([space["space_id"]])
            if not proposals:
                logging.info("\nNo proposals found")
                return
                
            # Generate reports
            reports = await reporter.generate_reports()
            
            if reports:
                for report in reports:
                    logging.info(report)
            else:
                logging.info("\nNo differences found in voting patterns")
                
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        raise

async def run_majority_finder():
    """Run the majority finder to find cases where target voted against majority."""
    # Get space IDs and target voter
    space_ids = [space['space_id'] for space in SPACES]
    target_voter = PARTIES['target']  # Using StableLabs as target
    
    # Log request message
    logging.info(f"\nReceived Request to Find Proposals where Target ({target_voter}) is not the highest voting power voter on {SPACES[0]['name']} ({SPACES[0]['space_id']}) Governance\n")
    
    async with SnapshotClient() as client:
        # Initialize reporter
        reporter = Reporter(client)
        
        # First get proposals to populate cache
        proposals = await client.fetch_proposals(space_ids)
        if not proposals:
            logging.info("\nNo proposals found")
            return
            
        # Generate reports
        reports = await reporter.generate_majority_reports()
        
        if reports:
            for report in reports:
                logging.info(report)
        else:
            logging.info("\nNo cases found where target is not the highest voting power voter.\n")

def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description='Snapshot Voting Analysis Tool')
    parser.add_argument(
        'command',
        choices=['discord', 'majority'],
        help='Command to run: discord (find different votes) or majority (find votes against majority)'
    )
    
    args = parser.parse_args()
    
    if args.command == 'discord':
        asyncio.run(run_discord_finder())
    else:
        asyncio.run(run_majority_finder())

if __name__ == "__main__":
    main() 