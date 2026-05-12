import csv
import os
from typing import List, Set


def load_linkedin_connections(csv_path: str = "data/Connections.csv") -> Set[str]:
    """Returns a set of LinkedIn profile URLs from your exported connections CSV."""
    if not os.path.exists(csv_path):
        print(f"  Connections CSV not found at {csv_path} — all contacts treated as cold")
        return set()

    urls = set()
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        # LinkedIn exports start with a few header rows; skip until we hit the actual header
        reader = csv.reader(f)
        header = None
        for row in reader:
            if "URL" in row or "Profile URL" in row or "LinkedIn Profile URL" in row:
                header = row
                break

        if not header:
            print("  Could not find URL column in Connections CSV")
            return urls

        url_col = next(
            (i for i, h in enumerate(header) if "url" in h.lower()),
            None
        )
        if url_col is None:
            return urls

        for row in reader:
            if len(row) > url_col and row[url_col].strip():
                urls.add(row[url_col].strip().lower().rstrip("/"))

    print(f"  Loaded {len(urls)} LinkedIn connections")
    return urls


def tag_warm_cold(contacts: List[dict], connections: Set[str]) -> List[dict]:
    for c in contacts:
        url = (c.get("linkedin_url") or "").lower().rstrip("/")
        c["is_warm"] = url in connections if url else False
    warm = sum(1 for c in contacts if c["is_warm"])
    print(f"  {warm} warm (already connected), {len(contacts) - warm} cold")
    return contacts
