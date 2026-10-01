"""Streamlit dashboard: ranked shortlist, new-this-week, review queue, methodology."""
import glob
import json
from pathlib import Path

import pandas as pd
import streamlit as st

DATA = Path(__file__).resolve().parent.parent / "data"

st.set_page_config(page_title="Sponsor Radar", layout="wide")
st.title("London Sponsor Radar")
st.caption("Freshly funded London startups × GOV.UK sponsor register")


def load_shortlist() -> pd.DataFrame | None:
    files = sorted(glob.glob(str(DATA / "shortlist_*.csv")))
    return pd.read_csv(files[-1]) if files else None


tab1, tab2, tab3 = st.tabs(["Shortlist", "Review queue", "Methodology"])

with tab1:
    df = load_shortlist()
    if df is None:
        st.info("Run the pipeline to populate data/shortlist CSV.")
    else:
        min_amt = st.slider("Min round (£M)", 0.0, float(df["amount_m"].max()), 0.0)
        show = df[df["amount_m"] >= min_amt]
        st.dataframe(show, use_container_width=True)
        st.caption(f"{len(show)} companies · ranked by funding + hiring + growth + signal")

with tab2:
    mp = DATA / "matches.json"
    if not mp.exists():
        st.info("No matches yet.")
    else:
        m = pd.DataFrame(json.loads(mp.read_text()))
        q = m[m["tier"] == "review"].sort_values("score", ascending=False)
        st.dataframe(q[["dealroom_name", "sponsor_name", "score", "town"]], use_container_width=True)
        st.caption(f"{len(q)} matches need manual review (score 80–90)")

with tab3:
    st.markdown(
        "- VC defaults: `is_vc_round`, exclude Mature 412 + Outside Tech 1102801\n"
        "- HQ London only (628061), standardized rounds, `date` takes YYYY-MM\n"
        "- Score: 0.4 funding + 0.3 hiring + 0.2 growth + 0.1 signal, A-rated boost"
    )
