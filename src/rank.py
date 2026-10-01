"""Score: 0.4 funding + 0.3 hiring + 0.2 growth + 0.1 signal, x sponsor boost."""
import csv
import json
from datetime import date
from pathlib import Path

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
        base = (
            0.4 * score_tx(tx.get("amount"))
            + 0.3 * min((jobs.get("open_count") or 0) / 20, 1.0)
            + 0.2 * min(((c.get("employee_count_1y_growth")) or 0) / 100, 1.0)
            + 0.1 * ((c.get("signal_rating") or 0) / 100)
        )
        boost = 1.0 if (m.get("rating") or "").startswith("Worker (A") else 0.5
        out.append(
            {
                "company": c.get("name"),
                "round": f"{tx.get('year')}-{tx.get('month')} {tx.get('standardized_round')}",
                "amount_m": round((tx.get("amount") or 0) / 1e6, 2),
                "open_roles": jobs.get("open_count"),
                "growth_1y": c.get("employee_count_1y_growth"),
                "signal": c.get("signal_rating"),
                "sponsor": m.get("sponsor_name"),
                "sponsor_rating": m.get("rating"),
                "sponsor_route": m.get("route"),
                "match_score": m.get("score"),
                "score": round(base * boost, 3),
                "dealroom_url": c.get("dealroom_url"),
            }
        )
    out.sort(key=lambda x: x["score"], reverse=True)
    fn = DATA / f"shortlist_{date.today().isoformat()}.csv"
    with open(fn, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    print(f"saved {fn} with {len(out)} rows")


if __name__ == "__main__":
    main()
