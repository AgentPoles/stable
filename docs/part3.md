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

Additionally, the `getUser` endpoint was used optionally to look up human-readable names for wallet addresses (e.g., StableLab and the whale). This step was only for improving the readability of the final report and is not required for the main logic or computation.

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

- [`src/main.py`](../src/main.py) - Entry point for the application, handles CLI commands and orchestrates the analysis
- [`src/services/reporter.py`](../src/services/reporter.py) - Wraps implementation details and generates readable output
- [`src/services/major_voting_power_finder.py`](../src/services/major_voting_power_finder.py) - Core logic for finding cases where target is not highest voter
- [`src/api/client.py`](../src/api/client.py) - Snapshot API client implementation
- [`src/models.py`](../src/models.py) - Data models for proposals and votes
- [`src/utils/date_formatter.py`](../src/utils/date_formatter.py) - Date and time formatting utilities
