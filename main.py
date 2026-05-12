"""
Main orchestrator — two-phase daily flow:

  PHASE 1 — Morning discovery (runs automatically at 7am via cron):
    python3.11 main.py --discover
    → Scrapes jobs, scores, finds contacts, WhatsApps you the plan + LinkedIn profiles
    → No emails sent yet

  PHASE 2 — Send outreach (run when you're ready, after tailoring resumes):
    python3.11 main.py --send
    → Attaches tailored PDFs from outputs/ folder, sends emails, logs to Notion

  Other commands:
    python3.11 main.py --dry      → Preview full run, no emails sent
    python3.11 main.py --digest   → Just resend the WhatsApp digest
"""
import argparse
import json
import os
import time

from job_scraper import build_contacts_from_jobs
from scorer import filter_by_alignment
from connections import load_linkedin_connections, tag_warm_cold
from outreach import get_gmail_service, send_outreach
from notion_tracker import log_contact
from tracker import check_replies, load_sent_log, save_sent_log
from digest import send_whatsapp_digest

PLAN_FILE = "data/todays_plan.json"


def already_contacted(email: str, log: dict) -> bool:
    return email in log and log[email].get("status") not in ("send_failed", "no_email")


# ── Phase 1: Discover ─────────────────────────────────────────────────────────

def discover() -> None:
    """Scrape jobs, score, find contacts, WhatsApp the plan. No emails sent."""
    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    print("\n1. Scraping PM job postings + finding recruiter emails...")
    all_contacts = build_contacts_from_jobs(results_per_search=30)

    print("\n2. Scoring alignment (only 4-5/5 get outreach)...")
    scored = filter_by_alignment(all_contacts, min_score=4)

    print("\n3. Cross-checking LinkedIn connections...")
    connections = load_linkedin_connections()
    scored = tag_warm_cold(scored, connections)

    print("\n4. Filtering already-contacted...")
    log = load_sent_log()
    new_contacts = [
        c for c in scored
        if c.get("email") and not already_contacted(c["email"], log)
    ]
    print(f"   {len(new_contacts)} new contacts ready for outreach")

    # Save plan for Phase 2
    with open(PLAN_FILE, "w") as f:
        json.dump(new_contacts, f, indent=2)

    # WhatsApp: today's jobs + planned outreach + LinkedIn profiles
    print("\n5. Sending morning WhatsApp digest...")
    for c in new_contacts:
        c["status"] = "planned"
    send_whatsapp_digest(todays_contacts=new_contacts, todays_jobs=scored)

    print(f"\nPlan saved. When ready: run `python3.11 main.py --send`")
    print(f"Before sending: run `/job-matching` in Claude to generate tailored PDFs in outputs/")


# ── Phase 2: Send ─────────────────────────────────────────────────────────────

def send() -> None:
    """Load today's plan, attach tailored resumes, send emails, log to Notion."""
    if not os.path.exists(PLAN_FILE):
        print("No plan found — run `python3.11 main.py --discover` first")
        return

    with open(PLAN_FILE) as f:
        contacts = json.load(f)

    if not contacts:
        print("No contacts in today's plan")
        return

    print(f"\nSending outreach to {len(contacts)} contacts...")
    service = get_gmail_service()
    log = load_sent_log()
    sent_today = []

    for contact in contacts:
        contact = send_outreach(contact, service=service, dry_run=False)
        notion_page_id = log_contact(contact)
        log[contact["email"]] = {
            "name": contact["name"],
            "company": contact["company"],
            "status": contact["status"],
            "is_warm": contact.get("is_warm", False),
            "notion_page_id": notion_page_id,
            "thread_id": contact.get("gmail_message_id"),
            "resume_attached": contact.get("resume_attached", ""),
        }
        if contact["status"] == "sent":
            sent_today.append(contact)
        time.sleep(2)

    save_sent_log(log)

    print("\nChecking for replies...")
    check_replies(service)

    print("\nSending updated WhatsApp digest...")
    send_whatsapp_digest(todays_contacts=sent_today, todays_jobs=None)
    print("\nDone.")


# ── Full run (for cron / GitHub Actions) ─────────────────────────────────────

def run_full(dry_run: bool = False) -> None:
    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    print("\n1. Scraping PM job postings...")
    all_contacts = build_contacts_from_jobs(results_per_search=30)

    print("\n2. Scoring alignment...")
    scored = filter_by_alignment(all_contacts, min_score=4)
    todays_jobs = scored[:]

    print("\n3. Cross-checking LinkedIn connections...")
    connections = load_linkedin_connections()
    scored = tag_warm_cold(scored, connections)

    print("\n4. Filtering already-contacted...")
    log = load_sent_log()
    new_contacts = [
        c for c in scored
        if c.get("email") and not already_contacted(c["email"], log)
    ]

    if not new_contacts:
        send_whatsapp_digest(todays_contacts=[], todays_jobs=todays_jobs)
        return

    print(f"\n5. Sending outreach {'[DRY RUN]' if dry_run else ''}...")
    service = None if dry_run else get_gmail_service()
    sent_today = []

    for contact in new_contacts:
        contact = send_outreach(contact, service=service, dry_run=dry_run)
        notion_page_id = log_contact(contact)
        log[contact["email"]] = {
            "name": contact["name"],
            "company": contact["company"],
            "status": contact["status"],
            "is_warm": contact.get("is_warm", False),
            "notion_page_id": notion_page_id,
            "thread_id": contact.get("gmail_message_id"),
        }
        if contact["status"] in ("sent", "dry_run"):
            sent_today.append(contact)
        time.sleep(2)

    save_sent_log(log)

    if not dry_run:
        check_replies(service)

    send_whatsapp_digest(todays_contacts=sent_today, todays_jobs=todays_jobs)
    print("\nDone.")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--discover", action="store_true", help="Phase 1: scrape + score + WhatsApp plan (no emails)")
    parser.add_argument("--send",     action="store_true", help="Phase 2: send emails with tailored resumes attached")
    parser.add_argument("--dry",      action="store_true", help="Full run preview, no emails sent")
    parser.add_argument("--digest",   action="store_true", help="Resend WhatsApp digest only")
    args = parser.parse_args()

    if args.discover:
        discover()
    elif args.send:
        send()
    elif args.digest:
        send_whatsapp_digest()
    else:
        run_full(dry_run=args.dry)
