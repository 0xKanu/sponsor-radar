"""Top-UK companion: biggest recent VC rounds HQ'd UK-wide, enrich top 20. Saves data/dealroom_raw_uk.json."""
import json
from datetime import date
from pathlib import Path

from dealroom_client import api_get
from ingest_dealroom import enrich_company

DATA = Path(__file__).resolve().parent.parent / "data"
UK = 93


def main(n: int = 20):
    DATA.mkdir(exist_ok=True)
    filt = (
        f"and(hq_location[eq]:{UK},date[gte]:2026-07,"
        "is_vc_round[eq]:true,growth_stage[nin_any]:412,taxonomy_id[nin_any]:1102801)"
    )
    tx = api_get(
        "/data/transactions",
        {"filter": filt, "sort": "-amount", "limit": 40, "include_total": "true"},
    )
    print("UK total:", tx.get("page", {}).get("total"))
    rows = []
    for t in tx.get("data", [])[:n]:
        uuid = (t.get("company") or {}).get("uuid", "")
        rows.append({"transaction": t, "company": enrich_company(uuid) if uuid else t.get("company", {})})
    (DATA / "dealroom_raw_uk.json").write_text(json.dumps(rows, indent=1))
    print(f"saved {len(rows)} UK rounds")


if __name__ == "__main__":
    main()
