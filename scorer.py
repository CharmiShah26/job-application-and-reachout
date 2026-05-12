"""
Alignment scorer for Charmi's PM job search.
Scores each company/job 1-5 based on her profile and target criteria.
Only contacts scoring >= 4 get outreach emails.
"""

# Companies Charmi specifically loves — instant 5/5
DREAM_COMPANIES = {
    "clay", "airbnb", "whoop", "robinhood", "expedia", "figma", "notion",
    "linear", "ramp", "brex", "stripe", "loom", "airtable", "vercel",
    "superhuman", "coda", "glean", "perplexity", "rippling", "deel",
    # Dubai / MENA
    "tabby", "tamara", "careem", "noon", "kitopi", "anghami", "sarwa", "yap",
}

# Skip — too big, wrong culture, or pure engineering shops
SKIP_COMPANIES = {
    "apple", "google", "meta", "amazon", "microsoft", "ibm", "accenture",
    "deloitte", "cognizant", "tcs", "infosys", "wipro", "capgemini",
    "lockheed", "boeing", "raytheon", "halliburton",
}

# Strong signals for high score
POSITIVE_SIGNALS = [
    # Role signals
    "product manager", "associate product manager", "apm", "technical product manager",
    "tpm", "head of product", "vp product", "director of product",
    # Culture signals
    "yc", "y combinator", "series a", "series b", "series c",
    "consumer", "developer tools", "dev tools", "api", "platform",
    "ai", "ml", "machine learning", "fintech", "edtech", "saas",
    "startup", "seed", "growth",
    # Location signals
    "san francisco", "sf", "bay area", "remote", "dubai", "uae",
]

NEGATIVE_SIGNALS = [
    "enterprise only", "government", "defense", "oil", "mining",
    "manufacturing", "logistics only", "non-tech", "staffing",
    "legal", "insurance only",
]


def score_job(job: dict) -> int:
    """
    Score a job 1-5 based on alignment with Charmi's profile.
    5 = perfect fit, 1 = skip.
    """
    company = (job.get("company") or "").lower()
    title = (job.get("job_title_posted") or job.get("title") or "").lower()
    location = (job.get("location") or "").lower()
    description = (job.get("description") or "").lower()

    # Auto-skip
    if company in SKIP_COMPANIES:
        return 1

    # Dream company — instant 5
    if any(dream in company for dream in DREAM_COMPANIES):
        return 5

    # Negative signals — cap at 2
    if any(neg in description or neg in company for neg in NEGATIVE_SIGNALS):
        return 2

    score = 2  # baseline

    # Role match
    pm_titles = ["product manager", "apm", "tpm", "head of product", "vp product"]
    if any(t in title for t in pm_titles):
        score += 1

    # Location match
    good_locations = ["san francisco", "sf", "bay area", "remote", "dubai", "uae", "new york"]
    if any(loc in location for loc in good_locations):
        score += 0.5

    # Positive signals in description or company name
    signal_hits = sum(1 for s in POSITIVE_SIGNALS if s in description or s in company)
    if signal_hits >= 4:
        score += 1
    elif signal_hits >= 2:
        score += 0.5

    # Technical PM signals (AWS background is a plus)
    tech_signals = ["api", "platform", "infrastructure", "developer", "technical pm", "tpm", "engineer"]
    if sum(1 for t in tech_signals if t in description) >= 2:
        score += 0.5

    return min(5, round(score))


def filter_by_alignment(contacts: list, min_score: int = 4) -> list:
    """Filter contacts — only keep those at companies scoring >= min_score."""
    scored = []
    skipped = 0

    for contact in contacts:
        s = score_job(contact)
        contact["alignment_score"] = s
        if s >= min_score:
            scored.append(contact)
        else:
            skipped += 1

    print(f"  Alignment filter: {len(scored)} pass (score >= {min_score}), {skipped} skipped")
    return scored


if __name__ == "__main__":
    # Quick test
    test_jobs = [
        {"company": "Figma", "job_title_posted": "Product Manager", "location": "San Francisco, CA", "description": "consumer product saas startup"},
        {"company": "Boeing", "job_title_posted": "PM", "location": "Seattle", "description": "defense manufacturing"},
        {"company": "Stripe", "job_title_posted": "Technical PM", "location": "Remote", "description": "api platform developer tools series"},
        {"company": "Yelp", "job_title_posted": "Associate Product Manager", "location": "San Francisco, CA", "description": "consumer app growth saas"},
    ]
    for j in test_jobs:
        print(f"  {j['company']}: {score_job(j)}/5")
