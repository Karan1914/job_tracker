"""
Build and update the Excel workbook with company data and job openings.
"""

import os
from datetime import datetime
from openpyxl import Workbook, load_workbook
from openpyxl.styles import (
    PatternFill, Font, Alignment, Border, Side, numbers
)
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import ColorScaleRule, DataBarRule
from openpyxl.worksheet.table import Table, TableStyleInfo

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "Job_Search_Tracker.xlsx")

# Color palette
DARK_BLUE = "1F3864"
MID_BLUE = "2E75B6"
LIGHT_BLUE = "BDD7EE"
ACCENT_GREEN = "70AD47"
ACCENT_ORANGE = "ED7D31"
ACCENT_RED = "C00000"
WHITE = "FFFFFF"
LIGHT_GRAY = "F2F2F2"
YELLOW = "FFFF00"


def _header_fill(hex_color):
    return PatternFill("solid", fgColor=hex_color)


def _thin_border():
    thin = Side(style="thin", color="CCCCCC")
    return Border(left=thin, right=thin, top=thin, bottom=thin)


def _fmt_tc(value: int) -> str:
    if not value:
        return "N/A"
    return f"${value:,}"


def build_workbook(companies: list[dict], jobs_by_company: dict[str, list[dict]]) -> str:
    """
    Build or refresh the Excel workbook.
    Returns the output file path.
    """
    wb = Workbook()

    _build_summary_sheet(wb, companies, jobs_by_company)
    _build_company_sheet(wb, companies)
    _build_jobs_sheet(wb, jobs_by_company)
    _build_instructions_sheet(wb)

    # Remove default empty sheet
    if "Sheet" in wb.sheetnames:
        del wb["Sheet"]

    wb.save(OUTPUT_PATH)
    print(f"Workbook saved: {OUTPUT_PATH}")
    return OUTPUT_PATH


def _build_summary_sheet(wb, companies, jobs_by_company):
    ws = wb.create_sheet("Summary", 0)
    ws.sheet_view.showGridLines = False

    # Title
    ws.merge_cells("A1:H1")
    ws["A1"] = "SF Bay Area Job Search Tracker — Karan Chandra"
    ws["A1"].font = Font(bold=True, size=16, color=WHITE)
    ws["A1"].fill = _header_fill(DARK_BLUE)
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 30

    ws.merge_cells("A2:H2")
    ws["A2"] = f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    ws["A2"].font = Font(italic=True, color="666666")
    ws["A2"].alignment = Alignment(horizontal="center")

    # Stats
    total_companies = len(companies)
    total_jobs = sum(len(v) for v in jobs_by_company.values())
    h1b_strong = sum(1 for c in companies if c.get("h1b_probability", 0) >= 80)
    high_genai = sum(1 for c in companies if c.get("genai_score", 0) >= 8)

    stats = [
        ("Total Companies", total_companies),
        ("Total Matched Openings", total_jobs),
        ("Strong H1B Sponsors (≥80%)", h1b_strong),
        ("High GenAI Relevance", high_genai),
    ]

    ws.row_dimensions[4].height = 14
    for i, (label, value) in enumerate(stats):
        col = i * 2 + 1
        cell_label = ws.cell(row=5, column=col, value=label)
        cell_value = ws.cell(row=6, column=col, value=value)

        cell_label.font = Font(bold=True, size=10, color=WHITE)
        cell_label.fill = _header_fill(MID_BLUE)
        cell_label.alignment = Alignment(horizontal="center")

        cell_value.font = Font(bold=True, size=20)
        cell_value.alignment = Alignment(horizontal="center")

        ws.merge_cells(
            start_row=5, start_column=col, end_row=5, end_column=col + 1
        )
        ws.merge_cells(
            start_row=6, start_column=col, end_row=6, end_column=col + 1
        )
        ws.row_dimensions[6].height = 30

    # Column widths
    for col in range(1, 10):
        ws.column_dimensions[get_column_letter(col)].width = 18


