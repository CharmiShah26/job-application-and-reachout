"""Check Gmail for replies to outreach emails and update Notion statuses."""
import json
import os
import base64
from outreach import get_gmail_service
from notion_tracker import update_status

STATE_FILE = "data/sent_log.json"


def load_sent_log() -> dict:
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE) as f:
        return json.load(f)


def save_sent_log(log: dict) -> None:
    os.makedirs("data", exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(log, f, indent=2)


def check_replies(service=None) -> dict:
    if service is None:
        service = get_gmail_service()

    log = load_sent_log()
    updates = {"replied": [], "bounced": []}

    # Check for replies (messages in thread after our send)
    for email, entry in log.items():
        if entry.get("status") not in ("sent",):
            continue

        thread_id = entry.get("thread_id")
        if not thread_id:
            continue

        thread = service.users().threads().get(userId="me", id=thread_id).execute()
        messages = thread.get("messages", [])

        if len(messages) > 1:
            # Someone replied
            log[email]["status"] = "replied"
            if entry.get("notion_page_id"):
                update_status(entry["notion_page_id"], "replied")
            updates["replied"].append(email)
            print(f"  Reply detected from {email}")

    # Check for bounces in inbox
    bounces = service.users().messages().list(
        userId="me",
        q='from:mailer-daemon OR subject:"Delivery Status Notification" newer_than:1d'
    ).execute()

    for msg_ref in bounces.get("messages", []):
        msg = service.users().messages().get(userId="me", id=msg_ref["id"], format="metadata").execute()
        headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
        original_to = headers.get("X-Failed-Recipients", "")
        if original_to and original_to in log:
            log[original_to]["status"] = "bounced"
            if log[original_to].get("notion_page_id"):
                update_status(log[original_to]["notion_page_id"], "bounced")
            updates["bounced"].append(original_to)

    save_sent_log(log)
    return updates
