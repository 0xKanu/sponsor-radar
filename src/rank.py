"""Score: 0.4 funding + 0.3 hiring + 0.2 growth + 0.1 signal. A-rated only. Display-ready schema."""
import csv
import json
from datetime import date
from pathlib import Path

from present import COLUMNS, growth_str, hq_city, round_label

DATA = Path(__file__).resolve().parent.parent / "data"


def score_tx(amount):
    return min((amount or 0) / 50_000_000, 1.0)


def main():
    rows = json.loads((DATA / "dealroom_raw.json").read_text())
    matches = {m["uuid"]: m for m in json.loads((DATA / "matches.json").read_text())}
    out = []
    for r in rows:
        tx, c = r["transaction"], r["company"]
        jobs = c.get("jobs", {}) or {}
        m = matches.get(c.get("uuid"), {})
        if m.get("tier") == "reject":
            continue
        # Hard exclude: only A-rated Worker licences can issue new CoS.
        if not (m.get("rating") or "").startswith("Worker (A"):
            continue
        base = (
            0.4 * score_tx(tx.get("amount"))
            + 0.3 * min((jobs.get("open_count") or 0) / 20, 1.0)
            + 0.2 * min(((c.get("employee_count_1y_growth")) or 0) / 100, 1.0)
            + 0.1 * ((c.get("signal_rating") or 0) / 100)
        )
        boost = 1.0
        amount_m = round((tx.get("amount") or 0) / 1e6, 2)
        match_score = m.get("score") or 0
        out.append(
            {
                "company": c.get("name"),
                "hq_city": hq_city(c),
                "scope": "london",
                "round_label": round_label(tx, amount_m),
                "std_round": tx.get("standardized_round") or "",
                "year": tx.get("year") or "",
                "month": tx.get("month") or "",
                "amount_m": amount_m,
                "open_roles": jobs.get("open_count") or 0,
                "growth_1y": growth_str(c.get("employee_count_1y_growth")),
                "signal": c.get("signal_rating") or "",
                "sponsor": m.get("sponsor_name"),
                "sponsor_route": m.get("route"),
                "verified": match_score >= 90,
                "score": round(base * boost, 3),
                "dealroom_url": c.get("dealroom_url"),
            }
        )
    # Verified matches first, then by score.
    out.sort(key=lambda x: (x["verified"], x["score"]), reverse=True)
    fn = DATA / f"shortlist_{date.today().isoformat()}.csv"
    with open(fn, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(out)
    print(f"saved {fn} with {len(out)} rows")


if __name__ == "__main__":
    main()
