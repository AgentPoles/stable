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
