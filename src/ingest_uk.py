"""Full UK sweep: all recent VC rounds HQ'd UK-wide (paginated), enrich each. Saves data/dealroom_raw_uk.json."""
import json
from pathlib import Path

from dealroom_client import api_get
from ingest_dealroom import enrich_company

DATA = Path(__file__).resolve().parent.parent / "data"
UK = 93
PAGE = 200


def main():
    DATA.mkdir(exist_ok=True)
    filt = (
        f"and(hq_location[eq]:{UK},date[gte]:2026-07,"
        "is_vc_round[eq]:true,growth_stage[nin_any]:412,taxonomy_id[nin_any]:1102801)"
    )
    txs, offset, total = [], 0, None
    while True:
        res = api_get(
            "/data/transactions",
            {"filter": filt, "sort": "-date", "limit": PAGE, "offset": offset, "include_total": "true"},
        )
        batch = res.get("data", [])
        txs.extend(batch)
        total = (res.get("page") or {}).get("total", total)
        print(f"page offset={offset}: {len(batch)} (total {total})")
        if len(batch) < PAGE:
            break
        offset += PAGE
    rows = []
    for i, t in enumerate(txs):
        uuid = (t.get("company") or {}).get("uuid", "")
        rows.append({"transaction": t, "company": enrich_company(uuid) if uuid else t.get("company", {})})
        if (i + 1) % 50 == 0:
            print(f"enriched {i + 1}/{len(txs)}")
    (DATA / "dealroom_raw_uk.json").write_text(json.dumps(rows, indent=1))
    print(f"saved {len(rows)} UK rounds")


if __name__ == "__main__":
    main()
