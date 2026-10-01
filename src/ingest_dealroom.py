"""Pull London VC transactions (90d window) + enrich companies. Saves data/dealroom_raw.json."""
import json
from datetime import date, timedelta
from pathlib import Path

from dealroom_client import api_get

DATA = Path(__file__).resolve().parent.parent / "data"
LONDON = 628061


def recent_transactions(months_back: int = 3, limit: int = 200) -> dict:
    since_ym = (date.today().replace(day=1) - timedelta(days=30 * (months_back - 1))).strftime("%Y-%m")
    filt = (
        f"and(hq_location[eq]:{LONDON},date[gte]:{since_ym},"
        "is_vc_round[eq]:true,growth_stage[nin_any]:412,taxonomy_id[nin_any]:1102801)"
    )
    return api_get(
        "/data/transactions",
        {"filter": filt, "sort": "-date", "limit": limit, "include_total": "true"},
    )


def enrich_company(uuid: str) -> dict:
    try:
        res = api_get(f"/data/companies/{uuid}")
        return res.get("data", res) if isinstance(res, dict) else {}
    except Exception:
        return {}


def main():
    DATA.mkdir(exist_ok=True)
    tx = recent_transactions()
    rows = []
    for t in tx.get("data", []):
        c = t.get("company", {})
        full = enrich_company(c.get("uuid", "")) if c.get("uuid") else {}
        rows.append({"transaction": t, "company": full or c})
    (DATA / "dealroom_raw.json").write_text(json.dumps(rows, indent=1))
    print(f"saved {len(rows)} rounds (total {tx.get('page', {}).get('total')})")


if __name__ == "__main__":
    main()
