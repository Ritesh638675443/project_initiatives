"""Supabase Storage abstraction for uploaded abstracts."""

from __future__ import annotations

import io

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
    SUPABASE_KEY,
)


# ============================================================
# STORAGE INITIALIZATION
# ============================================================

def ensure_storage() -> None:
    """
    The bucket must be created manually in the
    Supabase Dashboard.
    """
    return None


# ============================================================
# TEMP PDF
# ============================================================

def save_temp_pdf(pdf_bytes: bytes) -> io.BytesIO:
    """
    Keep the uploaded PDF in memory temporarily.
    """
    return io.BytesIO(pdf_bytes)


# ============================================================
# UPLOAD PDF
# ============================================================

def finalize_pdf(
    temp_path,
    submission_id: str,
    domain: str,
    team_name: str,
    project_title: str,
) -> str:

    # Supabase Storage path
    file_path = f"{submission_id}/abstract.pdf"

    # Get PDF bytes
    if hasattr(temp_path, "getvalue"):
        pdf_bytes = temp_path.getvalue()
    else:
        pdf_bytes = temp_path.read_bytes()

    if not pdf_bytes:
        raise ValueError("PDF file is empty.")

    # Upload to Supabase Storage
    response = (
        supabase.storage
        .from_(BUCKET_NAME)
        .upload(
            path=file_path,
            file=pdf_bytes,
            file_options={
                "content-type": "application/pdf",
                "upsert": "false",
            },
        )
    )

    return file_path


# ============================================================
# DOWNLOAD PDF
# ============================================================

def read_pdf(path: str) -> bytes:

    if not path:
        raise FileNotFoundError(
            "PDF path is empty."
        )

    response = (
        supabase.storage
        .from_(BUCKET_NAME)
        .download(path)
    )

    if not response:
        raise FileNotFoundError(
            f"PDF not found in Supabase Storage: {path}"
        )

    return response


# ============================================================
# DELETE PDF
# ============================================================

def remove_file(path) -> None:

    if not path:
        return

    # Temporary BytesIO object
    if hasattr(path, "getvalue"):
        return

    # Supabase Storage path
    (
        supabase.storage
        .from_(BUCKET_NAME)
        .remove([str(path)])
    )


# ============================================================
# STORAGE STATUS
# ============================================================

def storage_status() -> dict[str, str]:

    return {
        "root": f"Supabase Storage / {BUCKET_NAME}",
        "incoming": "Supabase Storage",
    }
