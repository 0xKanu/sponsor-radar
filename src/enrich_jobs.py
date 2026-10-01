"""Latest live job posting per company. Reads dealroom_raw*.json, writes data/company_jobs.json."""
import json
from pathlib import Path

from dealroom_client import api_get

DATA = Path(__file__).resolve().parent.parent / "data"


def latest(uuid: str) -> dict:
    try:
        res = api_get(
            "/data/jobs",
            {
                "filter": f"entity_id[eq]:{uuid}",
                "sort": "-date_posted",
                "limit": 1,
                "include_total": "true",
            },
        )
    except Exception:
        return {}
    items = res.get("data", [])
    total = (res.get("page") or {}).get("total")
    if not items:
        return {"active_postings": total or 0}
    j = items[0]
    return {
        "apply_url": j.get("url"),
        "job_title": j.get("title"),
        "job_date": j.get("date_posted"),
        "active_postings": total,
    }


def main():
    uuids: dict[str, bool] = {}
    for fn in ("dealroom_raw.json", "dealroom_raw_uk.json"):
        p = DATA / fn
        if p.exists():
            for r in json.loads(p.read_text()):
                u = (r.get("company") or {}).get("uuid")
                if u:
                    uuids[u] = True
    print(f"{len(uuids)} companies")
    out = {}
    for i, u in enumerate(uuids):
        out[u] = latest(u)
        if (i + 1) % 50 == 0:
            print(f"jobs {i + 1}/{len(uuids)}")
    (DATA / "company_jobs.json").write_text(json.dumps(out, indent=1))
    hits = sum(1 for v in out.values() if v.get("apply_url"))
    print(f"live ad URLs for {hits}/{len(out)}")


if __name__ == "__main__":
    main()
