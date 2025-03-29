import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from chain_analyzer import ChainAnalyzer
from tally_client import TallyClient
from vote_analyzer import VoteAnalyzer

async def analyze_votes():
    # Initialize components
    tally_client = TallyClient()
    vote_analyzer = VoteAnalyzer(tally_client)
    chain_analyzer = ChainAnalyzer(tally_client, vote_analyzer)
    
    # Run analysis
    print("Starting vote analysis...")
    results = await chain_analyzer.analyze_all_chains()
    
    # Sort results by timestamp
    results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    # Print summary
    print("\n=== Opposing Votes Analysis ===")
    print(f"Analysis completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total opposing votes found: {len(results)}")
    
    if results:
        print("\nOpposing votes found:")
        for result in results:
            print(f"\nProposal: {result['proposal_title']}")
            print(f"Chain: {result['chain']}")
            print(f"Whale vote: {result['whale_vote']}")
            print(f"StableLab vote: {result['stablelab_vote']}")
    else:
        print("\nNo opposing votes found between whale and StableLab addresses.")
    
    # Save results to file
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = results_dir / f"opposing_votes_{timestamp}.json"
    
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")

if __name__ == "__main__":
    asyncio.run(analyze_votes()) 