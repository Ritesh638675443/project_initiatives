"""SQLite persistence for the SIGMA submission portal."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(__import__("os").environ.get("SIGMA_DB_PATH", str(BASE_DIR / "data" / "sigma.db")))


class DuplicateSubmissionError(Exception):
    """Raised when a team/domain combination has already submitted."""


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db() -> None:
    """Create the database schema if it does not exist yet."""

    with _connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS submissions (
                submission_id TEXT PRIMARY KEY,
                domain TEXT NOT NULL,
                team_name TEXT NOT NULL,
                project_title TEXT NOT NULL,
                abstract TEXT NOT NULL DEFAULT '',
                guide TEXT NOT NULL,
                tags TEXT NOT NULL DEFAULT '[]',
                pdf_filename TEXT NOT NULL,
                pdf_path TEXT NOT NULL,
                submission_date TEXT NOT NULL,
                submission_time TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS team_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                submission_id TEXT NOT NULL,
                member_number INTEGER NOT NULL,
                name TEXT NOT NULL,
                register_number TEXT NOT NULL,
                year TEXT NOT NULL,
                tag TEXT NOT NULL,
                FOREIGN KEY (submission_id) REFERENCES submissions(submission_id)
                    ON DELETE CASCADE,
                UNIQUE (submission_id, member_number)
            );

            CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_team_domain
                ON submissions (LOWER(domain), LOWER(team_name));
            CREATE INDEX IF NOT EXISTS idx_submission_date
                ON submissions (submission_date);
            """
        )


def _next_submission_id(connection: sqlite3.Connection, year: int) -> str:
    prefix = f"SIGMA-{year}-"
    row = connection.execute(
        """
        SELECT COALESCE(MAX(CAST(SUBSTR(submission_id, ?) AS INTEGER)), 0) + 1 AS next_number
        FROM submissions
        WHERE submission_id LIKE ?
        """,
        (len(prefix) + 1, f"{prefix}%"),
    ).fetchone()
    return f"{prefix}{int(row['next_number']):04d}"


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
    """Create a submission and its members atomically."""

    submitted_at = submitted_at or datetime.now()
    with _connect() as connection:
        connection.execute("BEGIN IMMEDIATE")
        duplicate = connection.execute(
            """
            SELECT submission_id FROM submissions
            WHERE LOWER(domain) = LOWER(?) AND LOWER(team_name) = LOWER(?)
            """,
            (domain.strip(), team_name.strip()),
        ).fetchone()
        if duplicate:
            raise DuplicateSubmissionError(duplicate["submission_id"])

        submission_id = _next_submission_id(connection, submitted_at.year)
        connection.execute(
            """
            INSERT INTO submissions (
                submission_id, domain, team_name, project_title, abstract, guide,
                tags, pdf_filename, pdf_path, submission_date, submission_time, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                submission_id,
                domain.strip(),
                team_name.strip(),
                project_title.strip(),
                abstract.strip(),
                guide.strip(),
                json.dumps(tags),
                pdf_filename,
                pdf_path,
                submitted_at.strftime("%Y-%m-%d"),
                submitted_at.strftime("%H:%M:%S"),
                submitted_at.isoformat(timespec="seconds"),
            ),
        )
        connection.executemany(
            """
            INSERT INTO team_members (
                submission_id, member_number, name, register_number, year, tag
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    submission_id,
                    number,
                    member["name"].strip(),
                    member["register_number"].strip(),
                    member["year"],
                    member["tag"],
                )
                for number, member in enumerate(members, start=1)
            ],
        )
        return submission_id


def update_pdf_path(submission_id: str, pdf_path: str) -> None:
    with _connect() as connection:
        connection.execute(
            "UPDATE submissions SET pdf_path = ? WHERE submission_id = ?",
            (pdf_path, submission_id),
        )


def delete_submission(submission_id: str) -> None:
    with _connect() as connection:
        connection.execute("DELETE FROM submissions WHERE submission_id = ?", (submission_id,))


def _row_to_submission(row: sqlite3.Row) -> dict[str, Any]:
    submission = dict(row)
    try:
        submission["tags"] = json.loads(submission.get("tags") or "[]")
    except json.JSONDecodeError:
        submission["tags"] = []
    submission["years"] = [
        item for item in (submission.get("years") or "").split(",") if item
    ]
    submission["member_tags"] = [
        item for item in (submission.get("member_tags") or "").split(",") if item
    ]
    return submission


def list_submissions() -> list[dict[str, Any]]:
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT
                s.*,
                COUNT(tm.id) AS member_count,
                COALESCE(GROUP_CONCAT(DISTINCT tm.year), '') AS years,
                COALESCE(GROUP_CONCAT(DISTINCT tm.tag), '') AS member_tags
            FROM submissions s
            LEFT JOIN team_members tm ON tm.submission_id = s.submission_id
            GROUP BY s.submission_id
            ORDER BY s.created_at DESC
            """
        ).fetchall()
    return [_row_to_submission(row) for row in rows]


def get_submission(submission_id: str) -> dict[str, Any] | None:
    with _connect() as connection:
        row = connection.execute(
            """
            SELECT
                s.*,
                COUNT(tm.id) AS member_count,
                COALESCE(GROUP_CONCAT(DISTINCT tm.year), '') AS years,
                COALESCE(GROUP_CONCAT(DISTINCT tm.tag), '') AS member_tags
            FROM submissions s
            LEFT JOIN team_members tm ON tm.submission_id = s.submission_id
            WHERE s.submission_id = ?
            GROUP BY s.submission_id
            """,
            (submission_id,),
        ).fetchone()
        if row is None:
            return None
        submission = _row_to_submission(row)
        members = connection.execute(
            """
            SELECT member_number, name, register_number, year, tag
            FROM team_members
            WHERE submission_id = ?
            ORDER BY member_number
            """,
            (submission_id,),
        ).fetchall()
    submission["members"] = [dict(member) for member in members]
    return submission


def count_submissions() -> int:
    with _connect() as connection:
        return int(connection.execute("SELECT COUNT(*) FROM submissions").fetchone()[0])