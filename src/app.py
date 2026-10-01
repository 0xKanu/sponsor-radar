"""Sponsor Radar: freshly funded startups that can sponsor your visa. One screen, one job: apply."""
import glob
from pathlib import Path

import pandas as pd
import streamlit as st

DATA = Path(__file__).resolve().parent.parent / "data"

st.set_page_config(page_title="Sponsor Radar", layout="wide")

# Wider feed column reads like a job board, not a database.
st.markdown(
    "<style>div.block-container{max-width:760px;}</style>",
    unsafe_allow_html=True,
)


def load_csv(prefix: str, sample: str) -> pd.DataFrame | None:
    files = sorted(glob.glob(str(DATA / f"{prefix}*.csv")))
    # Prefer full dated shortlists; fall back to committed samples (e.g. Streamlit Cloud).
    dated = [f for f in files if "sample" not in f]
    if dated:
        return pd.read_csv(dated[-1])
    sp = DATA / sample
    return pd.read_csv(sp) if sp.exists() else None


APPLY_LABEL = {"job": "View live role →", "site": "Company site →", "dealroom": "View roles →"}


def apply_link(r) -> tuple[str, str]:
    url = getattr(r, "apply_url", "")
    if isinstance(url, str) and url:
        return url, APPLY_LABEL.get(getattr(r, "apply_kind", ""), "View roles →")
    if isinstance(r.dealroom_url, str) and r.dealroom_url:
        return r.dealroom_url, "View roles →"
    return "", ""


df_london = load_csv("shortlist_2", "sample_shortlist.csv")
df_uk = load_csv("shortlist_uk", "sample_shortlist_uk.csv")

st.title("Sponsor Radar")
st.caption("Freshly funded startups that can sponsor your visa.")

if df_london is None:
    st.info("Run the pipeline to populate the shortlist.")
    st.stop()

# Two controls. That's it.
scope = st.segmented_control("Scope", ["London", "UK-wide"], default="London")
query = st.text_input("Search companies", placeholder="e.g. Fractile")

df = df_uk if scope == "UK-wide" else df_london
if df is None:
    st.info("Run src/ingest_uk.py + src/rank_uk.py for the UK-wide view.")
    st.stop()
if query:
    df = df[df["company"].str.contains(query, case=False, na=False)]

# Hero strip follows the active scope: scope totals up top, search count in the feed caption.
total_funding = df["amount_m"].sum()
total_roles = int(df["open_roles"].sum())
c1, c2, c3 = st.columns(3)
c1.metric("Hiring sponsors", len(df))
c2.metric("Fresh funding tracked", f"${total_funding:,.0f}M")
c3.metric("Open roles", f"{total_roles:,}")

st.caption(f"{len(df)} companies · ranked by funding + hiring + growth · A-rated sponsors only")

for i, r in enumerate(df.itertuples(), start=1):
    roles = int(r.open_roles) if pd.notna(r.open_roles) else 0
    hiring = f"{roles} open roles" if roles else "Hiring now"
    route = r.sponsor_route if isinstance(r.sponsor_route, str) and r.sponsor_route else "Skilled Worker"
    with st.container(border=True):
        st.markdown(f"**#{i} · {r.company}**")
        st.caption(f"{r.round_label} · {hiring}")
        st.markdown(f":green-badge[✓ {route} sponsor]  ·  {r.sponsor}")
        if not r.verified:
            st.caption("⚠️ Unverified name match — check before applying.")
        left, right = st.columns([1, 1])
        with left:
            if isinstance(r.dealroom_url, str) and r.dealroom_url:
                st.link_button("Dealroom profile", r.dealroom_url)
        with right:
            url, label = apply_link(r)
            if url:
                st.link_button(label, url)

st.divider()
st.caption("Data: Dealroom API · GOV.UK sponsor register · A-rated Worker licences only")
with st.expander("How this is built"):
    st.markdown(
        "- Funding: VC rounds only (`is_vc_round`), excluding Mature + Outside Tech, standardized round stages\n"
        "- Geography: HQ London (`628061`) or UK-wide (`93`)\n"
        "- Match: exact → domain → fuzzy; scores below 90 are flagged, never hidden\n"
        "- Rank: 0.4 funding + 0.3 hiring + 0.2 growth + 0.1 signal"
    )
