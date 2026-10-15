"""Automated test to ensure Alembic migration integrity across the team.

This test prevents multiple heads, duplicate revision IDs, and broken migration
chains from ever being introduced into the repository or passing CI tests.
"""
import os
import re
from pathlib import Path
import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory


def test_alembic_single_head():
    """Verify that there is strictly one single head in the Alembic migration chain."""
    backend_dir = Path(__file__).resolve().parent.parent
    ini_path = backend_dir / "alembic.ini"
    assert ini_path.exists(), f"alembic.ini not found at {ini_path}"

    config = Config(str(ini_path))
    config.set_main_option("script_location", str(backend_dir / "alembic"))
    script = ScriptDirectory.from_config(config)

    heads = script.get_heads()
    assert len(heads) == 1, (
        f"Multiple Alembic migration heads detected: {heads}. "
        "A divergent migration branch was created. Rebase your migration "
        "onto the latest head or run 'alembic merge heads -m \"merge_heads\"' before committing."
    )


def test_alembic_no_duplicate_revision_ids():
    """Verify that every migration file defines a unique revision ID."""
    versions_dir = Path(__file__).resolve().parent.parent / "alembic" / "versions"
    assert versions_dir.exists(), f"Versions directory not found at {versions_dir}"

    revision_pattern = re.compile(r'^\s*revision\s*:\s*str\s*=\s*["\']([^"\']+)["\']', re.MULTILINE)
    seen_revisions = {}

    for file_path in versions_dir.glob("*.py"):
        content = file_path.read_text(encoding="utf-8")
        match = revision_pattern.search(content)
        if match:
            rev_id = match.group(1)
            assert rev_id not in seen_revisions, (
                f"Duplicate Alembic revision ID '{rev_id}' detected in: "
                f"'{file_path.name}' and '{seen_revisions[rev_id]}'. "
                "Ensure each migration uses a unique sequence or UUID."
            )
            seen_revisions[rev_id] = file_path.name
