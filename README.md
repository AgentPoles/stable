# Analyze the Voting Behavior of High-Stakes Whale Entities in DAO Governance Proposals

This project analyzes voting patterns in DAO governance, focusing on high-stakes entities and their influence on proposal outcomes. Using the Snapshot API, we track and compare voting behaviors, identify discrepancies between major voters, and analyze voting power distribution across proposals.

## CHALLENGE SOLUTION

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
- [2.4 Code Files](#24-code-files)

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

## 2.4 CODE FILES

The project's core functionality is distributed across several key files:

- [`src/main.py`](src/main.py) - Entry point for the application, handles CLI commands and orchestrates the analysis
- [`src/services/reporter.py`](src/services/reporter.py) - Wraps implementation details and generates readable output
- [`src/services/discord_finder.py`](src/services/discord_finder.py) - Core logic for finding voting discrepancies
- [`src/services/sentiment.py`](src/services/sentiment.py) - Used to determine if vote choices are actually opposing or not even if they are different
- [`src/api/client.py`](src/api/client.py) - Snapshot API client implementation
- [`src/models.py`](src/models.py) - Data models for proposals and votes
- [`src/utils/date_formatter.py`](src/utils/date_formatter.py) - Date and time formatting utilities

</details>

<details>
<summary><strong>Part 3: Finding proposals where Stable Labs did not have the highest voting power</strong></summary>

## TASK

Identify a proposal where the StableLab entity did not vote with the majority of the voting power.

## 3.0 SOLUTION

### Table of Contents

- [3.1 Approach Explanation](#31-approach)
- [3.2 Result Sample](#32-result-sample)
- [3.3 How to Test](#33-how-to-test)
- [3.4 Code Files](#34-code-files)

## 3.1 APPROACH

Similar to Part 2, the strategy here was to use the Snapshot API to efficiently retrieve and analyze governance data. Two core endpoints were used throughout the process:

- `getMultipleProposals` – to fetch batches of proposals
- `getVotes` – to retrieve voting activity for specific proposals and addresses

Note: API response caching was intentionally avoided. The assumption is that each task should be treated in isolation, which is important since some of the same API calls from Part 2 are reused here.

Additionally, the `getUser` endpoint was used optionally to look up human-readable names for wallet addresses (e.g., StableLab). This step was only for improving the readability of the final report and is not required for the main logic or computation.

### Step 1

Same as in Part 2 — a single API call to `getMultipleProposals` was made to fetch a batch of proposals from the Aave Snapshot space, starting from the most recent and moving backward. Only one batch is fetched and processed at a time. If nothing useful is found, the next batch is fetched. Each batch contains 30 proposals, as defined in `config.py`.

### Step 2

For all proposals in the batch, a single API call to `getVotes` (with the voter address set to StableLab) was used to filter down to only those proposals where StableLab actually voted.

### Step 3

For each of the proposals where StableLab voted, another single API call to `getVotes` was made — this time with results ordered by voting power (vp). The request was limited to VOTE_COUNT_MULTIPLIER × number of proposals (where VOTE_COUNT_MULTIPLIER is defined in `config.py`), increasing the chances of retrieving the top voter for each proposal without needing to query them individually. The response includes a combined list of votes across all proposals, sorted in descending order of voting power.

### Step 4

From the list of votes, a dictionary was created to track the highest voter per proposal. Proposals without a corresponding top voter were added to a retry list.
The proposal list was then sorted to match the order from Step 2 (to prioritize the most recent proposals), and each highest voter was compared to StableLab. If the top voter is different, that proposal is marked as a valid case and the process proceeds to the next step. If not, the check continues with the next proposal.

If all proposals are exhausted without finding a valid case, the retry list is used — Step 3 is repeated on that subset. If there's still no result, a new batch of proposals is fetched and the entire process starts over from Step 1.

### Step 5

The result is returned to the reporter service, which attempts to look up display names for the wallet addresses using the `getUser` endpoint, helping generate a clearer and more intuitive report.

## 3.2 RESULT SAMPLE

```log
Received Request to Find Proposals where Target (0xECC2a9240268BC7a26386ecB49E1Befca2706AC9) is not the highest voting power voter on AAVE (aave.eth) Governance


🔍 Searching for proposals in batches...

Found 30 proposals
Found 30 proposals with target votes
Fetching up to 90 highest VP votes...

🎯 Found case where target is not highest power voter!
    Proposal: [ARFC] Launch GHO on Gnosis Chain
    Highest VP: 327712.17238192516 (Address: 0x57ab7ee15ce5ecacb1ab84ee42d5a9d0d8112922)
    Target VP: 43339.13195576

✨ Stopping further search



PROPOSALS WHERE TARGET IS NOT THE HIGHEST VOTING POWER VOTER



📋 Proposal: [ARFC] Launch GHO on Gnosis Chain
─────────────────────────────
CREATED[⏰]: March 26, 2025 14:07:12

Target (0xECC2a9240268BC7a26386ecB49E1Befca2706AC9): StableLab (43339.13195576)
Majority (0x57ab7ee15cE5ECacB1aB84EE42D5A9d0d8112922): UNKNOWN (0x57ab7ee15cE5ECacB1aB84EE42D5A9d0d8112922) (327712.17238192516)
```

## 3.3 HOW TO TEST

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

### Running the Majority Power Finder

1. Run the majority power finder:

   ```bash
   PYTHONPATH=$PYTHONPATH:. python3 src/main.py majority
   ```

2. The output will show:
   - Progress of proposal batch processing
   - Found proposals where target is not the highest voter
   - Voting power comparison between target and highest voter
   - Human-readable names for the addresses (when available)

## 3.4 CODE FILES

The project's core functionality is distributed across several key files:

- [`src/main.py`](src/main.py) - Entry point for the application, handles CLI commands and orchestrates the analysis
- [`src/services/reporter.py`](src/services/reporter.py) - Wraps implementation details and generates readable output
- [`src/services/major_voting_power_finder.py`](src/services/major_voting_power_finder.py) - Core logic for finding cases where target is not highest voter
- [`src/api/client.py`](src/api/client.py) - Snapshot API client implementation
- [`src/models.py`](src/models.py) - Data models for proposals and votes
- [`src/utils/date_formatter.py`](src/utils/date_formatter.py) - Date and time formatting utilities

</details>

<details>
<summary><strong>Setup and Installation</strong></summary>

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Git

### Installation Steps

1. Clone the repository:

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

### Running Tests

Execute the test suite:

```bash
PYTHONPATH=$PYTHONPATH:. pytest tests/ -v
```

### Development Setup

1. Install development dependencies:

   ```bash
   pip install -r requirements-dev.txt
   ```

2. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```

</details>

<details>
<summary><strong>Project Structure</strong></summary>

```
.
├── docs/                  # Documentation
│   ├── part2.md          # Part 2 detailed documentation
│   └── part3.md          # Part 3 detailed documentation
├── src/                  # Source code
│   ├── api/              # API integration
│   │   └── client.py     # Snapshot API client
│   ├── services/         # Core services
│   │   ├── discord_finder.py           # Vote difference finder
│   │   ├── major_voting_power_finder.py # Voting power analysis
│   │   ├── reporter.py                 # Results reporting
│   │   └── sentiment.py                # Vote sentiment analysis
│   ├── utils/           # Utility functions
│   │   └── date_formatter.py # Date formatting utilities
│   ├── config.py        # Configuration settings
│   ├── models.py        # Data models
│   └── main.py          # CLI entry point
├── tests/               # Test suite
│   ├── api/            # API tests
│   ├── services/       # Service tests
│   └── utils/          # Utility tests
├── README.md           # Project documentation
└── requirements.txt    # Project dependencies
```

</details>

<details>
<summary><strong>Test Coverage</strong></summary>

### Coverage Report

| Module      | Coverage |
| ----------- | -------- |
| Services    | 100%     |
| Models      | 97%      |
| API Client  | 28%      |
| Utils       | 95%      |
| **Overall** | 58%      |

### Coverage Details

- **Services (100%)**

  - `discord_finder.py`: Full coverage of vote comparison logic
  - `major_voting_power_finder.py`: Complete coverage of voting power analysis
  - `reporter.py`: All reporting functions tested
  - `sentiment.py`: Full coverage of vote sentiment analysis

- **Models (97%)**

  - Core data structures fully tested
  - Edge cases covered
  - Minor exception paths pending

- **API Client (28%)**
  - Basic request/response flows covered
  - Mock testing for API interactions
  - Integration tests pending
  - Error handling scenarios needed

### Running Coverage Reports

Generate a coverage report:

```bash
PYTHONPATH=$PYTHONPATH:. pytest --cov=src tests/ --cov-report=term-missing
```

Generate HTML coverage report:

```bash
PYTHONPATH=$PYTHONPATH:. pytest --cov=src tests/ --cov-report=html
```

</details>
