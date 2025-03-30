# Analyze the Voting Behavior of High-Stakes Whale Entities in DAO Governance Proposals

This project analyzes voting patterns in DAO governance, focusing on high-stakes entities and their influence on proposal outcomes. Using the Snapshot API, we track and compare voting behaviors, identify discrepancies between major voters, and analyze voting power distribution across proposals.

## CHALLENGE

<details>
<summary><strong>Part 1: Address Associated with Stable Labs</strong></summary>

### Implementation

- Identified StableLabs' address: `0xECC2a9240268BC7a26386ecB49E1Befca2706AC9`
- Implemented in `src/config.py` as the target party
- Verified through Snapshot API integration

### Key Features

- Address validation and verification
- Integration with Snapshot's API for address resolution
- Configured as the primary target for voting analysis

### Usage

```python
from src.config import PARTIES

# Access StableLabs' address
stable_labs_address = PARTIES['target']
```

### Configuration

```python
PARTIES = {
    'target': '0xECC2a9240268BC7a26386ecB49E1Befca2706AC9',  # StableLabs
    'whale': '0x8b37a5Af68D315cf5A64097D96621F64b5502a22'    # Areta
}
```

</details>

<details>
<summary><strong>Part 2: Find Proposals where Stable Labs voted opposite to a whale</strong></summary>

### Implementation

- Created `DiscordFinder` service to identify voting discrepancies
- Implemented proposal fetching and comparison logic
- Added sentiment analysis for vote differences

### Key Features

- Batch processing of proposals
- Vote choice comparison between StableLabs and whale
- Sentiment analysis of voting patterns
- Detailed reporting of discrepancies

### Usage

```bash
# Run discord finder
PYTHONPATH=$PYTHONPATH:. python3 src/main.py discord
```

### Sample Output

```
📋 Proposal: [ARFC] wstETH and weETH E-Modes and LT/LTV Adjustments
─────────────────────────────
CREATED[⏰]: March 23, 2025 06:28:39

StableLab voted Against, while Areta voted For
SENTIMENT[😠]: votes are clearly opposing
```

### Implementation Details

- Utilizes Snapshot API for proposal fetching
- Implements pagination for comprehensive analysis
- Provides detailed reporting with timestamps and sentiment indicators
</details>

<details>
<summary><strong>Part 3: Finding proposals where Stable Labs did not have the highest voting power</strong></summary>

### Implementation

- Created `MajorVotingPowerFinder` service
- Implemented voting power comparison logic
- Added pagination support for comprehensive analysis

### Key Features

- Voting power calculation and comparison
- Pagination handling for large datasets
- Detailed reporting of power distribution
- Error handling and edge cases

### Usage

```bash
# Run majority power finder
PYTHONPATH=$PYTHONPATH:. python3 src/main.py majority
```

### Technical Details

- Implemented in `src/services/major_voting_power_finder.py`
- Uses async/await for efficient API calls
- Handles pagination with configurable batch sizes
- Provides detailed logging and error reporting

### Analysis Process

1. Fetches proposals in batches
2. For each proposal:
   - Retrieves all votes
   - Calculates voting power
   - Compares StableLabs' power with others
3. Generates detailed reports for cases where StableLabs isn't the highest power voter
</details>

## Setup and Installation

1. Clone the repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up environment variables if needed
4. Run tests:

```bash
PYTHONPATH=$PYTHONPATH:. pytest tests/ -v
```

## Project Structure

```
src/
├── api/
│   └── client.py          # Snapshot API client
├── services/
│   ├── discord_finder.py  # Vote difference finder
│   └── major_voting_power_finder.py  # Voting power analysis
├── models.py              # Data models
└── main.py               # CLI entry point
```

## Test Coverage

- Services: 100% coverage
- Models: 97% coverage
- API Client: 28% coverage
- Overall: 58% coverage
