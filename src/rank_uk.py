"""Rank UK-wide rounds with sponsor cross-ref. Reads dealroom_raw_uk.json, writes shortlist_uk CSV."""
import csv
import json
from datetime import date
from pathlib import Path

from rapidfuzz import fuzz, process

from match import load_sponsors, normalize
from present import COLUMNS, apply_target, growth_str, hq_city, round_label

DATA = Path(__file__).resolve().parent.parent / "data"


def load_jobs() -> dict:
    import json as _json

    p = DATA / "company_jobs.json"
    return _json.loads(p.read_text()) if p.exists() else {}


def main():
    rows = json.loads((DATA / "dealroom_raw_uk.json").read_text())
    sponsors = load_sponsors()
    names = [s.get("Organisation Name", "") for s in sponsors]
    jobs_map = load_jobs()
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
        hq = hq_city(c)
        amount_m = round((tx.get("amount") or 0) / 1e6, 2)
        apply_url, apply_kind = apply_target(jobs_map.get(c.get("uuid"), {}), c, c.get("dealroom_url"))
        out.append(
            {
                "company": name,
                "hq_city": hq,
                "scope": "uk",
                "round_label": round_label(tx, amount_m),
                "std_round": tx.get("standardized_round") or "",
                "year": tx.get("year") or "",
                "month": tx.get("month") or "",
                "amount_m": amount_m,
                "open_roles": jobs.get("open_count") or 0,
                "growth_1y": growth_str(c.get("employee_count_1y_growth")),
                "signal": c.get("signal_rating") or "",
                "sponsor": s.get("Organisation Name"),
                "sponsor_route": s.get("Route"),
                "verified": score >= 90,
                "score": round(base, 3),
                "apply_url": apply_url,
                "apply_kind": apply_kind,
                "dealroom_url": c.get("dealroom_url"),
            }
        )
    out.sort(key=lambda x: (x["verified"], x["score"]), reverse=True)
    fn = DATA / f"shortlist_uk_{date.today().isoformat()}.csv"
    with open(fn, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(out)
    print(f"saved {fn} with {len(out)} rows")


if __name__ == "__main__":
    main()
