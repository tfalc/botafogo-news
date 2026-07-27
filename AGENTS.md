# Agent guidance — Portal Fogão

## Stack split

| Area | Stack | Agent guidance |
|------|--------|----------------|
| Frontend | Angular under `apps/` | Follow existing Angular patterns in the repo |
| Content | Markdown/JSON under `content/` | Editorial rules in `content/EDITORIAL.md` |
| Tooling | Python under `tools/` | Python 3.12+ (uv/ruff/typing/pytest) |
| Branding / marcas | `docs/branding/` | Follow `docs/branding/USAGE-RIGHTS.md` — no official crests without license |
| CRM | `admin/` | Hub em `/admin/` — conteúdo (Decap) e tabelas em páginas separadas |

## Python

When working on `tools/`, `*.py`, `pyproject.toml`, `.python-version`, or Python deps:

1. Target **Python 3.12+** with modern tooling: **uv**, **ruff**, **pyproject.toml**, typing, **pytest**.
2. Prefer the project `.venv` (`npm run setup:python`).
3. Keep scripts idempotent and CLI-friendly; fail with clear errors.

Do not apply Python tooling conventions to Angular/frontend code.
