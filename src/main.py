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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    datefmt='%H:%M:%S'
)

async def run_discord_finder():
    """Run the discord finder to find proposals with different vote choices."""
    try:
        party1 = PARTIES[0]
        party2 = PARTIES[1]
        space = SPACES[0]
        
        logging.info(
            f"\nReceived Request to Find Proposals with Varying Vote Choices between "
            f"{party1['name']} ({party1['address']}) and {party2['name']} ({party2['address']}) "
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
    target_voter = PARTIES[0]['address']  # Using StableLabs as target
    
    # Log request message
    logging.info(f"\nReceived Request to Find Proposals where {PARTIES[0]['name']} ({target_voter}) is not the highest voting power voter on {SPACES[0]['name']} ({SPACES[0]['space_id']}) Governance\n")
    
    async with SnapshotClient() as client:
        finder = MajorVotingPowerFinder(client)
        # Find cases
        result = await finder.find_votes_against_majority(space_ids, target_voter)
        
        if result:
            # Get voter names
            voter_names = await client.fetch_voter_names([
                result['target_vote']['voter'],
                result['highest_power_vote']['voter']
            ])
            
            # Generate report
            target_name = voter_names[result['target_vote']['voter'].lower()]
            target_addr = result['target_vote']['voter']
            target_vp = result['target_vote']['vp']
            majority_name = voter_names[result['highest_power_vote']['voter'].lower()]
            majority_addr = result['highest_power_vote']['voter']
            majority_vp = result['highest_power_vote']['vp']
            
            logging.info("\n\nFOUND PROPOSAL WHERE TARGET IS NOT THE HIGHEST VOTING POWER VOTER:\n")
            logging.info(f"📊 Proposal: {result['proposal_title']}\n")
            logging.info(f"─────────────────────────────\n")
            logging.info(f"{target_name} ({target_addr}) voted with voting power {target_vp}, ")
            logging.info(f"but highest voting power was {majority_vp} by {majority_name}\n")
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