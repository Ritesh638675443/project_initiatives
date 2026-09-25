"""Supabase database persistence for the SIGMA submission portal."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import streamlit as st
from supabase import Client, create_client


# ============================================================
# SUPABASE CONNECTION
# ============================================================

SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


# ============================================================
# DUPLICATE SUBMISSION ERROR
# ============================================================

class DuplicateSubmissionError(Exception):
    """Raised when a team/domain combination already exists."""


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_db() -> None:
    """
    Supabase tables are created from the Supabase dashboard.
    Therefore, nothing needs to be initialized here.
    """
    pass


# ============================================================
# GENERATE NEXT SUBMISSION ID
# ============================================================

def _next_submission_id(year: int) -> str:

    prefix = f"SIGMA-{year}-"

    response = (
        supabase
        .table("submissions")
        .select("submission_id")
        .like(
            "submission_id",
            f"{prefix}%"
        )
        .execute()
    )

    numbers = []

    for row in response.data:

        submission_id = row["submission_id"]

        try:

            number = int(
                submission_id.replace(
                    prefix,
                    ""
                )
            )

            numbers.append(number)

        except ValueError:
            continue

    next_number = max(
        numbers,
        default=0
    ) + 1

    return f"{prefix}{next_number:04d}"


# ============================================================
# CREATE SUBMISSION
# ============================================================

def create_submission(
    *,
    domain: str,
    team_name: str,
    project_title: str,
    abstract: str,
    guide: str,
    tags: list[str],
    pdf_filename: str,
    pdf_path: str,
    members: list[dict[str, str]],
    submitted_at: datetime | None = None,
) -> str:

    submitted_at = submitted_at or datetime.now()

    domain = domain.strip()
    team_name = team_name.strip()

    # --------------------------------------------------------
    # CHECK DUPLICATE TEAM + DOMAIN
    # --------------------------------------------------------

    duplicate_response = (
        supabase
        .table("submissions")
        .select("submission_id")
        .eq("domain", domain)
        .eq("team_name", team_name)
        .execute()
    )

    if duplicate_response.data:

        raise DuplicateSubmissionError(
            duplicate_response.data[0]["submission_id"]
        )

    # --------------------------------------------------------
    # GENERATE SUBMISSION ID
    # --------------------------------------------------------

    submission_id = _next_submission_id(
        submitted_at.year
    )

    # --------------------------------------------------------
    # INSERT MAIN SUBMISSION
    # --------------------------------------------------------

    submission_data = {

        "submission_id": submission_id,

        "domain": domain,

        "team_name": team_name,

        "project_title": project_title.strip(),

        "abstract": abstract.strip(),

        "guide": guide.strip(),

        "tags": tags,

        "pdf_filename": pdf_filename,

        "pdf_path": pdf_path,

        "submission_date":
            submitted_at.strftime("%Y-%m-%d"),

        "submission_time":
            submitted_at.strftime("%H:%M:%S"),

        "created_at":
            submitted_at.isoformat(
                timespec="seconds"
            ),
    }

    supabase \
        .table("submissions") \
        .insert(submission_data) \
        .execute()

    # --------------------------------------------------------
    # INSERT TEAM MEMBERS
    # --------------------------------------------------------

    member_rows = []

    for number, member in enumerate(
        members,
        start=1
    ):

        member_rows.append({

            "submission_id":
                submission_id,

            "member_number":
                number,

            "name":
                member["name"].strip(),

            "register_number":
                member["register_number"].strip(),

            "year":
                member["year"],

            "tag":
                member["tag"],
        })

    if member_rows:

        supabase \
            .table("team_members") \
            .insert(member_rows) \
            .execute()

    return submission_id


# ============================================================
# UPDATE PDF PATH
# ============================================================

def update_pdf_path(
    submission_id: str,
    pdf_path: str
) -> None:

    (
        supabase
        .table("submissions")
        .update({
            "pdf_path": pdf_path
        })
        .eq(
            "submission_id",
            submission_id
        )
        .execute()
    )


# ============================================================
# DELETE SUBMISSION
# ============================================================

def delete_submission(
    submission_id: str
) -> None:

    (
        supabase
        .table("submissions")
        .delete()
        .eq(
            "submission_id",
            submission_id
        )
        .execute()
    )


# ============================================================
# LIST SUBMISSIONS
# ============================================================

def list_submissions() -> list[dict[str, Any]]:

    response = (
        supabase
        .table("submissions")
        .select(
            "*, team_members(*)"
        )
        .order(
            "created_at",
            desc=True
        )
        .execute()
    )

    submissions = []

    for row in response.data:

        submission = dict(row)

        members = submission.pop(
            "team_members",
            []
        )

        submission["member_count"] = len(
            members
        )

        submission["years"] = list({
            member["year"]
            for member in members
        })

        submission["member_tags"] = list({
            member["tag"]
            for member in members
        })

        if not submission.get("tags"):
            submission["tags"] = []

        submissions.append(
            submission
        )

    return submissions


# ============================================================
# GET ONE SUBMISSION
# ============================================================

def get_submission(
    submission_id: str
) -> dict[str, Any] | None:

    response = (
        supabase
        .table("submissions")
        .select(
            "*, team_members(*)"
        )
        .eq(
            "submission_id",
            submission_id
        )
        .maybe_single()
        .execute()
    )

    if not response.data:
        return None

    submission = dict(
        response.data
    )

    members = submission.pop(
        "team_members",
        []
    )

    members.sort(
        key=lambda x:
        x["member_number"]
    )

    submission["members"] = members

    submission["member_count"] = len(
        members
    )

    submission["years"] = list({
        member["year"]
        for member in members
    })

    submission["member_tags"] = list({
        member["tag"]
        for member in members
    })

    if not submission.get("tags"):
        submission["tags"] = []

    return submission


# ============================================================
# COUNT SUBMISSIONS
# ============================================================

def count_submissions() -> int:

    response = (
        supabase
        .table("submissions")
        .select(
            "submission_id",
            count="exact"
        )
        .execute()
    )

    return response.count or 0
