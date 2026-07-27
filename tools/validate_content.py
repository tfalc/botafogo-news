#!/usr/bin/env python3
"""Validate content/ against Pydantic schemas. Exit 1 on failure."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import frontmatter

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from schemas import (  # noqa: E402
    FixturesFile,
    NewsFrontmatter,
    ObjectivesConfig,
    SiteConfig,
    StandingsFile,
)


def fail(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)


def validate_site() -> list[str]:
    errors: list[str] = []
    path = CONTENT / "site.json"
    try:
        SiteConfig.model_validate_json(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"site.json: {exc}")
    return errors


def validate_news() -> list[str]:
    errors: list[str] = []
    slugs: set[str] = set()
    news_dir = CONTENT / "news"
    for path in sorted(news_dir.glob("*.md")):
        try:
            post = frontmatter.load(path)
            meta = NewsFrontmatter.model_validate(post.metadata)
            if meta.slug in slugs:
                errors.append(f"{path.name}: duplicate slug '{meta.slug}'")
            slugs.add(meta.slug)
            if not (post.content or "").strip():
                errors.append(f"{path.name}: empty body")
        except Exception as exc:
            errors.append(f"{path.name}: {exc}")
    return errors


def validate_standings() -> list[str]:
    errors: list[str] = []
    for path in sorted((CONTENT / "standings").glob("*.json")):
        try:
            data = StandingsFile.model_validate_json(path.read_text(encoding="utf-8"))
            positions = [t.position for t in data.teams]
            if positions != sorted(positions):
                errors.append(f"{path.name}: teams not sorted by position")
        except Exception as exc:
            errors.append(f"{path.name}: {exc}")
    return errors


def validate_fixtures() -> list[str]:
    errors: list[str] = []
    for path in sorted((CONTENT / "fixtures").glob("*.json")):
        try:
            FixturesFile.model_validate_json(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"{path.name}: {exc}")
    return errors


def validate_objectives() -> list[str]:
    errors: list[str] = []
    path = CONTENT / "objectives" / "config.json"
    try:
        ObjectivesConfig.model_validate_json(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"objectives/config.json: {exc}")
    return errors


def main() -> int:
    if not CONTENT.is_dir():
        fail(f"missing content dir: {CONTENT}")
        return 1

    all_errors = (
        validate_site()
        + validate_news()
        + validate_standings()
        + validate_fixtures()
        + validate_objectives()
    )
    if all_errors:
        for err in all_errors:
            fail(err)
        print(f"Validation failed with {len(all_errors)} error(s).", file=sys.stderr)
        return 1

    print("Content validation OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
