"""Display-ready fields for shortlist CSVs. App does zero formatting math."""

MONTHS = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Unified shortlist schema (london + uk identical).
COLUMNS = [
    "company",
    "hq_city",
    "scope",
    "round_label",
    "std_round",
    "year",
    "month",
    "amount_m",
    "open_roles",
    "growth_1y",
    "signal",
    "sponsor",
    "sponsor_route",
    "verified",
    "score",
    "apply_url",
    "apply_kind",
    "dealroom_url",
]


def money_label(amount_m: float) -> str:
    if amount_m >= 1000:
        return f"${amount_m / 1000:.2f}B"
    return f"${amount_m:.1f}M"


def round_label(tx: dict, amount_m: float) -> str:
    std = tx.get("standardized_round") or "Round"
    y, m = tx.get("year"), tx.get("month")
    when = f"{MONTHS[m]} {y}" if isinstance(m, int) and 1 <= m <= 12 else str(y)
    return f"{std} · {when} · {money_label(amount_m)}"


def growth_str(v) -> str:
    return f"{v:.0f}%" if isinstance(v, (int, float)) else ""


def hq_city(company: dict) -> str:    return (
        next(
            (
                (loc.get("city") or {}).get("name")
                for loc in company.get("locations", [])
                if loc.get("role") == "hq"
            ),
            None,
        )
        or ""
    )


def apply_target(job: dict, company: dict, dealroom_url: str) -> tuple[str, str]:
    """Best apply link: live job ad → company website → Dealroom profile."""
    if job and job.get("apply_url"):
        return job["apply_url"], "job"
    site = (company.get("links") or {}).get("website")
    if site:
        return site, "site"
    return dealroom_url or "", "dealroom"
