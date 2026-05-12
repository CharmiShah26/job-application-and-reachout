"""
Scrape PM job postings from LinkedIn/Indeed, filter to relevant companies,
then find recruiter emails via Hunter.io + Apollo enrichment as fallback.
"""
import requests
import time
from typing import List
from jobspy import scrape_jobs

# Skip giant corps — focus on startups/scale-ups where outreach works
SKIP_COMPANIES = {
    "apple", "google", "meta", "amazon", "microsoft", "netflix",
    "amazon web services", "amazon.com", "samsung", "bank of america",
    "jpmorgan", "jpmorganchase", "citi", "cognizant", "ibm",
    "accenture", "deloitte", "goldman sachs", "warner bros. discovery",
}

SEARCH_TERMS    = ["product manager", "senior product manager", "head of product"]
LOCATIONS       = ["San Francisco, CA", "New York, NY", "Remote"]
RECRUITER_TITLES = ["recruiter", "talent", "hr", "people", "hiring"]


def scrape_pm_jobs(results_per_search: int = 30) -> list:
    import pandas as pd
    all_jobs = []
    for term in SEARCH_TERMS:
        for location in LOCATIONS:
            try:
                jobs = scrape_jobs(
                    site_name=["linkedin", "indeed"],
                    search_term=term,
                    location=location,
                    results_wanted=results_per_search,
                    hours_old=168,
                    country_indeed="USA",
                )
                all_jobs.append(jobs)
                print(f"  '{term}' in {location}: {len(jobs)} jobs")
                time.sleep(2)
            except Exception as e:
                print(f"  Skipping '{term}' in {location}: {e}")

    if not all_jobs:
        return []
    combined = pd.concat(all_jobs, ignore_index=True)
    combined = combined.drop_duplicates(subset=["company"])
    return combined.to_dict("records")


# ── Email finders ─────────────────────────────────────────────────────────────

def _apollo_enrich(first: str, last: str, company: str, apollo_key: str) -> str:
    """Try Apollo people/match to get an email (uses 1 credit)."""
    try:
        resp = requests.post(
            "https://api.apollo.io/v1/people/match",
            headers={"Content-Type": "application/json", "X-Api-Key": apollo_key},
            json={
                "first_name": first,
                "last_name": last,
                "organization_name": company,
                "reveal_personal_emails": False,
            },
            timeout=10,
        )
        person = resp.json().get("person") or {}
        return person.get("email", "")
    except Exception:
        return ""


def _hunter_domain_search(company: str, hunter_key: str) -> dict:
    """Find recruiter email at a company via Hunter.io (uses 1 credit)."""
    try:
        # Step 1: resolve company → domain
        r1 = requests.get(
            "https://api.hunter.io/v2/domain-search",
            params={"company": company, "api_key": hunter_key, "limit": 1},
            timeout=10,
        )
        if r1.status_code == 429:
            print("  Hunter quota exhausted for today")
            return {}
        domain = r1.json().get("data", {}).get("domain", "")
        if not domain:
            return {}

        time.sleep(1.5)

        # Step 2: search emails on that domain, prefer recruiter titles
        r2 = requests.get(
            "https://api.hunter.io/v2/domain-search",
            params={"domain": domain, "api_key": hunter_key, "limit": 10},
            timeout=10,
        )
        if r2.status_code == 429:
            return {}
        emails = r2.json().get("data", {}).get("emails", [])

        for e in emails:
            if any(t in (e.get("position") or "").lower() for t in RECRUITER_TITLES):
                return e
        return emails[0] if emails else {}
    except Exception:
        return {}


def build_contacts_from_jobs(results_per_search: int = 30) -> List[dict]:
    from config import APOLLO_API_KEY, HUNTER_API_KEY

    print("Scraping PM job postings...")
    jobs = scrape_pm_jobs(results_per_search)
    print(f"  {len(jobs)} unique companies found — filtering big corps...")

    seen, contacts = set(), []
    hunter_calls  = 0
    HUNTER_LIMIT  = 20  # stay well within free monthly quota

    for job in jobs:
        company = str(job.get("company") or "").strip()
        if company.lower() in ("nan", "none", ""):
            continue
        if company.lower() in SKIP_COMPANIES:
            continue
        if company.lower() in seen:
            continue
        seen.add(company.lower())

        recruiter = {}
        email = ""

        # --- Hunter.io: domain search returns name + email together ---
        if HUNTER_API_KEY and hunter_calls < HUNTER_LIMIT:
            print(f"  [{hunter_calls+1}] {company}")
            recruiter = _hunter_domain_search(company, HUNTER_API_KEY)
            hunter_calls += 1
            email = recruiter.get("value", "")
            time.sleep(1.5)

        # --- Apollo fallback: if Hunter found a name but no email ---
        if not email and recruiter.get("first_name") and APOLLO_API_KEY:
            email = _apollo_enrich(
                recruiter.get("first_name", ""),
                recruiter.get("last_name", ""),
                company, APOLLO_API_KEY,
            )

        if not email:
            continue

        contacts.append({
            "id": f"job_{len(contacts)}",
            "name": (
                f"{recruiter.get('first_name', '')} {recruiter.get('last_name', '')}".strip()
                or "Hiring Team"
            ),
            "first_name": recruiter.get("first_name", "there"),
            "title": recruiter.get("position", "Recruiter"),
            "company": company,
            "company_funding": "",
            "email": email,
            "email_status": str(recruiter.get("confidence", "unknown")),
            "linkedin_url": recruiter.get("linkedin", ""),
            "location": str(job.get("location", "")),
            "job_title_posted": str(job.get("title", "")),
            "job_url": str(job.get("job_url", "")),
            "status": "pending",
        })

    print(f"\n  {len(contacts)} contacts with emails ready to outreach")
    return contacts


if __name__ == "__main__":
    contacts = build_contacts_from_jobs(results_per_search=10)
    print(f"\n{'='*60}")
    for c in contacts:
        print(f"  {c['name']} | {c['title']} @ {c['company']} | {c['email']}")
