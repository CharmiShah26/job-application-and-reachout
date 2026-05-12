"""
Scan LinkedIn connections for people worth reaching out to directly —
recruiters, PMs, founders, and people at target companies.
These are warm contacts: already connected, higher reply rate.
"""
import csv
import os
from typing import List
from scorer import DREAM_COMPANIES, SKIP_COMPANIES

CONNECTIONS_CSV = "data/Connections.csv"

# Titles worth reaching out to
TARGET_TITLES = [
    "recruiter", "talent acquisition", "head of talent", "people ops",
    "technical recruiter", "product recruiter", "hr", "hiring",
    "head of product", "vp of product", "vp product", "director of product",
    "chief product officer", "cpo", "group product manager",
    "founder", "co-founder", "ceo", "cto",  # founders often hire directly
]

# Industries / keywords that signal a good company
GOOD_COMPANY_SIGNALS = [
    "ai", "fintech", "saas", "platform", "developer", "consumer",
    "series", "yc", "startup", "tech",
]


def _is_worth_reaching_out(position: str, company: str) -> tuple:
    """Returns (should_contact, reason)"""
    pos = position.lower()
    comp = company.lower()

    # Skip big corps
    if any(s in comp for s in SKIP_COMPANIES):
        return False, ""

    # Dream company — always worth it regardless of title
    if any(d in comp for d in DREAM_COMPANIES):
        return True, f"works at {company} (dream company)"

    # Recruiter/talent at any decent company
    recruiter_titles = ["recruiter", "talent", "hr", "hiring", "people ops"]
    if any(t in pos for t in recruiter_titles):
        return True, f"{position} — can refer or forward your resume"

    # Head of Product / VP / CPO — they hire PMs
    pm_leadership = ["head of product", "vp of product", "vp product",
                     "director of product", "chief product officer", "cpo",
                     "group product manager"]
    if any(t in pos for t in pm_leadership):
        return True, f"{position} — likely hiring or knows who is"

    # Founder/CEO at a startup — often hire PMs directly
    founder_titles = ["founder", "co-founder", "ceo"]
    if any(t in pos for t in founder_titles):
        if any(s in comp for s in GOOD_COMPANY_SIGNALS):
            return True, f"{position} at {company} — founders hire PMs directly"

    return False, ""


def scan_connections(csv_path: str = CONNECTIONS_CSV) -> List[dict]:
    """Find connections worth proactively reaching out to."""
    if not os.path.exists(csv_path):
        print(f"  Connections CSV not found at {csv_path}")
        return []

    worth_reaching_out = []

    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        # Skip header notes until we hit the real header
        reader = csv.reader(f)
        header = None
        for row in reader:
            if "First Name" in row:
                header = row
                break

        if not header:
            return []

        col = {h.strip(): i for i, h in enumerate(header)}

        for row in reader:
            if len(row) < 4:
                continue

            first    = row[col.get("First Name", 0)].strip()
            last     = row[col.get("Last Name", 1)].strip()
            url      = row[col.get("URL", 2)].strip()
            email    = row[col.get("Email Address", 3)].strip()
            company  = row[col.get("Company", 4)].strip()
            position = row[col.get("Position", 5)].strip()

            if not company or not position:
                continue

            should_contact, reason = _is_worth_reaching_out(position, company)
            if not should_contact:
                continue

            worth_reaching_out.append({
                "id": f"conn_{len(worth_reaching_out)}",
                "name": f"{first} {last}".strip(),
                "first_name": first,
                "title": position,
                "company": company,
                "email": email,
                "linkedin_url": url,
                "location": "",
                "company_funding": "",
                "email_status": "connection" if email else "no_email",
                "job_title_posted": "",
                "job_url": "",
                "status": "pending",
                "is_warm": True,
                "alignment_score": 5 if any(d in company.lower() for d in DREAM_COMPANIES) else 4,
                "outreach_reason": reason,
            })

    print(f"  Found {len(worth_reaching_out)} connections worth reaching out to")
    return worth_reaching_out


def get_connections_without_email(limit: int = 20) -> List[dict]:
    """Return warm contacts who need email lookup via Hunter."""
    contacts = scan_connections()
    return [c for c in contacts if not c["email"]][:limit]


if __name__ == "__main__":
    contacts = scan_connections()
    print(f"\nTop connections to reach out to:")
    for c in contacts[:15]:
        email_label = c["email"] if c["email"] else "need email lookup"
        print(f"  {c['name']} | {c['title']} @ {c['company']}")
        print(f"    Why: {c['outreach_reason']} | {email_label}")
        print(f"    LinkedIn: {c['linkedin_url']}")
