# Supply Chain Shock Simulator

A data analytics and simulation platform for modeling, forecasting, and optimizing supply chain disruptions.

## Project Structure

```
SupplyChainShockSimulator/
├── data/               # Raw, processed, and external data
├── notebooks/          # Exploratory Jupyter notebooks
├── src/                # Core Python modules
│   ├── ingestion/      # Data ingestion pipelines
│   ├── cleaning/       # Data cleaning & validation
│   ├── database/       # DB models & connections
│   ├── analytics/      # Statistical analysis
│   ├── forecasting/    # ML forecasting models
│   ├── simulation/     # Shock simulation engine
│   ├── optimization/   # Supply chain optimization
│   └── utils/          # Shared utilities
├── app/                # Streamlit dashboard
│   ├── pages/          # Multi-page app pages
│   └── components/     # Reusable UI components
├── powerbi/            # Power BI reports & datasets
├── tests/              # Unit and integration tests
└── docs/               # Documentation
```

## Setup

```bash
# Create virtual environment
python -m venv .venv
.venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env  # then fill in values
```

## Running the App

```bash
streamlit run app/main.py
```

## Running Tests

```bash
pytest tests/
```
