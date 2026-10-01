"""Rank UK-wide rounds with sponsor cross-ref. Reads dealroom_raw_uk.json, writes shortlist_uk CSV."""
import csv
import json
from datetime import date
from pathlib import Path

from rapidfuzz import fuzz, process

from match import load_sponsors, normalize

DATA = Path(__file__).resolve().parent.parent / "data"


def main():
    rows = json.loads((DATA / "dealroom_raw_uk.json").read_text())
    sponsors = load_sponsors()
    names = [s.get("Organisation Name", "") for s in sponsors]
    by_norm = {}
    for i, s in enumerate(sponsors):
        ns = normalize(s.get("Organisation Name", ""))
        if ns and ns not in by_norm:
            by_norm[ns] = i
    out = []
    for r in rows:
        tx, c = r["transaction"], r["company"]
        name = c.get("name") or tx.get("company", {}).get("name", "")
        key = normalize(name)
        if key and key in by_norm:
            s, score = sponsors[by_norm[key]], 100.0
        else:
            best = process.extractOne(name, names, scorer=fuzz.WRatio)
            s, score = sponsors[best[2]], float(best[1])
            if score < 80:
                continue
        if not (s.get("Type & Rating") or "").startswith("Worker (A"):
            continue
        jobs = c.get("jobs", {}) or {}
        base = (
            0.4 * min((tx.get("amount") or 0) / 50_000_000, 1.0)
            + 0.3 * min((jobs.get("open_count") or 0) / 20, 1.0)
            + 0.2 * min((c.get("employee_count_1y_growth") or 0) / 100, 1.0)
            + 0.1 * ((c.get("signal_rating") or 0) / 100)
        )
        hq = next(
            (loc.get("city", {}).get("name") for loc in c.get("locations", []) if loc.get("role") == "hq"),
            None,
        )
        out.append(
            {
                "company": name,
                "hq_city": hq,
                "round": f"{tx.get('year')}-{tx.get('month')} {tx.get('standardized_round')}",
                "amount_m": round((tx.get("amount") or 0) / 1e6, 2),
                "open_roles": jobs.get("open_count"),
                "sponsor": s.get("Organisation Name"),
                "match_score": round(score, 1),
                "score": round(base, 3),
                "dealroom_url": c.get("dealroom_url"),
            }
        )
    out.sort(key=lambda x: x["score"], reverse=True)
    fn = DATA / f"shortlist_uk_{date.today().isoformat()}.csv"
    with open(fn, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    print(f"saved {fn} with {len(out)} rows")


if __name__ == "__main__":
    main()