def _build_company_sheet(wb, companies):
    ws = wb.create_sheet("Companies")
    ws.sheet_view.showGridLines = False
    ws.freeze_panes = "A2"

    headers = [
        "Rank", "Company", "Tier", "HQ", "Careers URL",
        "Open DS/ML Roles", "H1B Probability", "TC — DS",
        "TC — Senior DS", "TC — Staff DS",
        "Recruiter Search URL", "Main Competitors",
        "Interview Rounds", "Interview Focus",
        "Referral Priority (1-10)", "Work Mode",
        "GenAI Score (1-10)", "AV Score (1-10)",
        "Funding Stage", "Visa History", "Matched Roles",
        "Stock Ticker",
    ]

    # Header row
    for col_idx, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx, value=h)
        cell.font = Font(bold=True, color=WHITE, size=9)
        cell.fill = _header_fill(DARK_BLUE)
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
        cell.border = _thin_border()
    ws.row_dimensions[1].height = 35

    # Data rows — sort by H1B desc, then GenAI desc
    sorted_companies = sorted(
        companies,
        key=lambda c: (c.get("h1b_probability", 0) + c.get("genai_score", 0) * 5),
        reverse=True,
    )

    for rank, company in enumerate(sorted_companies, 1):
        row = rank + 1
        row_data = [
            rank,
            company["name"],
            company.get("tier", ""),
            company.get("hq", ""),
            company.get("careers_url", ""),
            ", ".join(company.get("match_roles", [])),
            f"{company.get('h1b_probability', 0)}%",
            _fmt_tc(company.get("tc_ds")),
            _fmt_tc(company.get("tc_senior_ds")),
            _fmt_tc(company.get("tc_staff_ds")),
            company.get("recruiter_linkedin_url", ""),
            ", ".join(company.get("competitors", [])),
            company.get("interview_rounds", ""),
            company.get("interview_focus", ""),
            company.get("referral_priority", ""),
            company.get("work_mode", ""),
            company.get("genai_score", ""),
            company.get("av_score", ""),
            company.get("funding_stage", ""),
            company.get("visa_history", ""),
            ", ".join(company.get("match_roles", [])),
            company.get("stock_ticker", ""),
        ]

        fill = _header_fill(LIGHT_GRAY) if rank % 2 == 0 else PatternFill()
        for col_idx, value in enumerate(row_data, 1):
            cell = ws.cell(row=row, column=col_idx, value=value)
            cell.alignment = Alignment(wrap_text=True, vertical="top")
            cell.border = _thin_border()
            cell.font = Font(size=9)
            if rank % 2 == 0:
                cell.fill = _header_fill("EBF3FB")

            # Hyperlinks for URL columns
            if col_idx == 5 and value:  # careers URL
                cell.hyperlink = value
                cell.font = Font(color="0563C1", underline="single", size=9)
            if col_idx == 11 and value:  # recruiter URL
                cell.hyperlink = value
                cell.font = Font(color="0563C1", underline="single", size=9)

            # Color-code H1B column
            if col_idx == 7:
                prob = company.get("h1b_probability", 0)
                if prob >= 90:
                    cell.fill = _header_fill("C6EFCE")
                    cell.font = Font(color="006100", bold=True, size=9)
                elif prob >= 75:
                    cell.fill = _header_fill("FFEB9C")
                    cell.font = Font(color="9C5700", size=9)
                else:
                    cell.fill = _header_fill("FFC7CE")
                    cell.font = Font(color="9C0006", size=9)

        ws.row_dimensions[row].height = 40

    # Column widths
    col_widths = [6, 22, 18, 20, 40, 28, 12, 14, 14, 14, 40, 30, 45, 40,
                  14, 18, 12, 12, 20, 35, 28, 12]
    for i, w in enumerate(col_widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w


def _build_jobs_sheet(wb, jobs_by_company):
    ws = wb.create_sheet("Job Openings")
    ws.sheet_view.showGridLines = False
    ws.freeze_panes = "A2"

    headers = [
        "Company", "Job Title", "Location", "Match Score",
        "Matched Skills", "Role Match", "Apply URL",
        "Posted Date", "Source", "Notes",
    ]

    for col_idx, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx, value=h)
        cell.font = Font(bold=True, color=WHITE, size=9)
        cell.fill = _header_fill(DARK_BLUE)
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
        cell.border = _thin_border()
    ws.row_dimensions[1].height = 30

    row = 2
    for company_name, jobs in sorted(jobs_by_company.items()):
        for job in jobs:
            row_data = [
                job.get("company", company_name),
                job.get("title", ""),
                job.get("location", ""),
                job.get("match_score", ""),
                job.get("matched_skills", ""),
                job.get("role_match", ""),
                job.get("url", ""),
                job.get("posted_date", ""),
                job.get("source", ""),
                "",  # Notes — user fills
            ]

            for col_idx, value in enumerate(row_data, 1):
                cell = ws.cell(row=row, column=col_idx, value=value)
                cell.alignment = Alignment(wrap_text=True, vertical="top")
                cell.border = _thin_border()
                cell.font = Font(size=9)
                if row % 2 == 0:
                    cell.fill = _header_fill("EBF3FB")

                # Hyperlink on Apply URL
                if col_idx == 7 and value and value.startswith("http"):
                    cell.hyperlink = value
                    cell.font = Font(color="0563C1", underline="single", size=9)

                # Color match score
                if col_idx == 4 and value and value != "N/A":
                    try:
                        pct = int(value.replace("%", ""))
                        if pct >= 90:
                            cell.fill = _header_fill("C6EFCE")
                            cell.font = Font(color="006100", bold=True, size=9)
                        elif pct >= 75:
                            cell.fill = _header_fill("FFEB9C")
                            cell.font = Font(color="9C5700", size=9)
                    except ValueError:
                        pass

            ws.row_dimensions[row].height = 35
            row += 1

    col_widths = [22, 42, 22, 12, 40, 12, 50, 14, 12, 25]
    for i, w in enumerate(col_widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w


def _build_instructions_sheet(wb):
    ws = wb.create_sheet("How to Use")
    ws.sheet_view.showGridLines = False

    instructions = [
        ("SF Bay Area Job Search Tracker — Instructions", True, 14, DARK_BLUE),
        ("", False, 10, None),
        ("SHEETS", True, 11, MID_BLUE),
        ("• Summary — High-level stats and counts", False, 10, None),
        ("• Companies — Enriched company metadata, TC estimates, H1B probability", False, 10, None),
        ("• Job Openings — Live matched openings scraped from career pages", False, 10, None),
        ("• How to Use — This page", False, 10, None),
        ("", False, 10, None),
        ("COLUMNS", True, 11, MID_BLUE),
        ("• H1B Probability: Green ≥90%, Yellow ≥75%, Red <75%", False, 10, None),
        ("• Match Score: % match between job description and Karan's resume skills", False, 10, None),
        ("• GenAI Score: 1-10 — how central generative AI is to the company's business", False, 10, None),
        ("• AV Score: 1-10 — autonomous vehicle / robotics relevance", False, 10, None),
        ("• Referral Priority: 1-10 — estimated ease of getting a referral", False, 10, None),
        ("• Recruiter Search URL: Click to open LinkedIn search for recruiters at that company", False, 10, None),
        ("", False, 10, None),
        ("AUTOMATION", True, 11, MID_BLUE),
        ("• This file is auto-updated every 24 hours via a macOS cron job", False, 10, None),
        ("• New openings are added, filled roles are removed", False, 10, None),
        ("• You receive an email notification at the configured NOTIFICATION_EMAIL after each update", False, 10, None),
        ("• Cron schedule: 8:00 AM daily", False, 10, None),
        ("", False, 10, None),
        ("TARGET PROFILE", True, 11, MID_BLUE),
        ("• Roles: Senior Data Scientist, ML Engineer, AI Engineer, Applied Scientist", False, 10, None),
        ("• TC Target: $250K–$350K", False, 10, None),
        ("• H1B sponsorship required: Yes", False, 10, None),
        ("• Match threshold: 75%+ skill overlap with resume", False, 10, None),
    ]

    for row_idx, (text, bold, size, bg) in enumerate(instructions, 1):
        cell = ws.cell(row=row_idx, column=1, value=text)
        cell.font = Font(bold=bold, size=size, color=WHITE if bg else "333333")
        if bg:
            cell.fill = _header_fill(bg)
        cell.alignment = Alignment(vertical="center", indent=1 if not bold else 0)
        ws.row_dimensions[row_idx].height = 18

    ws.column_dimensions["A"].width = 80
