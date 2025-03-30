# Snapshot Discord Finder

A tool to find voting discords between parties in Snapshot proposals.

## Setup

1. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file with the following variables:

```
AAVE_SPACE_ID=your_aave_space_id
STABLE_LABS=stable_labs_address
ARETA_LABS=areta_labs_address
```

## Running Tests

Run the test suite with coverage:

```bash
pytest
```

## Running the Application

Run the main application:

```bash
python -m src.main
```

## Project Structure

```
.
├── src/
│   ├── api/
│   │   └── client.py
│   ├── services/
│   │   └── discord_finder.py
│   ├── models.py
│   └── main.py
├── tests/
│   ├── conftest.py
│   ├── test_models.py
│   ├── test_client.py
│   └── test_discord_finder.py
├── requirements.txt
├── pytest.ini
└── README.md
```
