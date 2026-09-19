"""File storage abstraction for uploaded abstracts."""

from __future__ import annotations

import os
import shutil
import uuid
from pathlib import Path

from utils import safe_filename


BASE_DIR = Path(__file__).resolve().parent
STORAGE_ROOT = Path(
    os.environ.get("SIGMA_STORAGE_DIR", str(BASE_DIR / "data" / "submissions"))
).resolve()
INCOMING_ROOT = STORAGE_ROOT / ".incoming"


def ensure_storage() -> None:
    STORAGE_ROOT.mkdir(parents=True, exist_ok=True)
    INCOMING_ROOT.mkdir(parents=True, exist_ok=True)


def save_temp_pdf(pdf_bytes: bytes) -> Path:
    ensure_storage()
    path = INCOMING_ROOT / f"{uuid.uuid4().hex}.pdf"
    path.write_bytes(pdf_bytes)
    return path


def finalize_pdf(
    temp_path: Path,
    submission_id: str,
    domain: str,
    team_name: str,
    project_title: str,
) -> Path:
    ensure_storage()
    domain_dir = STORAGE_ROOT / safe_filename(domain, fallback="domain")
    domain_dir.mkdir(parents=True, exist_ok=True)
    filename = (
        f"{safe_filename(submission_id)}_"
        f"{safe_filename(team_name, fallback='team')}_"
        f"{safe_filename(project_title, fallback='abstract')}.pdf"
    )
    final_path = domain_dir / filename
    shutil.move(str(temp_path), str(final_path))
    return final_path


def remove_file(path: str | Path) -> None:
    candidate = Path(path)
    try:
        candidate.unlink(missing_ok=True)
    except OSError:
        pass


def read_pdf(path: str | Path) -> bytes:
    candidate = Path(path).resolve()
    root = STORAGE_ROOT.resolve()
    if os.path.commonpath([str(candidate), str(root)]) != str(root):
        raise ValueError("Requested file is outside the configured storage directory.")
    if not candidate.is_file():
        raise FileNotFoundError(candidate)
    return candidate.read_bytes()


def storage_status() -> dict[str, str]:
    ensure_storage()
    return {
        "root": str(STORAGE_ROOT),
        "incoming": str(INCOMING_ROOT),
    }