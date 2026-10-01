# Sponsor Radar — London startups with money, hiring, and visa sponsorship

> International graduates can only join UK visa sponsors. This pipeline finds London startups with fresh funding + live hiring, cross-references the GOV.UK sponsor register (143k employers), and ranks A-rated sponsors first — testing whether funding signals surface employers earlier than job boards. Latest run: 136 London VC rounds → 98 ranked, 16 UK-wide.

Weekly pipeline: Dealroom API (London VC funding + growth + jobs) × GOV.UK sponsor register → ranked Streamlit shortlist.

## Run
```
pip install -r requirements.txt
python src/ingest_sponsors.py   # then save CSV as data/sponsors.csv
python src/ingest_dealroom.py
python src/match.py
python src/rank.py
python src/ingest_uk.py && python src/rank_uk.py   # Top-UK tab
streamlit run src/app.py
```

## Creds
`.env` in this folder (never commit). Tokens last 24h, cached in `.token_cache.json`.

## Method
VC defaults per `dealroom-api-analysis.md`: `is_vc_round`, exclude Mature 412 + Outside Tech 1102801, HQ London only, standardized rounds.
