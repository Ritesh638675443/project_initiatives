"""Supabase Storage abstraction for uploaded abstracts."""

from __future__ import annotations

import io
from typing import Any

import streamlit as st
from supabase import Client, create_client


# ============================================================
# SUPABASE STORAGE
# ============================================================

BUCKET_NAME = "sigma-abstracts"


SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


# ============================================================
# STORAGE INITIALIZATION
# ============================================================

def ensure_storage() -> None:
    """
    The Supabase Storage bucket is created
    from the Supabase dashboard.
    """
    pass


# ============================================================
# TEMP PDF
# ============================================================

def save_temp_pdf(
    pdf_bytes: bytes
) -> io.BytesIO:

    return io.BytesIO(
        pdf_bytes
    )


# ============================================================
# UPLOAD PDF TO SUPABASE
# ============================================================

def finalize_pdf(
    temp_path,
    submission_id: str,
    domain: str,
    team_name: str,
    project_title: str,
) -> str:

    # --------------------------------------------------------
    # Storage path
    # --------------------------------------------------------

    file_path = (
        f"{submission_id}/abstract.pdf"
    )

    # --------------------------------------------------------
    # Read PDF bytes
    # --------------------------------------------------------

    if hasattr(
        temp_path,
        "getvalue"
    ):

        pdf_bytes = temp_path.getvalue()

    else:

        pdf_bytes = temp_path.read_bytes()

    # --------------------------------------------------------
    # Upload
    # --------------------------------------------------------

    supabase.storage \
        .from_(BUCKET_NAME) \
        .upload(
            file_path,
            pdf_bytes,
            {
                "content-type":
                    "application/pdf",

                "upsert":
                    "false"
            }
        )

    return file_path


# ============================================================
# DOWNLOAD PDF
# ============================================================

def read_pdf(
    path: str
) -> bytes:

    if not path:
        raise FileNotFoundError(
            "PDF path is empty."
        )

    response = (
        supabase
        .storage
        .from_(BUCKET_NAME)
        .download(path)
    )

    return response


# ============================================================
# DELETE PDF
# ============================================================

def remove_file(path) -> None:

    if not path:
        return

    # Temporary local/in-memory PDF.
    # Nothing needs to be deleted from Supabase Storage.
    if hasattr(path, "getvalue"):
        return

    # Actual Supabase Storage path.
    (
        supabase
        .storage
        .from_(BUCKET_NAME)
        .remove([str(path)])
    )


# ============================================================
# STORAGE STATUS
# ============================================================

def storage_status() -> dict[str, str]:

    return {
        "root":
            f"Supabase Storage / {BUCKET_NAME}",

        "incoming":
            "Supabase Storage"
    }
