from chain_analyzer import ChainAnalyzer
import json

def main():
    analyzer = ChainAnalyzer()
    results = analyzer.analyze_all_chains()
    
    # Save results to file
    with open('results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print(f"Found {len(results)} opposing votes across all chains")
    for result in results:
        print(f"\nChain: {result['chain']}")
        print(f"Proposal: {result['proposal_title']}")
        print(f"Whale Vote: {result['whale_vote']} ({result['whale_amount']})")
        print(f"StableLab Vote: {result['stablelab_vote']} ({result['stablelab_amount']})")

if __name__ == "__main__":
    main() 