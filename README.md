# DAO Vote Analyzer

This tool analyzes voting patterns in DAO governance proposals, specifically focusing on finding opposing votes between StableLab and a specific whale address in AAVE governance.

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your Tally API key:
   ```
   TALLY_API_KEY=your_api_key_here
   ```

## Running Tests

```bash
pytest tests/
```

## Running the Analysis

```bash
python src/main.py
```

The results will be saved to `results.json` and printed to the console.

## Project Structure

- `src/`: Source code
  - `tally_client.py`: Tally API client
  - `vote_analyzer.py`: Vote analysis logic
  - `chain_analyzer.py`: Multi-chain analysis
  - `main.py`: Main script
- `tests/`: Test files
- `data/`: Data files
  - `stablelab_addresses.json`: List of StableLab addresses
