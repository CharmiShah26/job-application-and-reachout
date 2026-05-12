# Reachouts — How to Run Every Day (No Claude Needed)

## What This System Does Each Day

1. Scrapes LinkedIn + Indeed for PM/APM/TPM job postings (last 7 days)
2. Scores each company 1–5 against your profile (only 4-5/5 pass)
3. Finds the recruiter/hiring manager email at each company via Hunter.io
4. Cross-checks your LinkedIn connections (warm vs cold template)
5. Sends personalized Gmail outreach WITH tailored resume attached
6. Logs every contact to your Notion "Reachout Tracker" database
7. WhatsApps you: today's ideal-fit jobs, who we're reaching out to + their LinkedIn, reply stats

---

## Your Ideal Daily Routine (Two Phases)

### Phase 1 — 7am (automatic, while you sleep)
Cron runs `--discover`: scrapes jobs, scores them, finds recruiter contacts.
You wake up to a WhatsApp showing:
- Today's 4-5/5 job matches with apply links
- Who we plan to email + their **LinkedIn profile** + why each one
- No emails sent yet — you're in control

### Phase 2 — When you open your laptop (~15 min)
1. **Check WhatsApp** → see today's targets, tap their LinkedIn links to review
2. **Open Claude Desktop** → run `/job-matching tailor resume for [Company]` for each match
   - Claude generates `Charmi_Shah_Figma_APM.pdf`, saves to `outputs/` folder automatically
3. **Send outreach** → one command fires all emails with tailored PDFs attached:
   ```bash
   cd /Users/charmishah/Documents/Projects/Reachouts
   python3.11 main.py --send
   ```
4. Done — Notion updates automatically, replies tracked, next digest queued

---

## All Commands

```bash
cd /Users/charmishah/Documents/Projects/Reachouts

# Phase 1: scrape + score + WhatsApp plan (no emails sent)
python3.11 main.py --discover

# Phase 2: send emails with tailored resumes attached
python3.11 main.py --send

# Preview full run (no emails, just shows what would happen)
python3.11 main.py --dry

# Resend WhatsApp digest only
python3.11 main.py --digest

# Full automated run (no phases — sends immediately, for GitHub Actions)
python3.11 main.py
```

---

## Set Up Automatic 7am Discovery (One-Time)

```bash
crontab -e
```

Add this line:
```
0 7 * * * cd /Users/charmishah/Documents/Projects/Reachouts && python3.11 main.py --discover >> logs/daily.log 2>&1
```

After this, Phase 1 runs every morning at 7am. You just wake up, check WhatsApp, tailor resumes, run `--send`.

---

## Option: Run Fully in the Cloud (Mac Can Be Off)

Use GitHub Actions so nothing depends on your Mac being on.

1. Create a private GitHub repo and push this folder
2. Add all `.env` values as GitHub Secrets (Settings → Secrets → Actions)
3. Create `.github/workflows/daily.yml`:

```yaml
name: Daily Reachout
on:
  schedule:
    - cron: '0 15 * * *'   # 7am SF time (UTC-8)
jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python main.py --discover
        env:
          APOLLO_API_KEY: ${{ secrets.APOLLO_API_KEY }}
          HUNTER_API_KEY: ${{ secrets.HUNTER_API_KEY }}
          GMAIL_SENDER: ${{ secrets.GMAIL_SENDER }}
          NOTION_TOKEN: ${{ secrets.NOTION_TOKEN }}
          NOTION_DATABASE_ID: ${{ secrets.NOTION_DATABASE_ID }}
          TWILIO_ACCOUNT_SID: ${{ secrets.TWILIO_ACCOUNT_SID }}
          TWILIO_AUTH_TOKEN: ${{ secrets.TWILIO_AUTH_TOKEN }}
          YOUR_WHATSAPP_NUMBER: ${{ secrets.YOUR_WHATSAPP_NUMBER }}
```

---

## How Resume Tailoring Works

Resume tailoring is done by Claude's `/job-matching` Cowork skill. It knows:
- Your full background (AWS SDE, E-Cornell PM, Cornell M.Eng — all locked, never fabricated)
- Which bullets to lead with per role type:
  - **TPM roles** (Stripe, Linear, Vercel) → lead AWS bullets
  - **Growth/Consumer roles** (Airbnb, Robinhood) → lead E-Cornell PM bullets
  - **AI roles** (Glean, Perplexity, Clay) → lead E-Cornell SWE/RAG bullets
  - **Dubai roles** (Tabby, Careem) → add MENA relocation note
- XYZ bullet format: *"Accomplished X as measured by Y by doing Z"*
- Output: `Charmi_Shah_[Company]_[Role].pdf` saved to `outputs/`

**To tailor in Claude Desktop:**
```
/job-matching tailor my resume for Figma APM role
/job-matching tailor my resume for Stripe Technical PM
/job-matching find me 4-5/5 PM roles today
```

**Resume naming** (so `--send` picks them up automatically):
```
outputs/Charmi_Shah_Figma_APM.pdf
outputs/Charmi_Shah_Stripe_TPM.pdf
outputs/Charmi_Shah_Ramp_PM.pdf
```

---

## Monitoring

| Where | What to check |
|---|---|
| WhatsApp | Morning digest — jobs, contacts, LinkedIn links, reply alerts |
| Notion | Full pipeline — every contact's status (sent/replied/bounced) |
| Gmail | Replies from recruiters — respond within 2 hours |
| `logs/daily.log` | Full terminal output from each run |
| `data/sent_log.json` | Raw log of every contact emailed |

---

## API Quotas

| Service | Free limit | Resets |
|---|---|---|
| Hunter.io | 50 searches/month | 11th of each month |
| Apollo | 120 email credits/year | Annually |
| Gmail | 500 emails/day | Daily |
| Twilio | ~$15.50 trial credit | On upgrade |

When Hunter quota runs low, the system falls back to Apollo enrichment.
Companies with no email are logged in Notion as `no_email` — check Apollo manually.

---

## Files Reference

```
main.py             — orchestrator (--discover / --send / --dry / --digest)
job_scraper.py      — scrapes LinkedIn/Indeed + finds emails via Hunter.io
scorer.py           — scores company fit 1-5 against your profile
connections.py      — loads LinkedIn connections CSV (warm vs cold)
outreach.py         — sends Gmail with tailored PDF attached
notion_tracker.py   — logs contacts + updates statuses in Notion
tracker.py          — checks Gmail for replies and bounces
digest.py           — builds + sends WhatsApp daily summary
config.py           — loads API keys from .env
templates/          — cold_email.txt and warm_email.txt
data/               — LinkedIn connections CSV, sent log, today's plan, Gmail token
outputs/            — tailored resume PDFs (generated by /job-matching in Claude)
logs/               — daily run logs
HOW_TO_RUN.md       — this file
```
