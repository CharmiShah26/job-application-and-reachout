import os
import base64
import pickle
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import Optional, Tuple
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from config import GMAIL_SENDER, GMAIL_CREDENTIALS_FILE, GMAIL_TOKEN_FILE

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
]

RESUME_OUTPUT_DIR = "outputs"


def get_gmail_service():
    creds = None
    if os.path.exists(GMAIL_TOKEN_FILE):
        with open(GMAIL_TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(GMAIL_CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(GMAIL_TOKEN_FILE, "wb") as f:
            pickle.dump(creds, f)

    return build("gmail", "v1", credentials=creds)


def find_resume_for(company: str) -> Optional[str]:
    """
    Look for a tailored resume PDF in the outputs/ folder.
    Naming convention: Charmi_Shah_[Company]_*.pdf
    Falls back to Charmi_Shah_General.pdf if no tailored version.
    """
    if not os.path.exists(RESUME_OUTPUT_DIR):
        return None

    company_clean = company.replace(" ", "_").replace(".", "").replace(",", "")
    for fname in os.listdir(RESUME_OUTPUT_DIR):
        if fname.endswith(".pdf") and company_clean.lower() in fname.lower():
            return os.path.join(RESUME_OUTPUT_DIR, fname)

    # Fallback: generic resume
    generic = os.path.join(RESUME_OUTPUT_DIR, "Charmi_Shah_General.pdf")
    return generic if os.path.exists(generic) else None


def load_template(is_warm: bool) -> str:
    path = "templates/warm_email.txt" if is_warm else "templates/cold_email.txt"
    with open(path) as f:
        return f.read()


def render_template(template: str, contact: dict) -> Tuple[str, str]:
    lines = template.strip().split("\n")
    subject_line = lines[0].replace("Subject: ", "").strip()
    body = "\n".join(lines[2:]).strip()
    subject = subject_line.format(**contact)
    body = body.format(**contact)
    return subject, body


def send_email(service, to_email: str, subject: str, body: str, resume_path: Optional[str] = None) -> str:
    message = MIMEMultipart("mixed")
    message["to"] = to_email
    message["from"] = GMAIL_SENDER
    message["subject"] = subject

    message.attach(MIMEText(body, "plain"))

    if resume_path and os.path.exists(resume_path):
        with open(resume_path, "rb") as f:
            pdf = MIMEApplication(f.read(), _subtype="pdf")
            pdf.add_header(
                "Content-Disposition",
                "attachment",
                filename=os.path.basename(resume_path),
            )
            message.attach(pdf)

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    sent = service.users().messages().send(userId="me", body={"raw": raw}).execute()
    return sent["id"]


def send_outreach(contact: dict, service=None, dry_run: bool = False) -> dict:
    if not contact.get("email"):
        contact["status"] = "no_email"
        return contact

    template = load_template(contact.get("is_warm", False))
    subject, body = render_template(template, contact)
    resume_path = find_resume_for(contact.get("company", ""))

    if dry_run:
        has_resume = f"+ resume: {os.path.basename(resume_path)}" if resume_path else "(no resume found)"
        print(f"  [DRY RUN] → {contact['email']} | {subject} {has_resume}")
        contact["status"] = "dry_run"
        contact["resume_attached"] = resume_path or ""
        return contact

    try:
        if service is None:
            service = get_gmail_service()
        msg_id = send_email(service, contact["email"], subject, body, resume_path)
        contact["status"] = "sent"
        contact["gmail_message_id"] = msg_id
        contact["resume_attached"] = resume_path or ""
        warm_label = "warm" if contact.get("is_warm") else "cold"
        resume_label = f" + {os.path.basename(resume_path)}" if resume_path else " (no resume)"
        print(f"  ✉️  {contact['name']} <{contact['email']}> ({warm_label}){resume_label}")
    except Exception as e:
        contact["status"] = "send_failed"
        contact["error"] = str(e)
        print(f"  ❌ Failed: {contact['email']}: {e}")

    return contact
