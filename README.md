# EquityIQ

AI-assisted equity research and portfolio intelligence platform.

## Product
- Company research dashboard
- Fundamental and valuation metrics
- Portfolio tracking with SQLite
- Relative valuation / peer comparison
- AI research prompt pipeline
- Annual-report research architecture

## Stack
Python · Streamlit · Pandas · Plotly · SQLite · Alpha Vantage

## Local setup
```bash
pip install -r requirements.txt
streamlit run app.py
```

Set `ALPHAVANTAGE_API_KEY` as an environment variable. Never commit API keys.

## Status
Working MVP. AI generation and document/news ingestion are designed as the next modules.