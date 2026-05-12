from dotenv import load_dotenv
import os

load_dotenv()

APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")
HUNTER_API_KEY = os.getenv("HUNTER_API_KEY", "")
GMAIL_SENDER = os.getenv("GMAIL_SENDER")
GMAIL_CREDENTIALS_FILE = os.getenv("GMAIL_CREDENTIALS_FILE", "data/gmail_credentials.json")
GMAIL_TOKEN_FILE = os.getenv("GMAIL_TOKEN_FILE", "data/gmail_token.json")

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
YOUR_WHATSAPP_NUMBER = os.getenv("YOUR_WHATSAPP_NUMBER")

TARGET_LOCATIONS = os.getenv("TARGET_LOCATIONS", "San Francisco,United States,Dubai").split(",")
TARGET_FUNDING_STAGES = os.getenv("TARGET_FUNDING_STAGES", "Series A,Series B,Series C").split(",")
RESULTS_PER_RUN = int(os.getenv("RESULTS_PER_RUN", 50))

HIRING_TITLES = [
    "Head of Product",
    "VP of Product",
    "Chief Product Officer",
    "Director of Product",
    "Hiring Manager",
    "Recruiter",
    "Talent Acquisition",
    "Technical Recruiter",
    "Product Recruiter",
    "Head of Talent",
    "People Operations",
]
