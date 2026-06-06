"""
Job scraper — fetches live openings from company career pages.
Supports: Greenhouse API, Lever API, and fallback static data.
"""

import requests
import json
import re
import time
from datetime import datetime
from matcher import score_job, format_match_pct
from config import TARGET_ROLES, MATCH_THRESHOLD

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}

# Role keywords to search for in job titles
ROLE_KEYWORDS = [
    "data scientist", "machine learning", "ml engineer", "ai engineer",
    "applied scientist", "research scientist", "mlops", "data science",
    "artificial intelligence",
]


def title_is_relevant(title: str) -> bool:
    t = title.lower()
    return any(kw in t for kw in ROLE_KEYWORDS)


def scrape_greenhouse(board_token: str, company_name: str, careers_url: str) -> list[dict]:
    """Fetch jobs from Greenhouse public API."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        jobs = data.get("jobs", [])
    except Exception as e:
        print(f"  [greenhouse] {company_name}: {e}")
        return []

    results = []
    for job in jobs:
        title = job.get("title", "")
        if not title_is_relevant(title):
            continue

        job_id = job.get("id")
        job_url = job.get("absolute_url", f"https://boards.greenhouse.io/{board_token}/jobs/{job_id}")
        description = ""
        if job.get("content"):
            description = re.sub(r"<[^>]+>", " ", job["content"])  # strip HTML

        # Location filter — Bay Area
        location = job.get("location", {}).get("name", "")
        if location and not _is_bay_area(location):
            continue

        score_result = score_job(title, description)
        if not score_result["passes_threshold"]:
            continue

        results.append({
            "company": company_name,
            "title": title,
            "location": location or "San Francisco Bay Area, CA",
            "url": job_url,
            "posted_date": job.get("updated_at", "")[:10],
            "match_score": format_match_pct(score_result["overall_score"]),
            "matched_skills": ", ".join(score_result["skill_hits"][:8]),
            "role_match": "Yes" if score_result["role_match"] else "Partial",
            "source": "Greenhouse",
        })

    return results


def scrape_lever(company_id: str, company_name: str, careers_url: str) -> list[dict]:
    """Fetch jobs from Lever public postings API."""
    url = f"https://api.lever.co/v0/postings/{company_id}?mode=json"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        jobs = resp.json()
    except Exception as e:
        print(f"  [lever] {company_name}: {e}")
        return []

    results = []
    for job in jobs:
        title = job.get("text", "")
        if not title_is_relevant(title):
            continue

        # Location filter
        categories = job.get("categories", {})
        location = categories.get("location", "")
        if location and not _is_bay_area(location):
            continue

        job_url = job.get("hostedUrl", careers_url)
        description = ""
        lists = job.get("lists", [])
        for lst in lists:
            description += " " + lst.get("content", "")
        description += " " + job.get("descriptionBody", "")
        description = re.sub(r"<[^>]+>", " ", description)

        score_result = score_job(title, description)
        if not score_result["passes_threshold"]:
            continue

        results.append({
            "company": company_name,
            "title": title,
            "location": location or "San Francisco Bay Area, CA",
            "url": job_url,
            "posted_date": datetime.fromtimestamp(
                job.get("createdAt", 0) / 1000
            ).strftime("%Y-%m-%d") if job.get("createdAt") else "",
            "match_score": format_match_pct(score_result["overall_score"]),
            "matched_skills": ", ".join(score_result["skill_hits"][:8]),
            "role_match": "Yes" if score_result["role_match"] else "Partial",
            "source": "Lever",
        })

    return results


def scrape_company(company: dict) -> list[dict]:
    """Route to the right scraper based on ATS type."""
    name = company["name"]
    ats = company.get("ats", "")
    careers_url = company.get("careers_url", "")

    print(f"  Scraping {name} ({ats})...")
    time.sleep(0.5)  # polite delay

    if ats == "greenhouse" and company.get("greenhouse_id"):
        jobs = scrape_greenhouse(company["greenhouse_id"], name, careers_url)
    elif ats == "lever" and company.get("lever_id"):
        jobs = scrape_lever(company["lever_id"], name, careers_url)
    else:
        # For companies with custom ATS (Apple, Google, Meta, Workday-based),
        # return placeholder indicating manual check needed
        jobs = _fallback_placeholder(company)

    print(f"    Found {len(jobs)} matching openings")
    return jobs


def _fallback_placeholder(company: dict) -> list[dict]:
    """
    For companies with unsupported ATS (Workday, custom).
    Returns a single row with the career URL so the user can check manually.
    The 24h updater can be extended to support these.
    """
    return [{
        "company": company["name"],
        "title": f"[Visit careers page — {company['name']}]",
        "location": company.get("hq", ""),
        "url": company.get("careers_url", ""),
        "posted_date": datetime.now().strftime("%Y-%m-%d"),
        "match_score": "N/A",
        "matched_skills": "See career page",
        "role_match": "Manual check",
        "source": "Manual",
    }]


def _is_bay_area(location: str) -> bool:
    """Return True if location is US-based (Bay Area, US remote, or unspecified)."""
    if not location:
        return True  # assume yes if unspecified
    loc = location.lower()

    # Reject non-US locations first
    non_us = [
        "canada", "toronto", "vancouver", "montreal", "ottawa", "calgary", "british columbia",
        "united kingdom", " uk", "london", "manchester", "edinburgh",
        "india", "bangalore", "mumbai", "hyderabad", "pune", "bengaluru",
        "germany", "berlin", "munich", "frankfurt",
        "france", "paris",
        "australia", "sydney", "melbourne",
        "singapore", "dublin", "amsterdam", "stockholm", "zurich", "tel aviv",
    ]
    if any(kw in loc for kw in non_us):
        return False

    us_keywords = [
        "san francisco", "sf", "menlo park", "palo alto", "mountain view",
        "sunnyvale", "santa clara", "cupertino", "san jose", "redwood city",
        "burlingame", "san mateo", "foster city", "fremont", "oakland",
        "berkeley", "emeryville", "south san francisco", "milpitas",
        "bay area", "california", ", ca", " ca,", " ca ",
        "remote", "united states", "usa", "u.s.a", "u.s.",
        "new york", "seattle", "austin", "boston", "chicago", "los angeles",
    ]
    return any(kw in loc for kw in us_keywords)
