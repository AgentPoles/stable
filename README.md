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

## TASK

Locate a governance proposal within the AAVE DAO where StableLab cast a vote opposite to that of another influential whale (on-chain address: 0x8b37a5Af68D315cf5A64097D96621F64b5502a22).

## 2.0 SOLUTION

### Table of Contents

- [2.1 Approach Explanation](#21-approach)
- [2.2 Result Sample](#22-result-sample)
- [2.3 How to Test](#23-how-to-test)

## 2.1 APPROACH

The strategy was to use the Snapshot API to efficiently retrieve and analyze governance data. Two core endpoints were used throughout the process:

- `getMultipleProposals` – to fetch batches of proposals
- `getVotes` – to retrieve voting activity for specific proposals and addresses

In addition, the `getUser` endpoint was used optionally to look up human-readable names for wallet addresses (such as StableLab and the whale). This step was purely for improving the clarity of the final report and is not essential to the main logic or computation.

### Step 1

A single API call was made using `getMultipleProposals` to fetch a batch of proposals from Aave's Governance Space, starting from the latest and moving backward. Only one batch is fetched and processed at a time. If nothing relevant is found in that batch, the next one is fetched. Each batch includes 30 proposals, as set in the `config.py` file.

### Step 2

For all the proposals in the batch, a single API call to `getVotes` was used to fetch all votes cast by StableLab and the whale address per proposal. Snapshot makes this easy by allowing multiple proposals and voter addresses to be passed into one request.

### Step 3

From the collected data, proposals where StableLab and the whale voted differently were filtered out. Their exact vote choices were also recorded.

If no such proposals are found in the current batch, a new batch is fetched and the process starts again from Step 1.
If at least one such proposal is found, there's no need to fetch additional batches — the analysis proceeds to the next steps, since the task is complete once a qualifying proposal is identified.

### Step 4

The vote choices were sent to a custom sentiment processor. It uses a predefined knowledge base of common Aave vote options to determine whether the votes were actually opposing.
It's important to note that vote choices can be different without necessarily being opposing. For example, one voter might select "abstain" while another votes "yes"—technically different, but not necessarily in conflict. The sentiment processor helps account for these nuances by interpreting the intent behind the vote options, rather than just checking for inequality.

### Step 5

A summary report was prepared with the final findings. To make it clearer, the Snapshot `getUser` API was used to retrieve wallet display names (like StableLab and the whale), where available.

## 2.2 RESULT SAMPLE

```log
Received Request to Find Proposals with Varying Vote Choices between Target (0xECC2a9240268BC7a26386ecB49E1Befca2706AC9) and Whale (0x8b37a5Af68D315cf5A64097D96621F64b5502a22) on AAVE (aave.eth) Governance


🔍 Looking for proposals in batches...

[Batch 1-30] Getting proposals...
[Batch 1-30] Found 30 proposals
[Batch 1-30] Finding proposals with different vote choices...
[Batch 1-30] Found 2 proposals with different vote choices
✨ stopping further search



PROPOSALS IN PROCESSED BATCH WITH DIFFERENT VOTE CHOICES


🕵️  Found party names:
    Target (0xECC2a9240268BC7a26386ecB49E1Befca2706AC9): StableLab
    Whale (0x8b37a5Af68D315cf5A64097D96621F64b5502a22): Areta



📋 Proposal: [ARFC] wstETH and weETH E-Modes and LT/LTV Adjustments on Ethereum, Arbitrum, Base
─────────────────────────────
CREATED[⏰]: March 23, 2025 06:28:39

StableLab voted Against, while Areta voted For
SENTIMENT[😠]: votes are clearly opposing



📋 Proposal: [TEMP CHECK] Deploy Aave v3 on Plasma
─────────────────────────────
CREATED[⏰]: March 13, 2025 06:53:41

StableLab voted YAE, while Areta voted Abstain
SENTIMENT[🤔]: one party took a clear position while the other remained neutral
```

## 2.3 HOW TO TEST

### Setup

1. Clone the repository and navigate to the project directory:

   ```bash
   git clone <repository-url>
   cd <project-directory>
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Configuration

1. The target addresses are configured in `src/config.py`:

   ```python
   PARTIES = {
       "target": "0xECC2a9240268BC7a26386ecB49E1Befca2706AC9",  # StableLab
       "whale": "0x8b37a5Af68D315cf5A64097D96621F64b5502a22"    # Whale address
   }
   ```

2. The AAVE space configuration is also in `src/config.py`:
   ```python
   SPACES = [
       {
           "space_id": "aave.eth",
           "name": "AAVE"
       }
   ]
   ```

### Running the Discord Finder

1. Run the discord finder:

   ```bash
   PYTHONPATH=$PYTHONPATH:. python3 src/main.py discord
   ```

2. The output will show:
   - Progress of proposal batch processing
   - Found proposals with different votes
   - Sentiment analysis of the voting differences
   - Human-readable names for the addresses (when available)

### Troubleshooting

- If no proposals are found, try increasing the batch size in `config.py`
- Ensure you have proper internet connectivity for API calls
- Check the logs for any API rate limiting messages

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

## TASK

Locate a governance proposal within the AAVE DAO where StableLab cast a vote opposite to that of another influential whale (on-chain address: 0x8b37a5Af68D315cf5A64097D96621F64b5502a22).

## 2.0 SOLUTION

### Table of Contents

- [2.1 Approach Explanation](#21-approach)
- [2.2 Result Sample](#22-result-sample)
- [2.3 How to Test](#23-how-to-test)

## 2.1 APPROACH

The strategy was to use the Snapshot API to efficiently retrieve and analyze governance data. Two core endpoints were used throughout the process:

- `getMultipleProposals` – to fetch batches of proposals
- `getVotes` – to retrieve voting activity for specific proposals and addresses

In addition, the `getUser` endpoint was used optionally to look up human-readable names for wallet addresses (such as StableLab and the whale). This step was purely for improving the clarity of the final report and is not essential to the main logic or computation.

### Step 1:

A single API call was made using `getMultipleProposals` to fetch a batch of proposals from Aave's Governance Space, starting from the latest and moving backward. Only one batch is fetched and processed at a time. If nothing relevant is found in that batch, the next one is fetched. Each batch includes 30 proposals, as set in the `config.py` file.

### Step 2:

For all the proposals in the batch, a single API call to `getVotes` was used to fetch all votes cast by StableLab and the whale address per proposal. Snapshot makes this easy by allowing multiple proposals and voter addresses to be passed into one request.

### Step 3:

From the collected data, proposals where StableLab and the whale voted differently were filtered out. Their exact vote choices were also recorded.

If no such proposals are found in the current batch, a new batch is fetched and the process starts again from Step 1.
If at least one such proposal is found, there's no need to fetch additional batches — the analysis proceeds to the next steps, since the task is complete once a qualifying proposal is identified.

### Step 4:

The vote choices were sent to a custom sentiment processor. It uses a predefined knowledge base of common Aave vote options to determine whether the votes were actually opposing.
It's important to note that vote choices can be different without necessarily being opposing. For example, one voter might select "abstain" while another votes "yes"—technically different, but not necessarily in conflict. The sentiment processor helps account for these nuances by interpreting the intent behind the vote options, rather than just checking for inequality.

### Step 5:

A summary report was prepared with the final findings. To make it clearer, the Snapshot `getUser` API was used to retrieve wallet display names (like StableLab and the whale), where available.

## 2.2 RESULT SAMPLE
