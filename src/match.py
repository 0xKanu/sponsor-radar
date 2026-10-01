"""Tiered name matching: normalize → exact → domain → rapidfuzz. Writes data/matches.json."""
import csv
import json
import re
from pathlib import Path

from rapidfuzz import fuzz, process

DATA = Path(__file__).resolve().parent.parent / "data"
SUFFIXES = r"\b(ltd|limited|uk|holdings|group|ventures|technologies|technology|labs?|inc|corp|plc|llp|cio|cic|company)\b"


def normalize(name: str) -> str:
    n = name.lower()
    n = re.split(r"\bt/?a\b", n)[0]
    n = re.sub(SUFFIXES, "", n)
    return re.sub(r"[^a-z0-9]", "", n)


def load_sponsors() -> list[dict]:
    with open(DATA / "sponsors.csv", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def main():
    rows = json.loads((DATA / "dealroom_raw.json").read_text())
    sponsors = load_sponsors()
    print(f"matching {len(rows)} companies vs {len(sponsors)} sponsors…")
    names = [s.get("Organisation Name", "") for s in sponsors]
    by_norm: dict[str, int] = {}
    for i, s in enumerate(sponsors):
        ns = normalize(s.get("Organisation Name", ""))
        if ns and ns not in by_norm:
            by_norm[ns] = i
    out = []
    for r in rows:
        tx, comp = r["transaction"], r["company"]
        name = comp.get("name") or tx.get("company", {}).get("name", "")
        domain = comp.get("domain") or ""
        key = normalize(name)
        if key and key in by_norm:
            s = sponsors[by_norm[key]]
            out.append(
                {
                    "dealroom_name": name,
                    "domain": domain,
                    "sponsor_name": s.get("Organisation Name"),
                    "town": s.get("Town/City"),
                    "rating": s.get("Type & Rating"),
                    "route": s.get("Route"),
                    "score": 100.0,
                    "tier": "exact",
                    "uuid": comp.get("uuid"),
                }
            )
            continue
        if domain:
            stem = re.sub(r"[^a-z0-9]", "", domain.split(".")[0].lower())
            hit = None
            if stem and len(stem) > 4:
                for i, s in enumerate(sponsors):
                    ns = normalize(s.get("Organisation Name", ""))
                    if stem == ns or stem in ns:
                        hit = s
                        break
            if hit:
                out.append(
                    {
                        "dealroom_name": name,
                        "domain": domain,
                        "sponsor_name": hit.get("Organisation Name"),
                        "town": hit.get("Town/City"),
                        "rating": hit.get("Type & Rating"),
                        "route": hit.get("Route"),
                        "score": 95.0,
                        "tier": "domain",
                        "uuid": comp.get("uuid"),
                    }
                )
                continue
        best = process.extractOne(name, names, scorer=fuzz.WRatio)
        sname, score, idx = best[0], float(best[1]), best[2]
        s = sponsors[idx]
        tier = "fuzzy" if score >= 90 else ("review" if score >= 80 else "reject")
        out.append(
            {
                "dealroom_name": name,
                "domain": domain,
                "sponsor_name": s.get("Organisation Name"),
                "town": s.get("Town/City"),
                "rating": s.get("Type & Rating"),
                "route": s.get("Route"),
                "score": round(score, 1),
                "tier": tier,
                "uuid": comp.get("uuid"),
            }
        )
    (DATA / "matches.json").write_text(json.dumps(out, indent=1))
    acc = sum(1 for m in out if m["tier"] in ("exact", "domain", "fuzzy"))
    print(f"matched {acc}/{len(out)} auto, {sum(1 for m in out if m['tier']=='review')} to review")


if __name__ == "__main__":
    main()
