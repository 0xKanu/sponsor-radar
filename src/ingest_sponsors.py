"""Download GOV.UK sponsor register CSV. Saves data/sponsors.csv."""
import urllib.request
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
CSV_URL = (
    "https://assets.publishing.service.gov.uk/media/"
    "6abe33d2efad0f1df6722889/SP_-_Worker_and_Temporary_Worker_Web_Register_-_2026-10-01.csv"
)
# If the dated URL 404s (register updates daily), open:
# https://www.gov.uk/government/publications/register-of-licensed-sponsors-workers
# and paste the new 'Register of Worker ...' CSV link here.


def main(url: str = CSV_URL):
    DATA.mkdir(exist_ok=True)
    out = DATA / "sponsors.csv"
    urllib.request.urlretrieve(url, out)
    print(f"saved {out} ({out.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
