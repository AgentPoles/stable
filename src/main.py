"""
Main entry point for the application.
Fetches and analyzes voting data from Snapshot.
"""

import asyncio
import logging
from src.api.client import SnapshotClient
from src.services.reporter import Reporter
from src.config import PARTIES, SPACES

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    datefmt='%H:%M:%S'
)

async def main():
    """Main entry point for the application."""
    try:
        party1 = PARTIES[0]
        party2 = PARTIES[1]
        space = SPACES[0]
        
        logging.info(
            f"\nReceived Request to Find Proposals with Varying Vote Choices between "
            f"{party1['name']} ({party1['address']}) and {party2['name']} ({party2['address']}) "
            f"on {space['name']} ({space['space_id']}) Governance\n"
        )
        
        # Initialize client
        client = SnapshotClient()
        
        # Initialize reporter
        reporter = Reporter(client)
        
        # Generate reports
        reports = await reporter.generate_reports()
        
        # Print reports
        if reports:
            for report in reports:
                logging.info(report)
        else:
            logging.info("\nNo differences found in voting patterns")
            
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 