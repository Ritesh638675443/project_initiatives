"""Shared constants, validation, export, and formatting helpers."""

from __future__ import annotations

import io
import re
import zipfile
from datetime import datetime
from typing import Any

import pandas as pd
import streamlit as st


DOMAINS = [
    "IE-Awards",
    "Logistics",
    "Alumni Relations",
    "Projects and Initiatives",
    "Design",
    "Events Management",
    "Content and Documentation",
    "Cultural Heads",
    "Hospitality",
    "Human Resources",
    "Sustainable Development Goals",
    "Editor's in Chief",
    "External Relations",
    "5-S",
    "Career Development Wing",
    "Social Media Management and Marketing",
    "Operations Excellence",
]

TAGS = [
    "Grey",
    "Red",
    "Brown",
]

YEARS = ["1st Year", "2nd Year", "3rd Year", "4th Year"]
MAX_PDF_SIZE = 10 * 1024 * 1024


def safe_filename(value: str, fallback: str = "file") -> str:
    """Return a portable filename component with no path traversal."""

    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", (value or "").strip())
    cleaned = cleaned.strip("._-")
    return (cleaned or fallback)[:120]


def validate_pdf(filename: str, pdf_bytes: bytes) -> str | None:
    if not filename.lower().endswith(".pdf"):
        return "Only PDF files are accepted."
    if len(pdf_bytes) == 0:
        return "The uploaded file is empty."
    if len(pdf_bytes) > MAX_PDF_SIZE:
        return f"The PDF must be {MAX_PDF_SIZE // (1024 * 1024)} MB or smaller."
    if not pdf_bytes.startswith(b"%PDF-"):
        return "The uploaded file does not appear to be a valid PDF."
    return None


def get_admin_credentials() -> tuple[str, str]:
    """Read admin credentials from Streamlit secrets with a local fallback."""

    try:
        admin = st.secrets.get("admin", {})
        if admin:
            username = str(admin.get("username", "admin")).strip() or "admin"
            password = str(admin.get("password", "admin123"))
            return username, password
    except Exception:
        pass
    return "admin", "admin123"


def build_acknowledgement(submission: dict[str, Any]) -> bytes:
    timestamp = f"{submission['submission_date']} {submission['submission_time']}"
    lines = [
        "SIGMA – DOMAIN MINI PROJECT",
        "ABSTRACT SUBMISSION ACKNOWLEDGEMENT",
        "",
        "Department of Industrial Engineering",
        "Anna University, Chennai",
        "",
        f"Submission ID: {submission['submission_id']}",
        f"Team Name: {submission['team_name']}",
        f"Domain: {submission['domain']}",
        f"Project: {submission['project_title']}",
        f"Members: {submission['member_count']}",
        f"Submitted On: {timestamp}",
        "",
        "Keep this acknowledgement for your records.",
    ]
    return "\n".join(lines).encode("utf-8")


def submission_table_rows(submissions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "Submission ID": item["submission_id"],
            "Domain": item["domain"],
            "Team Name": item["team_name"],
            "Project Title": item["project_title"],
            "Team Leader Gmail": item["guide"],
            "Members": item["member_count"],
            "Submission Date": item["submission_date"],
            "Submission Time": item["submission_time"],
            "Status": "Submitted",
        }
        for item in submissions
    ]


def submissions_dataframe(submissions: list[dict[str, Any]]) -> pd.DataFrame:
    rows = [
        {
            "Submission ID": item["submission_id"],
            "Domain": item["domain"],
            "Team Name": item["team_name"],
            "Project Title": item["project_title"],
            "Abstract": item["abstract"],
            "Team Leader Gmail": item["guide"],
            "Submission Date": item["submission_date"],
            "Submission Time": item["submission_time"],
            "PDF Filename": item["pdf_filename"],
            "Number of Members": item["member_count"],
        }
        for item in submissions
    ]
    columns = [
        "Submission ID",
        "Domain",
        "Team Name",
        "Project Title",
        "Abstract",
        "Team Leader Gmail",
        "Submission Date",
        "Submission Time",
        "PDF Filename",
        "Number of Members",
    ]
    return pd.DataFrame(rows, columns=columns)


def submission_register_dataframe(submissions: list[dict[str, Any]]) -> pd.DataFrame:
    """A compact register that makes the submitting team obvious to admins."""

    rows = [
        {
            "Submission ID": item["submission_id"],
            "Team Name": item["team_name"],
            "Domain": item["domain"],
            "Project Title": item["project_title"],
            "Team Leader Gmail": item["guide"],
            "Number of Members": item["member_count"],
            "Submission Date": item["submission_date"],
            "Submission Time": item["submission_time"],
            "Status": "Submitted",
        }
        for item in submissions
    ]
    columns = [
        "Submission ID",
        "Team Name",
        "Domain",
        "Project Title",
        "Team Leader Gmail",
        "Number of Members",
        "Submission Date",
        "Submission Time",
        "Status",
    ]
    return pd.DataFrame(rows, columns=columns)


def members_dataframe(submissions: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for submission in submissions:
        for member in submission.get("members", []):
            rows.append(
                {
                    "Submission ID": submission["submission_id"],
                    "Team Name": submission["team_name"],
                    "Member Number": member["member_number"],
                    "Name": member["name"],
                    "Register Number": member["register_number"],
                    "Year": member["year"],
                    "TAG": member["tag"],
                }
            )
    columns = [
        "Submission ID",
        "Team Name",
        "Member Number",
        "Name",
        "Register Number",
        "Year",
        "TAG",
    ]
    return pd.DataFrame(rows, columns=columns)


def build_excel(submissions: list[dict[str, Any]]) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        submissions_dataframe(submissions).to_excel(
            writer, sheet_name="Submissions", index=False
        )
        members_dataframe(submissions).to_excel(
            writer, sheet_name="Team Members", index=False
        )
        submission_register_dataframe(submissions).to_excel(
            writer, sheet_name="Team Register", index=False
        )
    return output.getvalue()


def build_pdf_zip(submissions: list[dict[str, Any]], storage_reader) -> tuple[bytes, int]:
    output = io.BytesIO()
    added = 0
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for submission in submissions:
            try:
                pdf_bytes = storage_reader(submission["pdf_path"])
            except (FileNotFoundError, ValueError, OSError):
                continue
            domain = safe_filename(submission["domain"], fallback="domain")
            filename = (
                f"{safe_filename(submission['team_name'], fallback='team')}_"
                f"{safe_filename(submission['project_title'], fallback='project')}.pdf"
            )
            archive.writestr(f"SIGMA_Abstract_Submissions/{domain}/{filename}", pdf_bytes)
            added += 1
    return output.getvalue(), added


def display_timestamp(submission: dict[str, Any]) -> str:
    try:
        value = datetime.fromisoformat(submission["created_at"])
        return value.strftime("%d-%m-%Y %H:%M")
    except (KeyError, ValueError):
        return f"{submission.get('submission_date', '')} {submission.get('submission_time', '')}"
