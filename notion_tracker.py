import requests
from datetime import datetime, timezone
from typing import Optional
from config import NOTION_TOKEN, NOTION_DATABASE_ID

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

STATUS_OPTIONS = ["pending", "sent", "replied", "bounced", "no_email", "send_failed", "dry_run"]


def _text(value: str) -> dict:
    return {"rich_text": [{"text": {"content": str(value)[:2000]}}]}


def _title(value: str) -> dict:
    return {"title": [{"text": {"content": str(value)[:2000]}}]}


def _select(value: str) -> dict:
    return {"select": {"name": value}}


def _date(dt: str) -> dict:
    return {"date": {"start": dt}}


def log_contact(contact: dict) -> Optional[str]:
    if not NOTION_TOKEN or not NOTION_DATABASE_ID:
        print("  Notion not configured — skipping tracker log")
        return None

    now = datetime.now(timezone.utc).isoformat()
    email_val = contact.get("email", "")
    linkedin_val = contact.get("linkedin_url", "")

    props = {
        "Name": _title(contact.get("name", "")),
        "Title": _text(contact.get("title", "")),
        "Company": _text(contact.get("company", "")),
        "Funding Stage": _text(contact.get("company_funding", "")),
        "Location": _text(contact.get("location", "")),
        "Status": _select(contact.get("status", "pending")),
        "Warm": {"checkbox": contact.get("is_warm", False)},
        "Sent At": _date(now),
        "Apollo ID": _text(contact.get("id", "")),
        "Notes": _text(contact.get("job_title_posted", "")),
    }

    # Only include email/url fields if non-empty (Notion validates format)
    if email_val:
        props["Email"] = {"email": email_val}
    if linkedin_val and linkedin_val.startswith("http"):
        props["LinkedIn"] = {"url": linkedin_val}

    payload = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": props,
    }

    resp = requests.post("https://api.notion.com/v1/pages", headers=HEADERS, json=payload)
    if resp.status_code == 200:
        page_id = resp.json()["id"]
        return page_id
    else:
        print(f"  Notion error: {resp.status_code} {resp.text[:200]}")
        return None


def update_status(page_id: str, status: str, note: str = "") -> None:
    if not NOTION_TOKEN:
        return

    props = {"Status": _select(status)}
    if note:
        props["Notes"] = _text(note)
    if status == "replied":
        props["Replied At"] = _date(datetime.now(timezone.utc).isoformat())

    requests.patch(
        f"https://api.notion.com/v1/pages/{page_id}",
        headers=HEADERS,
        json={"properties": props},
    )


def get_status_summary() -> dict:
    if not NOTION_TOKEN or not NOTION_DATABASE_ID:
        return {}

    payload = {"filter": {"property": "Status", "select": {"is_not_empty": True}}}
    resp = requests.post(
        f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query",
        headers=HEADERS,
        json=payload,
    )
    if resp.status_code != 200:
        return {}

    counts: dict[str, int] = {}
    for page in resp.json().get("results", []):
        status = page["properties"].get("Status", {}).get("select", {})
        if status:
            name = status.get("name", "unknown")
            counts[name] = counts.get(name, 0) + 1

    return counts
