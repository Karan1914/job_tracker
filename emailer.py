"""Send email notification after workbook update."""

import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from config import NOTIFICATION_EMAIL, SENDER_EMAIL

# Gmail App Password — set via environment variable GMAIL_APP_PASSWORD
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")


def send_update_email(excel_path: str, stats: dict):
    """Send notification email with summary stats."""
    if not GMAIL_APP_PASSWORD:
        print("  [email] GMAIL_APP_PASSWORD not set — skipping email")
        return False

    subject = f"Job Search Tracker Updated — {datetime.now().strftime('%Y-%m-%d')}"

    html_body = f"""
    <html><body style="font-family: Arial, sans-serif; color: #333;">
    <h2 style="color: #1F3864;">Job Search Tracker Update</h2>
    <p>Your SF Bay Area DS/ML job tracker has been refreshed.</p>

    <table style="border-collapse: collapse; width: 400px;">
      <tr style="background: #2E75B6; color: white;">
        <th style="padding: 8px; text-align: left;">Metric</th>
        <th style="padding: 8px; text-align: right;">Count</th>
      </tr>
      <tr style="background: #EBF3FB;">
        <td style="padding: 8px;">Companies tracked</td>
        <td style="padding: 8px; text-align: right;">{stats.get('companies', 0)}</td>
      </tr>
      <tr>
        <td style="padding: 8px;">Matched openings</td>
        <td style="padding: 8px; text-align: right;">{stats.get('total_jobs', 0)}</td>
      </tr>
      <tr style="background: #EBF3FB;">
        <td style="padding: 8px;">New since last update</td>
        <td style="padding: 8px; text-align: right;">{stats.get('new_jobs', 0)}</td>
      </tr>
      <tr>
        <td style="padding: 8px;">Removed (filled)</td>
        <td style="padding: 8px; text-align: right;">{stats.get('removed_jobs', 0)}</td>
      </tr>
    </table>

    <p style="margin-top: 20px;">
      The updated Excel file has been uploaded to your Google Drive in the
      <strong>Job Search</strong> folder.
    </p>

    <p style="color: #888; font-size: 12px;">
      This is an automated message from your job tracker. Next update in ~24 hours.
    </p>
    </body></html>
    """

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = NOTIFICATION_EMAIL

        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, GMAIL_APP_PASSWORD)
            server.sendmail(SENDER_EMAIL, NOTIFICATION_EMAIL, msg.as_string())

        print(f"  [email] Sent to {NOTIFICATION_EMAIL}")
        return True

    except Exception as e:
        print(f"  [email] Failed: {e}")
        return False
