"""
Main orchestrator for the job tracker.
Usage:
  python3 main.py           — full run (all companies)
  python3 main.py --sample  — sample run (first 10 companies for testing)
"""

import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from companies import get_sample_companies, get_all_companies
from scraper import scrape_company
from excel_builder import build_workbook, OUTPUT_PATH
from emailer import send_update_email

STATE_FILE = os.path.join(os.path.dirname(__file__), "..", "job_tracker_state.json")


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"last_run": None, "known_jobs": {}}


def save_state(state: dict):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def run(sample_mode=False):
    print(f"\n{'='*60}")
    print(f"Job Tracker — {'SAMPLE' if sample_mode else 'FULL'} run")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    companies = get_sample_companies(10) if sample_mode else get_all_companies()
    print(f"Processing {len(companies)} companies...\n")

    state = load_state()
    previous_jobs = state.get("known_jobs", {})

    # Scrape jobs for each company
    jobs_by_company = {}
    for company in companies:
        jobs = scrape_company(company)
        if jobs:
            jobs_by_company[company["name"]] = jobs

    # Compute diff stats
    current_job_ids = set()
    for company_name, jobs in jobs_by_company.items():
        for job in jobs:
            current_job_ids.add(f"{company_name}::{job['title']}::{job.get('url','')}")

    previous_job_ids = set(previous_jobs.keys())
    new_jobs = current_job_ids - previous_job_ids
    removed_jobs = previous_job_ids - current_job_ids
    total_jobs = sum(len(v) for v in jobs_by_company.values())

    print(f"\n--- Results ---")
    print(f"Companies scraped: {len(companies)}")
    print(f"Companies with openings: {len(jobs_by_company)}")
    print(f"Total matched openings: {total_jobs}")
    print(f"New since last run: {len(new_jobs)}")
    print(f"Removed (filled): {len(removed_jobs)}")

    # Build Excel
    print(f"\nBuilding Excel workbook...")
    excel_path = build_workbook(companies, jobs_by_company)

    # Save state
    new_state = {
        "last_run": datetime.now().isoformat(),
        "known_jobs": {jid: True for jid in current_job_ids},
    }
    save_state(new_state)

    stats = {
        "companies": len(companies),
        "total_jobs": total_jobs,
        "new_jobs": len(new_jobs),
        "removed_jobs": len(removed_jobs),
    }

    print(f"\nDone. Output: {excel_path}")
    return excel_path, stats


if __name__ == "__main__":
    sample_mode = "--sample" in sys.argv
    excel_path, stats = run(sample_mode=sample_mode)
