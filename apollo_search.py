import requests
import json
import time
from typing import List
from config import APOLLO_API_KEY, HIRING_TITLES, TARGET_LOCATIONS, TARGET_FUNDING_STAGES, RESULTS_PER_RUN

BASE_URL = "https://api.apollo.io/v1"

HEADERS = {
    "Content-Type": "application/json",
    "Cache-Control": "no-cache",
    "X-Api-Key": APOLLO_API_KEY,
}

FUNDING_STAGE_MAP = {
    "Series A": "series_a",
    "Series B": "series_b",
    "Series C": "series_c",
    "Seed": "seed",
    "Pre-Seed": "angel",
}


def search_contacts(page: int = 1) -> List[dict]:
    payload = {
        "page": page,
        "per_page": min(RESULTS_PER_RUN, 100),
        "person_titles": HIRING_TITLES,
        "person_locations": TARGET_LOCATIONS,
        "organization_funding_stages": [
            FUNDING_STAGE_MAP[s] for s in TARGET_FUNDING_STAGES if s in FUNDING_STAGE_MAP
        ],
        "contact_email_status": ["verified", "guessed"],
    }

    resp = requests.post(f"{BASE_URL}/contacts/search", headers=HEADERS, json=payload)
    resp.raise_for_status()
    data = resp.json()

    contacts = data.get("contacts", [])
    print(f"  Page {page}: {len(contacts)} contacts found (total available: {data.get('pagination', {}).get('total_entries', '?')})")
    return contacts


def extract_contact(raw: dict) -> dict:
    emails = raw.get("email_status", "")
    primary_email = raw.get("email", "")

    org = raw.get("organization", {}) or {}
    return {
        "id": raw.get("id", ""),
        "name": raw.get("name", ""),
        "first_name": raw.get("first_name", ""),
        "title": raw.get("title", ""),
        "company": org.get("name", raw.get("organization_name", "")),
        "company_funding": org.get("latest_funding_stage", ""),
        "email": primary_email,
        "email_status": emails,
        "linkedin_url": raw.get("linkedin_url", ""),
        "location": raw.get("city", "") + ", " + raw.get("country", ""),
        "status": "pending",
    }


def fetch_all_targets(max_pages: int = 3) -> List[dict]:
    all_contacts = []
    for page in range(1, max_pages + 1):
        try:
            raw = search_contacts(page)
            if not raw:
                break
            all_contacts.extend([extract_contact(c) for c in raw])
            time.sleep(1)
        except requests.HTTPError as e:
            print(f"  Apollo API error on page {page}: {e}")
            break
    return all_contacts


if __name__ == "__main__":
    print("Searching Apollo for hiring managers and recruiters...")
    contacts = fetch_all_targets(max_pages=2)
    print(f"\nFound {len(contacts)} contacts total")
    for c in contacts[:5]:
        print(f"  {c['name']} | {c['title']} @ {c['company']} | {c['email']} | {c['location']}")
