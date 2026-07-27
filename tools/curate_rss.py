#!/usr/bin/env python3
"""Fetch RSS feeds and create draft news markdown for human review."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import feedparser

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
NEWS = CONTENT / "news"
FEEDS_FILE = CONTENT / "rss_feeds.json"


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[àáâãäå]", "a", text)
    text = re.sub(r"[èéêë]", "e", text)
    text = re.sub(r"[ìíîï]", "i", text)
    text = re.sub(r"[òóôõö]", "o", text)
    text = re.sub(r"[ùúûü]", "u", text)
    text = re.sub(r"[ç]", "c", text)
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:80] or "noticia-rss"


def existing_slugs() -> set[str]:
    slugs: set[str] = set()
    for path in NEWS.glob("*.md"):
        # Prefer filename; also scan frontmatter slug if present
        slugs.add(path.stem)
        text = path.read_text(encoding="utf-8")
        m = re.search(r"^slug:\s*[\"']?([^\"'\n]+)", text, re.M)
        if m:
            slugs.add(m.group(1).strip())
    return slugs


def unique_slug(base: str, used: set[str]) -> str:
    slug = base
    i = 2
    while slug in used:
        slug = f"{base}-{i}"
        i += 1
    used.add(slug)
    return slug


def write_draft(slug: str, title: str, summary: str, link: str, tone: str, published: str) -> Path:
    body = (
        f"{summary.strip() or title}\n\n"
        f"_Rascunho importado via RSS. Reescreva no tom editorial Fogão "
        f"(ver `content/EDITORIAL.md`) e altere `status` para `validated`._\n\n"
        f"Fonte original: {link}\n"
    )
    # Escape quotes in YAML
    safe_title = title.replace('"', "'")
    safe_summary = (summary or title)[:200].replace('"', "'")
    content = f"""---
title: "{safe_title}"
slug: "{slug}"
publishedAt: "{published}"
status: draft
tags:
  - curadoria
  - rss
tone: {tone}
sources:
  - "{link}"
summary: "{safe_summary}"
---

{body}
"""
    path = NEWS / f"{slug}.md"
    path.write_text(content, encoding="utf-8")
    return path


def main() -> int:
    if not FEEDS_FILE.exists():
        print(f"Missing {FEEDS_FILE}", file=sys.stderr)
        return 1

    config = json.loads(FEEDS_FILE.read_text(encoding="utf-8"))
    max_items = int(config.get("maxItemsPerFeed", 5))
    used = existing_slugs()
    created = 0

    for feed in config.get("feeds", []):
        if not feed.get("enabled", True):
            continue
        url = feed["url"]
        tone = feed.get("tone", "fogao")
        print(f"Fetching {feed.get('name', url)} ...")
        parsed = feedparser.parse(url)
        if getattr(parsed, "bozo", False) and not parsed.entries:
            print(f"  WARN: failed to parse feed: {getattr(parsed, 'bozo_exception', '')}")
            continue

        for entry in parsed.entries[:max_items]:
            title = (entry.get("title") or "Sem título").strip()
            link = (entry.get("link") or "").strip()
            summary = re.sub(r"<[^>]+>", "", entry.get("summary", entry.get("description", ""))).strip()
            base = slugify(title)
            # Skip if similar slug or same source already exists
            if any(link and link in p.read_text(encoding="utf-8") for p in NEWS.glob("*.md")):
                print(f"  skip (source exists): {title[:60]}")
                continue
            slug = unique_slug(base, used)
            published = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
            path = write_draft(slug, title, summary, link, tone, published)
            print(f"  draft: {path.name}")
            created += 1

    print(f"Created {created} draft(s). Review before validating.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
