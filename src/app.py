"""Streamlit dashboard: London shortlist, Top UK, review queue, methodology."""
import glob
from pathlib import Path

import pandas as pd
import streamlit as st

DATA = Path(__file__).resolve().parent.parent / "data"

st.set_page_config(page_title="Sponsor Radar", layout="wide")
st.title("London Sponsor Radar")
st.caption("Freshly funded startups × GOV.UK sponsor register — money + hiring + visa licence")


def load_csv(prefix: str, sample: str) -> pd.DataFrame | None:
    files = sorted(glob.glob(str(DATA / f"{prefix}_*.csv")))
    # Prefer full dated shortlists; fall back to committed samples (e.g. Streamlit Cloud).
    if files:
        return pd.read_csv(files[-1])
    sp = DATA / sample
    return pd.read_csv(sp) if sp.exists() else None


def shortlist_tab(df: pd.DataFrame | None, empty_msg: str, key: str):
    if df is None:
        st.info(empty_msg)
        return
    min_amt = st.slider("Min round (£M)", 0.0, float(df["amount_m"].max()), 0.0, key=key)
    show = df[df["amount_m"] >= min_amt]
    st.dataframe(show, use_container_width=True)
    st.caption(f"{len(show)} companies · 0.4 funding + 0.3 hiring + 0.2 growth + 0.1 signal · A-rated only")


tab_london, tab_uk, tab_review, tab_method = st.tabs(
    ["London shortlist", "Top UK", "Review queue", "Methodology"]
)

with tab_london:
    shortlist_tab(load_csv("shortlist_2", "sample_shortlist.csv"),
                  "Run the pipeline to populate the London shortlist.", key="amt_london")

with tab_uk:
    shortlist_tab(load_csv("shortlist_uk", "sample_shortlist_uk.csv"),
                  "Run src/ingest_uk.py + src/rank_uk.py for the UK-wide view.", key="amt_uk")

with tab_review:
    st.markdown(
        "Fuzzy matches scoring 80–90 land here for manual accept/reject. "
        "Known traps: same-name nurseries, civil-engineering firms, similarly named ventures — "
        "always check the `dealroom_url` before applying."
    )

with tab_method:
    st.markdown(
        "- **VC defaults** (`dealroom-api-analysis.md`): `is_vc_round`, exclude Mature `412` + Outside Tech `1102801`, standardized rounds\n"
        "- **London** = HQ city `628061` · **UK** = country `93` · `date` filter takes `YYYY-MM`\n"
        "- **Sponsor filter**: A-rated Worker licences only — B-rated sponsors can't issue new CoS\n"
        "- **Hypothesis test**: compare round `year-month` vs open `open_roles` — fresh funding with live postings surfaces employers earlier than job boards"
    )
