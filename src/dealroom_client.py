"""Dealroom API client: .env auth, 24h token cache, 5 req/s throttle, 3 headers."""
import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

BASE = "https://api.beta.dealroom.app"
AUTH_URL = "https://accounts.dealroom.co/oauth/token"
AUDIENCE = "https://api.beta.dealroom.app"
USER_AGENT = "sponsor-radar/1.0"
CACHE_FILE = Path(__file__).resolve().parent.parent / ".token_cache.json"
_LAST_CALL = [0.0]

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
CLIENT_ID = os.environ["DEALROOM_CLIENT_ID"]
CLIENT_SECRET = os.environ["DEALROOM_CLIENT_SECRET"]


def _throttle(min_gap: float = 0.25):
    dt = time.time() - _LAST_CALL[0]
    if dt < min_gap:
        time.sleep(min_gap - dt)
    _LAST_CALL[0] = time.time()


def get_token() -> str:
    now = time.time()
    if CACHE_FILE.exists():
        try:
            cached = json.loads(CACHE_FILE.read_text())
            if cached.get("expires_at", 0) - 300 > now:
                return cached["access_token"]
        except (json.JSONDecodeError, KeyError):
            pass
    _throttle()
    r = requests.post(
        AUTH_URL,
        json={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "audience": AUDIENCE,
            "grant_type": "client_credentials",
        },
        timeout=30,
    )
    r.raise_for_status()
    body = r.json()
    token = body["access_token"]
    CACHE_FILE.write_text(
        json.dumps(
            {"access_token": token, "expires_at": now + body.get("expires_in", 86400)}
        )
    )
    return token


def api_get(path: str, params: dict | None = None, retries: int = 3) -> dict:
    headers = {
        "Authorization": f"Bearer {get_token()}",
        "X-Client-Id": CLIENT_ID,
        "User-Agent": USER_AGENT,
    }
    for attempt in range(retries):
        _throttle()
        r = requests.get(f"{BASE}{path}", headers=headers, params=params, timeout=30)
        if r.status_code == 401 and attempt == 0:
            CACHE_FILE.unlink(missing_ok=True)
            headers["Authorization"] = f"Bearer {get_token()}"
            continue
        if r.status_code == 429:
            time.sleep(int(r.headers.get("Retry-After", "2")))
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError("api_get retries exhausted")
