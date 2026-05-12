"""
Read contacts from an Apollo CSV export.

How to export from Apollo UI:
1. Go to apollo.io → Search → People
2. Filter: Title = "Head of Product" / "VP of Product" / "Recruiter" / "Talent Acquisition" / "Hiring Manager"
           Location = San Francisco, United States, Dubai
3. Select all → Export → CSV
4. Save file as data/apollo_export.csv
"""
import csv
import os
from typing import List


APOLLO_CSV = "data/apollo_export.csv"

COLUMN_MAP = {
    "first_name":   ["First Name", "first_name"],
    "last_name":    ["Last Name", "last_name"],
    "title":        ["Title", "Job Title", "title"],
    "company":      ["Company", "Account Name", "company", "organization_name"],
    "email":        ["Email", "Work Email", "email"],
    "linkedin_url": ["LinkedIn Url", "Person Linkedin Url", "linkedin_url"],
    "location":     ["City", "Location", "location"],
    "funding":      ["Latest Funding", "Funding Stage", "Latest Funding Round Type"],
    "id":           ["Apollo Contact Id", "Person Id", "id"],
}


def _find_col(header: list, candidates: list) -> int:
    for candidate in candidates:
        for i, h in enumerate(header):
            if h.strip().lower() == candidate.lower():
                return i
    return -1


def load_apollo_csv(csv_path: str = APOLLO_CSV) -> List[dict]:
    if not os.path.exists(csv_path):
        print(f"  Apollo CSV not found at {csv_path}")
        print(f"  Export from apollo.io and save as {csv_path}")
        return []

    contacts = []
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader)

        col_idx = {field: _find_col(header, candidates) for field, candidates in COLUMN_MAP.items()}

        def get(row, field):
            idx = col_idx.get(field, -1)
            return row[idx].strip() if idx >= 0 and idx < len(row) else ""

        for row in reader:
            first = get(row, "first_name")
            last = get(row, "last_name")
            name = f"{first} {last}".strip()
            if not name:
                continue

            contacts.append({
                "id":           get(row, "id"),
                "name":         name,
                "first_name":   first,
                "title":        get(row, "title"),
                "company":      get(row, "company"),
                "company_funding": get(row, "funding"),
                "email":        get(row, "email"),
                "email_status": "exported",
                "linkedin_url": get(row, "linkedin_url"),
                "location":     get(row, "location"),
                "status":       "pending",
            })

    print(f"  Loaded {len(contacts)} contacts from Apollo CSV")
    return contacts


if __name__ == "__main__":
    contacts = load_apollo_csv()
    for c in contacts[:5]:
        print(f"  {c['name']} | {c['title']} @ {c['company']} | {c['email']}")
