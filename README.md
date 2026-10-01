# Sponsor Radar — London startups with money, hiring, and visa sponsorship

Weekly pipeline: Dealroom API (London VC funding + growth + jobs) × GOV.UK sponsor register → ranked Streamlit shortlist.

## Run
```
pip install -r requirements.txt
python src/ingest_sponsors.py
python src/ingest_dealroom.py
python src/match.py
python src/rank.py
streamlit run src/app.py
```

## Creds
`.env` in this folder (never commit). Tokens last 24h, cached in `.token_cache.json`.

## Method
VC defaults per `dealroom-api-analysis.md`: `is_vc_round`, exclude Mature 412 + Outside Tech 1102801, HQ London only, standardized rounds.
