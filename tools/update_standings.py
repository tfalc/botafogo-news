#!/usr/bin/env python3
"""Fetch Brasileirão (and configured) standings from safe/configured providers."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
SOURCES_PATH = CONTENT / "config" / "standings_sources.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from schemas import StandingsFile  # noqa: E402


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def alias_name(name: str, aliases: dict[str, str]) -> str:
    if name in aliases:
        return aliases[name]
    # soft match: strip common suffixes
    for src, dst in aliases.items():
        if name.casefold() == src.casefold():
            return dst
    return name


def write_standings(path: Path, payload: dict[str, Any]) -> None:
    validated = StandingsFile.model_validate(payload)
    data = validated.model_dump(mode="json", exclude_none=True)
    for key in ("source", "sourceFetchedAt", "sourceNotes"):
        if key in payload:
            data[key] = payload[key]
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def fetch_espn(league_path: str) -> dict[str, Any]:
    url = f"https://site.api.espn.com/apis/v2/sports/soccer/{league_path}/standings"
    with httpx.Client(timeout=30.0, headers={"User-Agent": "PortalFogao/0.1 (editorial)"}) as client:
        resp = client.get(url)
        resp.raise_for_status()
        return resp.json()


def parse_espn(raw: dict[str, Any], *, competition_id: str, name: str, season: int, aliases: dict[str, str]) -> dict[str, Any]:
    children = raw.get("children") or []
    if not children:
        raise ValueError("ESPN: resposta sem standings")
    entries = children[0]["standings"]["entries"]
    teams: list[dict[str, Any]] = []
    for entry in entries:
        stats = {s["name"]: s.get("value", s.get("displayValue")) for s in entry.get("stats", [])}

        def num(key: str) -> int:
            val = stats.get(key, 0)
            return int(float(val))

        team_name = alias_name(entry["team"]["displayName"], aliases)
        played = num("gamesPlayed")
        won = num("wins")
        drawn = num("ties")
        lost = num("losses")
        gf = num("pointsFor")
        ga = num("pointsAgainst")
        teams.append(
            {
                "position": num("rank"),
                "name": team_name,
                "played": played,
                "won": won,
                "drawn": drawn,
                "lost": lost,
                "goalsFor": gf,
                "goalsAgainst": ga,
                "goalDifference": gf - ga,
                "points": num("points"),
            }
        )
    teams.sort(key=lambda t: t["position"])
    return {
        "id": competition_id,
        "name": name,
        "season": season,
        "updatedAt": now_iso(),
        "teams": teams,
        "source": "espn",
        "sourceFetchedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sourceNotes": f"ESPN site API ({raw.get('name', 'bra.1')})",
    }


def fetch_api_football(league_id: int, season: int, api_key: str) -> dict[str, Any]:
    url = "https://v3.football.api-sports.io/standings"
    headers = {"x-apisports-key": api_key}
    with httpx.Client(timeout=30.0, headers=headers) as client:
        resp = client.get(url, params={"league": league_id, "season": season})
        resp.raise_for_status()
        data = resp.json()
    errors = data.get("errors")
    if errors:
        raise ValueError(f"api-football errors: {errors}")
    return data


def parse_api_football(
    raw: dict[str, Any],
    *,
    competition_id: str,
    name: str,
    season: int,
    aliases: dict[str, str],
) -> dict[str, Any]:
    response = raw.get("response") or []
    if not response:
        raise ValueError("api-football: resposta vazia (cheque league/season e plano)")
    league = response[0]["league"]
    table = league["standings"][0]
    teams: list[dict[str, Any]] = []
    for row in table:
        team_name = alias_name(row["team"]["name"], aliases)
        teams.append(
            {
                "position": int(row["rank"]),
                "name": team_name,
                "played": int(row["all"]["played"]),
                "won": int(row["all"]["win"]),
                "drawn": int(row["all"]["draw"]),
                "lost": int(row["all"]["lose"]),
                "goalsFor": int(row["all"]["goals"]["for"]),
                "goalsAgainst": int(row["all"]["goals"]["against"]),
                "goalDifference": int(row["goalsDiff"]),
                "points": int(row["points"]),
            }
        )
    teams.sort(key=lambda t: t["position"])
    return {
        "id": competition_id,
        "name": name,
        "season": season,
        "updatedAt": now_iso(),
        "teams": teams,
        "source": "api-football",
        "sourceFetchedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sourceNotes": f"API-Football league={league.get('id')} season={league.get('season')}",
    }


def fetch_football_data(code: str, token: str) -> dict[str, Any]:
    url = f"https://api.football-data.org/v4/competitions/{code}/standings"
    headers = {"X-Auth-Token": token}
    with httpx.Client(timeout=30.0, headers=headers) as client:
        resp = client.get(url)
        resp.raise_for_status()
        return resp.json()


def parse_football_data(
    raw: dict[str, Any],
    *,
    competition_id: str,
    name: str,
    season: int,
    aliases: dict[str, str],
) -> dict[str, Any]:
    standings = raw.get("standings") or []
    total = next((s for s in standings if s.get("type") == "TOTAL"), None)
    if not total:
        raise ValueError("football-data: tabela TOTAL não encontrada")
    teams: list[dict[str, Any]] = []
    for row in total["table"]:
        team_name = alias_name(row["team"]["name"], aliases)
        teams.append(
            {
                "position": int(row["position"]),
                "name": team_name,
                "played": int(row["playedGames"]),
                "won": int(row["won"]),
                "drawn": int(row["draw"]),
                "lost": int(row["lost"]),
                "goalsFor": int(row["goalsFor"]),
                "goalsAgainst": int(row["goalsAgainst"]),
                "goalDifference": int(row["goalDifference"]),
                "points": int(row["points"]),
            }
        )
    teams.sort(key=lambda t: t["position"])
    return {
        "id": competition_id,
        "name": name,
        "season": season,
        "updatedAt": now_iso(),
        "teams": teams,
        "source": "football-data",
        "sourceFetchedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sourceNotes": f"football-data.org {raw.get('competition', {}).get('code', '')}",
    }


def resolve_season(comp_cfg: dict[str, Any], override: int | None) -> int:
    if override is not None:
        return override
    if comp_cfg.get("seasonFromSite", True):
        site = load_json(CONTENT / "site.json")
        return int(site["season"])
    return int(datetime.now().year)


def update_competition(competition: str, provider: str | None, season: int | None, dry_run: bool) -> dict[str, Any]:
    cfg = load_json(SOURCES_PATH)
    competitions = cfg["competitions"]
    if competition not in competitions:
        raise SystemExit(f"Competição desconhecida: {competition}. Opções: {', '.join(competitions)}")
    comp = competitions[competition]
    provider_id = provider or cfg.get("defaultProvider") or "espn"
    providers = comp["providers"]
    if provider_id not in providers:
        raise SystemExit(f"Provider desconhecido: {provider_id}. Opções: {', '.join(providers)}")
    pcfg = providers[provider_id]
    if not pcfg.get("enabled", True):
        raise SystemExit(f"Provider '{provider_id}' desabilitado em sources.json")

    season_n = resolve_season(comp, season)
    aliases = comp.get("nameAliases") or {}

    if provider_id == "espn":
        raw = fetch_espn(pcfg["leaguePath"])
        payload = parse_espn(
            raw,
            competition_id=comp["id"],
            name=comp["name"],
            season=season_n,
            aliases=aliases,
        )
        payload["sourceNotes"] = pcfg.get("notes", payload.get("sourceNotes"))
    elif provider_id == "api-football":
        key = os.environ.get(pcfg["envKey"], "").strip()
        if not key:
            raise SystemExit(
                f"Defina a variável de ambiente {pcfg['envKey']} (chave free em https://www.api-football.com/)."
            )
        raw = fetch_api_football(int(pcfg["leagueId"]), season_n, key)
        payload = parse_api_football(
            raw,
            competition_id=comp["id"],
            name=comp["name"],
            season=season_n,
            aliases=aliases,
        )
    elif provider_id == "football-data":
        token = os.environ.get(pcfg["envKey"], "").strip()
        if not token:
            raise SystemExit(
                f"Defina {pcfg['envKey']} (token em https://www.football-data.org/). "
                "Atenção: BSA pode não estar no plano free."
            )
        raw = fetch_football_data(pcfg["competitionCode"], token)
        payload = parse_football_data(
            raw,
            competition_id=comp["id"],
            name=comp["name"],
            season=season_n,
            aliases=aliases,
        )
    else:
        raise SystemExit(f"Provider sem implementação: {provider_id}")

    # Validate before write
    StandingsFile.model_validate({k: v for k, v in payload.items() if k in StandingsFile.model_fields})

    out = CONTENT / "standings" / f"{competition}.json"
    if dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return payload

    write_standings(out, payload)
    print(f"Atualizado {out} via {provider_id} ({len(payload['teams'])} times, temporada {season_n})")
    top = ", ".join(f"{t['position']}º {t['name']} ({t['points']})" for t in payload["teams"][:5])
    print(f"Topo: {top}")

    if competition == "brasileirao":
        # Recompute objectives from the new table
        import subprocess

        py = sys.executable
        subprocess.run([py, str(ROOT / "tools" / "compute_objectives.py")], check=False, cwd=ROOT)

    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Atualiza tabelas a partir de fontes configuradas")
    parser.add_argument("--competition", default="brasileirao")
    parser.add_argument("--provider", default=None, help="espn | api-football | football-data")
    parser.add_argument("--season", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--list-providers", action="store_true")
    args = parser.parse_args()

    # Load .env if present (simple KEY=VALUE)
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

    if args.list_providers:
        cfg = load_json(SOURCES_PATH)
        print(json.dumps(cfg, ensure_ascii=False, indent=2))
        return 0

    update_competition(args.competition, args.provider, args.season, args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
