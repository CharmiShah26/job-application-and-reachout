"""
Daily WhatsApp digest — sent every morning.
Covers: ideal-fit jobs found today, who we're reaching out to + why, reply/bounce stats.
"""
import os
from twilio.rest import Client
from datetime import datetime
from notion_tracker import get_status_summary
from tracker import check_replies, load_sent_log
from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM, YOUR_WHATSAPP_NUMBER


def build_message(
    summary: dict,
    updates: dict,
    todays_contacts: list = None,
    todays_jobs: list = None,
) -> str:
    today = datetime.now().strftime("%b %d, %Y")
    lines = [f"👋 *Reachout Daily — {today}*\n"]

    # ── Section 1: Today's ideal-fit jobs ─────────────────────────────────────
    if todays_jobs:
        lines.append("🎯 *Ideal-fit roles found today (4-5/5):*")
        for j in todays_jobs[:5]:
            score = j.get("alignment_score", "?")
            company = j.get("company", "")
            title = j.get("job_title_posted", "")
            url = j.get("job_url", "")
            lines.append(f"  {'⭐⭐' if score == 5 else '⭐'} {company} — {title} ({score}/5)")
            if url and url != "nan":
                lines.append(f"    🔗 {url[:80]}")
        if len(todays_jobs) > 5:
            lines.append(f"  ...and {len(todays_jobs)-5} more — check Notion for full list")
    else:
        lines.append("🎯 *Jobs today:* No new 4-5/5 matches found — retrying tomorrow")

    lines.append("")

    # ── Section 2: Who we're reaching out to today + why + their LinkedIn ─────
    if todays_contacts:
        sent = [c for c in todays_contacts if c.get("status") == "sent"]
        planned = [c for c in todays_contacts if c.get("status") != "sent"]
        group = sent if sent else planned
        label = "📨 *Sent today:*" if sent else "📋 *Planned outreach (run --send to fire):*"
        lines.append(f"{label}")
        for c in group[:5]:
            warm = "🔥" if c.get("is_warm") else "🧊"
            score = c.get("alignment_score", "?")
            resume = f"📎 {os.path.basename(c.get('resume_attached',''))}" if c.get("resume_attached") else "⚠️ no resume"
            lines.append(f"  {warm} *{c.get('name','Someone')}* @ {c.get('company')} ({c.get('title','Recruiter')}) — {score}/5")
            lines.append(f"    Why: Hiring for {c.get('job_title_posted','PM')} | {resume}")
            linkedin = c.get("linkedin_url", "")
            if linkedin and linkedin.startswith("http"):
                lines.append(f"    🔗 {linkedin}")
        if len(group) > 5:
            lines.append(f"  ...+{len(group)-5} more in Notion")
    else:
        lines.append("📨 *Outreach today:* No new contacts — Hunter quota may be low or all contacted")

    lines.append("")

    # ── Section 3: Overall pipeline stats ─────────────────────────────────────
    total = sum(summary.values())
    lines.append("📊 *Pipeline so far:*")
    lines.append(f"  Sent: {summary.get('sent', 0)} | Replied: {summary.get('replied', 0)} ✅ | Bounced: {summary.get('bounced', 0)} ❌")
    lines.append(f"  Pending: {summary.get('pending', 0)} | Total tracked: {total}")

    # ── Section 4: New replies today ──────────────────────────────────────────
    if updates.get("replied"):
        lines.append("\n🎉 *New replies today:*")
        log = load_sent_log()
        for email in updates["replied"]:
            name = log.get(email, {}).get("name", email)
            company = log.get(email, {}).get("company", "")
            lines.append(f"  ✅ {name} @ {company} replied — check Gmail and respond!")

    if updates.get("bounced"):
        lines.append("\n⚠️ *Bounced (need new contact):*")
        log = load_sent_log()
        for email in updates["bounced"]:
            company = log.get(email, {}).get("company", email)
            lines.append(f"  ❌ {company} — find another contact on Apollo or LinkedIn")

    # ── Section 5: Action for today ───────────────────────────────────────────
    lines.append("\n💡 *Your action today:*")
    if updates.get("replied"):
        lines.append("  1. Reply to anyone who responded (within 2 hours is best)")
    if todays_jobs:
        lines.append("  2. Run `/job-matching` in Claude to tailor resumes for today's roles")
    lines.append("  3. Check Notion for full contact list → notion.so")

    return "\n".join(lines)


def send_whatsapp_digest(todays_contacts=None, todays_jobs=None) -> None:
    summary = get_status_summary()
    updates = check_replies()
    message = build_message(summary, updates, todays_contacts, todays_jobs)

    if not TWILIO_ACCOUNT_SID or not YOUR_WHATSAPP_NUMBER:
        print("\n── DIGEST PREVIEW ──")
        print(message)
        return

    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    msg = client.messages.create(
        from_=TWILIO_WHATSAPP_FROM,
        to=YOUR_WHATSAPP_NUMBER,
        body=message,
    )
    print(f"WhatsApp digest sent: {msg.sid}")


if __name__ == "__main__":
    send_whatsapp_digest()
