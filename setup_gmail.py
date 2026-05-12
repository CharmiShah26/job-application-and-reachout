"""
Run this once to authorize Gmail.
You need to download OAuth credentials from Google Cloud Console first.

Steps:
1. Go to console.cloud.google.com
2. Create a project → Enable Gmail API
3. Credentials → Create OAuth 2.0 Client ID (Desktop app)
4. Download JSON → save as data/gmail_credentials.json
5. Run: python setup_gmail.py
"""
from outreach import get_gmail_service

print("Opening browser for Gmail authorization...")
service = get_gmail_service()
profile = service.users().getProfile(userId="me").execute()
print(f"Connected as: {profile['emailAddress']}")
print("Gmail is ready.")
