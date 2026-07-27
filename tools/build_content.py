#!/usr/bin/env python3
"""Build content/ into apps/web/public/content as JSON for the Angular SPA."""

from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

import frontmatter

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
OUT = ROOT / "apps" / "web" / "public" / "content"


def json_default(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(type(obj))


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, default=json_default) + "\n",
        encoding="utf-8",
    )


def copy_json_tree(src_rel: str) -> None:
    src = CONTENT / src_rel
    dst = OUT / src_rel
    if src.is_file():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    elif src.is_dir():
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)


def build_news() -> list[dict]:
    items: list[dict] = []
    news_out = OUT / "news"
    if news_out.exists():
        shutil.rmtree(news_out)
    news_out.mkdir(parents=True)

    for path in sorted((CONTENT / "news").glob("*.md")):
        post = frontmatter.load(path)
        meta = dict(post.metadata)
        # Normalize datetime to iso string
        pub = meta.get("publishedAt")
        if hasattr(pub, "isoformat"):
            meta["publishedAt"] = pub.isoformat()
        elif isinstance(pub, str):
            meta["publishedAt"] = pub

        article = {
            **meta,
            "body": (post.content or "").strip(),
        }
        write_json(news_out / f"{meta['slug']}.json", article)
        items.append({k: v for k, v in article.items() if k != "body"})

    items.sort(key=lambda x: x.get("publishedAt", ""), reverse=True)
    write_json(OUT / "news.json", items)
    validated = [i for i in items if i.get("status") == "validated"]
    write_json(OUT / "news.validated.json", validated)
    return items


def main() -> int:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    shutil.copy2(CONTENT / "site.json", OUT / "site.json")
    copy_json_tree("standings")
    copy_json_tree("fixtures")
    copy_json_tree("objectives")
    build_news()

    # Admin CMS config lives under public/admin (copied separately by npm script)
    print(f"Built content -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
