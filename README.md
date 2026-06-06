# SF Bay Area DS/ML Job Tracker

Automated tracker that scrapes live Data Science, ML, and AI job openings across 500 SF Bay Area companies, scores them against a resume profile, and outputs a formatted Excel workbook.

Built by Karan Chandra · Assisted by Claude (Anthropic) · [See DISCLAIMER.md](DISCLAIMER.md)

---

## What It Does

- Queries the **Greenhouse** and **Lever** public APIs for 500 Bay Area companies
- Filters for DS/ML/AI/Applied Scientist roles
- Scores each job against a resume profile (skills, seniority, domain alignment)
- Outputs `Job_Search_Tracker.xlsx` with 4 sheets:
  - **Summary** — total counts and key stats
  - **Companies** — enriched metadata (TC estimates, H1B probability, GenAI/AV scores, LinkedIn recruiter search links)
  - **Job Openings** — live matched openings with apply links and match scores
  - **How to Use** — reference guide
- Tracks state between runs to show new vs. filled jobs
- Sends an optional email notification after each run

---

## Quickstart

### 1. Clone and install

```bash
git clone https://github.com/<your-username>/sf-job-tracker.git
cd sf-job-tracker
pip install -r requirements.txt
```

### 2. Run

```bash
python3 main.py           # full run — all 500 companies (~5–10 min)
python3 main.py --sample  # sample run — first 10 companies (for testing)
```

The output file is written to `../Job_Search_Tracker.xlsx` (one level above the repo).

### 3. Email notifications (optional)

Email is sent via Gmail after each run. To enable:

```bash
cp .env.example .env
# Edit .env and set GMAIL_APP_PASSWORD
export GMAIL_APP_PASSWORD="your_app_password"
python3 main.py
```

Generate a Gmail App Password at: https://myaccount.google.com/apppasswords  
(Requires 2FA to be enabled.)

---

## Schedule as a daily cron job (macOS)

To auto-run every day at 8 AM, add to your crontab (`crontab -e`):

```
0 8 * * * cd /path/to/sf-job-tracker && /usr/bin/python3 main.py >> /tmp/job_tracker.log 2>&1
```

---

## Customizing for Your Own Search

This tracker is pre-configured for Karan's profile. To adapt it for yourself:

### `config.py` — Target profile

```python
NOTIFICATION_EMAIL = "you@example.com"   # where to send update emails
SENDER_EMAIL = "you@gmail.com"           # Gmail account to send from
TARGET_TC_LOW = 200000                   # minimum TC target
TARGET_TC_HIGH = 300000                  # maximum TC target
NEEDS_H1B = True                         # set False if you don't need sponsorship
MATCH_THRESHOLD = 0.80                   # 0–1, jobs below this are filtered out
```

### `matcher.py` — Resume scoring

The scoring model has four components (100 pts total):
- **Title match** (30 pts) — role keywords in job title
- **Level match** (10 pts) — Senior / Staff / Lead
- **Core skills** (30 pts) — Python, SQL, ML frameworks, cloud, etc.
- **Domain bonus** (20 pts) — your strongest domain alignments

Update `SENIOR_ROLE_PATTERNS`, `CORE_SKILL_CHECKS`, and `DOMAIN_CHECKS` to reflect your own resume and target roles.

### `companies.py` — Target companies

The list of 500 companies is stored in `get_all_companies()`. Each company is defined with the `_co()` helper:

```python
_co(
    name="Company Name",
    tier="Growth",                  # Megacap / Large Cap / Mid Cap / Growth / Small Cap
    hq="San Francisco, CA",
    careers_url="https://company.com/careers",
    ats="greenhouse",               # greenhouse | lever | workday | custom
    gh="greenhouse-board-token",    # Greenhouse board token (if ats=greenhouse)
    lv="lever-company-id",          # Lever company ID (if ats=lever)
    h1b=85,                         # H1B sponsorship probability (0–100)
    tc=(180000, 260000, 350000),    # (DS, Senior DS, Staff DS) TC estimates
    genai=8,                        # GenAI relevance score (1–10)
    stage="Series C",               # funding stage
)
```

To find a company's Greenhouse token, check:  
`https://boards.greenhouse.io/{token}` — if it loads their job board, the token is correct.

For Lever, check:  
`https://jobs.lever.co/{company-id}`

---

## Project Structure

```
sf-job-tracker/
├── main.py           # Orchestrator — run this
├── companies.py      # 500-company master list
├── scraper.py        # Greenhouse + Lever API clients
├── matcher.py        # Resume-to-job scoring model
├── excel_builder.py  # Excel workbook builder (openpyxl)
├── emailer.py        # Email notification sender
├── config.py         # Target profile, thresholds, credentials
├── requirements.txt
├── .env.example      # Template for GMAIL_APP_PASSWORD
├── .gitignore
├── DISCLAIMER.md
└── README.md
```

---

## ATS Coverage (500 companies)

| ATS        | Companies |
|------------|-----------|
| Greenhouse | ~370      |
| Workday    | ~64       |
| Custom     | ~53       |
| Lever      | ~10       |
| Other      | ~3        |

Greenhouse and Lever companies are scraped automatically. Workday and custom ATS companies appear in the Excel with a link to their careers page for manual review.

---

## Limitations

- Only Greenhouse and Lever companies are auto-scraped. Workday/custom ATS requires manual checking.
- Bay Area location filtering is heuristic — some remote-first companies may not appear.
- TC estimates are sourced from public data (Levels.fyi, LinkedIn, Glassdoor) and may be outdated.
- H1B probability scores are estimates based on public USCIS data and company filings.

---

## License

This project is for personal/educational use. See [DISCLAIMER.md](DISCLAIMER.md).
