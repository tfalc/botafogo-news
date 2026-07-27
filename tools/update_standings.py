#!/usr/bin/env python3
"""Fetch standings from configured providers (Sofascore, Google/SerpAPI, ESPN, …)."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
SOURCES_PATH = CONTENT / "config" / "standings_sources.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from schemas import StandingsFile  # noqa: E402

UA = "PortalFogao/0.2 (editorial; +https://github.com/tfalc/botafogo-news)"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def utc_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def alias_name(name: str, aliases: dict[str, str]) -> str:
    if name in aliases:
        return aliases[name]
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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def http_get(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    params: dict[str, Any] | None = None,
    prefer_chrome: bool = False,
) -> httpx.Response | Any:
    """GET with optional Chrome TLS impersonation (Sofascore/Google scraping)."""
    hdrs = {"User-Agent": UA, "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8"}
    if headers:
        hdrs.update(headers)

    if prefer_chrome:
        try:
            from curl_cffi import requests as creq

            resp = creq.get(
                url,
                params=params,
                headers=hdrs,
                impersonate="chrome124",
                timeout=35,
            )
            if resp.status_code >= 400:
                raise RuntimeError(f"HTTP {resp.status_code} for {url}: {resp.text[:200]}")
            return resp
        except ImportError as exc:
            raise SystemExit(
                "Provider exige curl_cffi (pip install curl_cffi). Rode: npm run setup:python"
            ) from exc

    with httpx.Client(timeout=35.0, headers=hdrs, follow_redirects=True) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        return resp


def base_payload(
    *,
    competition_id: str,
    name: str,
    season: int,
    teams: list[dict[str, Any]],
    source: str,
    notes: str,
    stage: str | None = None,
    fmt: str | None = None,
) -> dict[str, Any]:
    teams = sorted(teams, key=lambda t: t["position"])
    out: dict[str, Any] = {
        "id": competition_id,
        "name": name,
        "season": season,
        "updatedAt": now_iso(),
        "teams": teams,
        "source": source,
        "sourceFetchedAt": utc_iso(),
        "sourceNotes": notes,
    }
    if stage:
        out["stage"] = stage
    if fmt:
        out["format"] = fmt
    return out


# —— ESPN ——
def fetch_espn(league_path: str) -> dict[str, Any]:
    url = f"https://site.api.espn.com/apis/v2/sports/soccer/{league_path}/standings"
    return http_get(url).json()


def parse_espn(
    raw: dict[str, Any],
    *,
    competition_id: str,
    name: str,
    season: int,
    aliases: dict[str, str],
) -> dict[str, Any]:
    children = raw.get("children") or []
    if not children:
        raise ValueError("ESPN: resposta sem standings")
    entries = children[0]["standings"]["entries"]
    teams: list[dict[str, Any]] = []
    for entry in entries:
        stats = {s["name"]: s.get("value", s.get("displayValue")) for s in entry.get("stats", [])}

        def num(key: str, bag: dict[str, Any] = stats) -> int:
            val = bag.get(key, 0)
            return int(float(val))

        gf = num("pointsFor")
        ga = num("pointsAgainst")
        teams.append(
            {
                "position": num("rank"),
                "name": alias_name(entry["team"]["displayName"], aliases),
                "played": num("gamesPlayed"),
                "won": num("wins"),
                "drawn": num("ties"),
                "lost": num("losses"),
                "goalsFor": gf,
                "goalsAgainst": ga,
                "goalDifference": gf - ga,
                "points": num("points"),
            }
        )
    return base_payload(
        competition_id=competition_id,
        name=name,
        season=season,
        teams=teams,
        source="espn",
        notes=f"ESPN site API ({raw.get('name', 'league')})",
    )


# —— API-Football ——
def fetch_api_football(league_id: int, season: int, api_key: str) -> dict[str, Any]:
    url = "https://v3.football.api-sports.io/standings"
    return http_get(
        url,
        headers={"x-apisports-key": api_key},
        params={"league": league_id, "season": season},
    ).json()


def parse_api_football(
    raw: dict[str, Any],
    *,
    competition_id: str,
    name: str,
    season: int,
    aliases: dict[str, str],
) -> dict[str, Any]:
    errors = raw.get("errors")
    if errors:
        raise ValueError(f"api-football errors: {errors}")
    response = raw.get("response") or []
    if not response:
        raise ValueError("api-football: resposta vazia")
    league = response[0]["league"]
    table = league["standings"][0]
    teams = [
        {
            "position": int(row["rank"]),
            "name": alias_name(row["team"]["name"], aliases),
            "played": int(row["all"]["played"]),
            "won": int(row["all"]["win"]),
            "drawn": int(row["all"]["draw"]),
            "lost": int(row["all"]["lose"]),
            "goalsFor": int(row["all"]["goals"]["for"]),
            "goalsAgainst": int(row["all"]["goals"]["against"]),
            "goalDifference": int(row["goalsDiff"]),
            "points": int(row["points"]),
        }
        for row in table
    ]
    return base_payload(
        competition_id=competition_id,
        name=name,
        season=season,
        teams=teams,
        source="api-football",
        notes=f"API-Football league={league.get('id')} season={league.get('season')}",
    )


# —— football-data ——
def fetch_football_data(code: str, token: str) -> dict[str, Any]:
    url = f"https://api.football-data.org/v4/competitions/{code}/standings"
    return http_get(url, headers={"X-Auth-Token": token}).json()


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
    teams = [
        {
            "position": int(row["position"]),
            "name": alias_name(row["team"]["name"], aliases),
            "played": int(row["playedGames"]),
            "won": int(row["won"]),
            "drawn": int(row["draw"]),
            "lost": int(row["lost"]),
            "goalsFor": int(row["goalsFor"]),
            "goalsAgainst": int(row["goalsAgainst"]),
            "goalDifference": int(row["goalDifference"]),
            "points": int(row["points"]),
        }
        for row in total["table"]
    ]
    return base_payload(
        competition_id=competition_id,
        name=name,
        season=season,
        teams=teams,
        source="football-data",
        notes=f"football-data.org {raw.get('competition', {}).get('code', '')}",
    )


# —— Sofascore ——
def sofascore_season_id(tournament_id: int, season_year: int) -> int:
    url = f"https://api.sofascore.com/api/v1/unique-tournament/{tournament_id}/seasons"
    raw = http_get(url, prefer_chrome=True).json()
    seasons = raw.get("seasons") or []
    for s in seasons:
        if str(s.get("year")) == str(season_year) or str(season_year) in str(s.get("name", "")):
            return int(s["id"])
    if not seasons:
        raise ValueError(f"Sofascore: sem seasons para tournament={tournament_id}")
    return int(seasons[0]["id"])


def parse_sofascore_table(
    raw: dict[str, Any],
    *,
    competition_id: str,
    name: str,
    season: int,
    aliases: dict[str, str],
) -> dict[str, Any]:
    standings = raw.get("standings") or []
    if not standings:
        raise ValueError("Sofascore: standings vazio")
    # Prefer overall / total
    block = next((s for s in standings if s.get("type") == "total"), standings[0])
    rows = block.get("rows") or []
    teams: list[dict[str, Any]] = []
    for row in rows:
        team_name = alias_name(row["team"]["name"], aliases)
        teams.append(
            {
                "position": int(row["position"]),
                "name": team_name,
                "played": int(row.get("matches", 0)),
                "won": int(row.get("wins", 0)),
                "drawn": int(row.get("draws", 0)),
                "lost": int(row.get("losses", 0)),
                "goalsFor": int(row.get("scoresFor", 0)),
                "goalsAgainst": int(row.get("scoresAgainst", 0)),
                "goalDifference": int(row.get("scoresFor", 0)) - int(row.get("scoresAgainst", 0)),
                "points": int(row.get("points", 0)),
            }
        )
    return base_payload(
        competition_id=competition_id,
        name=name,
        season=season,
        teams=teams,
        source="sofascore",
        notes=f"Sofascore tournament standings ({block.get('name', 'total')})",
        fmt="league",
    )


def parse_sofascore_cuptree(
    raw: dict[str, Any],
    *,
    competition_id: str,
    name: str,
    season: int,
    aliases: dict[str, str],
) -> dict[str, Any]:
    trees = raw.get("cupTrees") or []
    if not trees:
        raise ValueError("Sofascore: cupTrees vazio")
    tree = trees[0]
    stage_name = tree.get("name") or "Mata-mata"
    current = tree.get("currentRound") or {}
    if isinstance(current, dict) and current.get("description"):
        stage_name = str(current.get("description") or current.get("type") or stage_name)

    rounds = tree.get("rounds") or []
    # Prefer the latest unfinished round; else last round with blocks
    target_rounds = list(reversed(rounds))
    seen: dict[str, dict[str, Any]] = {}
    current_stage = stage_name

    def add_team(tname: str, note: str) -> None:
        tname = alias_name(tname, aliases)
        if not tname or tname in seen:
            return
        seen[tname] = {
            "position": len(seen) + 1,
            "name": tname,
            "played": 0,
            "won": 0,
            "drawn": 0,
            "lost": 0,
            "goalsFor": 0,
            "goalsAgainst": 0,
            "goalDifference": 0,
            "points": 0,
            "note": note,
        }

    for rnd in target_rounds:
        blocks = rnd.get("blocks") or []
        if not blocks:
            continue
        note = str(rnd.get("description") or rnd.get("type") or current_stage)
        current_stage = note
        for block in blocks:
            for part in block.get("participants") or []:
                team = part.get("team") or {}
                tname = team.get("name")
                if tname:
                    status = "classificado" if part.get("winner") else note
                    add_team(tname, status)
        if seen:
            break

    if not seen:
        raise ValueError("Sofascore: não foi possível extrair times da chave")

    return base_payload(
        competition_id=competition_id,
        name=name,
        season=season,
        teams=list(seen.values()),
        source="sofascore",
        notes="Sofascore cup tree (mata-mata)",
        stage=current_stage,
        fmt="knockout",
    )


def fetch_sofascore(pcfg: dict[str, Any], season_n: int) -> dict[str, Any]:
    tid = int(pcfg["uniqueTournamentId"])
    sid = sofascore_season_id(tid, season_n)
    mode = pcfg.get("mode", "table")
    if mode == "cuptree":
        url = f"https://api.sofascore.com/api/v1/unique-tournament/{tid}/season/{sid}/cuptrees"
        return http_get(url, prefer_chrome=True).json()
    url = f"https://api.sofascore.com/api/v1/unique-tournament/{tid}/season/{sid}/standings/total"
    return http_get(url, prefer_chrome=True).json()


# —— Google (SerpAPI) + Wikipedia fallback ——
class _WikiTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_table = False
        self.tables: list[list[list[str]]] = []
        self._table: list[list[str]] = []
        self._row: list[str] = []
        self._cell = ""
        self._capture = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        cls = " ".join(v or "" for k, v in attrs if k == "class")
        if tag == "table" and "wikitable" in cls:
            self.in_table = True
            self._table = []
        elif self.in_table and tag == "tr":
            self._row = []
        elif self.in_table and tag in {"td", "th"}:
            self._capture = True
            self._cell = ""

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self._capture:
            self._row.append(re.sub(r"\s+", " ", self._cell).strip())
            self._capture = False
        elif tag == "tr" and self.in_table and self._row:
            self._table.append(self._row)
        elif tag == "table" and self.in_table:
            self.tables.append(self._table)
            self.in_table = False

    def handle_data(self, data: str) -> None:
        if self._capture:
            self._cell += data


def parse_wiki_league_table(html: str, aliases: dict[str, str]) -> list[dict[str, Any]]:
    parser = _WikiTableParser()
    parser.feed(html)
    best: list[dict[str, Any]] = []
    for table in parser.tables:
        if len(table) < 5:
            continue
        header = [re.split(r"\.mw-parser-output", c, maxsplit=1)[0] for c in table[0]]
        header = [re.sub(r"\s+", " ", c).strip().casefold()[:48] for c in header]
        # Prefer tables with Pts / Pontos
        if not any("pts" in h or "ponto" in h for h in header):
            # sometimes header is second row
            if len(table) > 1:
                header = [re.split(r"\.mw-parser-output", c, maxsplit=1)[0] for c in table[1]]
                header = [re.sub(r"\s+", " ", c).strip().casefold()[:48] for c in header]
                body = table[2:]
            else:
                continue
        else:
            body = table[1:]

        def col(hdr: list[str], *names: str) -> int | None:
            # Exact match first (important for single-letter cols: J V E D)
            for i, h in enumerate(hdr):
                if h in names:
                    return i
            for i, h in enumerate(hdr):
                if any(len(n) > 1 and (h.startswith(n) or n in h) for n in names):
                    return i
            return None

        i_pos = col(header, "pos", "#")
        i_team = col(header, "equipe", "time", "clube", "team")
        i_pts = col(header, "pts", "pontos", "ponto")
        i_pj = col(header, "j", "pj", "partidas", "jogos")
        i_v = col(header, "v", "vit")
        i_e = col(header, "e", "emp")
        i_d = col(header, "d", "der")
        i_gp = col(header, "gp", "gm")
        i_gc = col(header, "gc", "gs")
        i_sg = col(header, "sg", "saldo")
        if i_team is None or i_pts is None:
            continue
        # Avoid mapping V/E/D onto "equipe" via startswith
        if i_team in {i_v, i_e, i_d, i_pj}:
            i_v, i_e, i_d, i_pj, i_gp, i_gc, i_sg = 4, 5, 6, 3, 7, 8, 9
            if i_pts != 2:
                i_pts = 2
            if i_team != 1:
                i_team = 1
            if i_pos != 0:
                i_pos = 0
        teams: list[dict[str, Any]] = []
        for idx, row in enumerate(body, start=1):
            if len(row) <= max(i for i in (i_team, i_pts) if i is not None):
                continue
            try:
                name = alias_name(re.sub(r"\[.*?\]", "", row[i_team]).strip(), aliases)
                if not name or name.casefold() in {"time", "equipe", "clube"}:
                    continue
                pts = int(re.sub(r"[^\d-]", "", row[i_pts]) or 0)
                pos = int(re.sub(r"[^\d]", "", row[i_pos]) or idx) if i_pos is not None else idx

                def cell(i: int | None, r: list[str] = row) -> int:
                    if i is None or i >= len(r):
                        return 0
                    return int(re.sub(r"[^\d-]", "", r[i]) or 0)

                gf = cell(i_gp)
                ga = cell(i_gc)
                teams.append(
                    {
                        "position": pos,
                        "name": name,
                        "played": cell(i_pj),
                        "won": cell(i_v),
                        "drawn": cell(i_e),
                        "lost": cell(i_d),
                        "goalsFor": gf,
                        "goalsAgainst": ga,
                        "goalDifference": cell(i_sg) if i_sg is not None else gf - ga,
                        "points": pts,
                    }
                )
            except ValueError:
                continue
        if len(teams) < 8:
            continue
        # Prefer season table: points roughly match 3*W+D and stay in league range
        coherent = 0
        for t in teams:
            expected = 3 * t["won"] + t["drawn"]
            if t["points"] == expected and 0 <= t["points"] <= 120:
                coherent += 1
        if coherent < max(6, len(teams) // 2):
            continue
        if len(teams) > len(best):
            best = teams
    if len(best) < 4:
        raise ValueError("Wikipedia: tabela de classificação não encontrada/parseável")
    return best


def fetch_google_serpapi(query: str, api_key: str) -> dict[str, Any]:
    url = "https://serpapi.com/search.json"
    return http_get(
        url,
        params={"engine": "google", "q": query, "hl": "pt-BR", "gl": "br", "api_key": api_key},
    ).json()


def parse_serpapi_sports(
    raw: dict[str, Any],
    *,
    competition_id: str,
    name: str,
    season: int,
    aliases: dict[str, str],
) -> dict[str, Any]:
    sports = raw.get("sports_results") or {}
    standings = sports.get("standings") or {}
    rows: list[dict[str, Any]] = []
    if isinstance(standings, dict):
        for group_rows in standings.values():
            if isinstance(group_rows, list):
                rows.extend(group_rows)
    elif isinstance(standings, list):
        rows = standings
    if not rows:
        raise ValueError("SerpAPI/Google: sports_results.standings ausente")

    teams: list[dict[str, Any]] = []
    for idx, row in enumerate(rows, start=1):
        team_name = alias_name(str(row.get("team") or row.get("name") or ""), aliases)
        if not team_name:
            continue
        wins = int(row.get("wins") or row.get("w") or 0)
        draws = int(row.get("draws") or row.get("d") or row.get("ties") or 0)
        losses = int(row.get("losses") or row.get("l") or 0)
        played = int(row.get("matches") or row.get("played") or (wins + draws + losses))
        gf = int(row.get("goals_for") or row.get("gf") or 0)
        ga = int(row.get("goals_against") or row.get("ga") or 0)
        teams.append(
            {
                "position": int(row.get("rank") or row.get("pos") or idx),
                "name": team_name,
                "played": played,
                "won": wins,
                "drawn": draws,
                "lost": losses,
                "goalsFor": gf,
                "goalsAgainst": ga,
                "goalDifference": int(row.get("goal_diff") or gf - ga),
                "points": int(row.get("points") or row.get("pts") or 0),
            }
        )
    return base_payload(
        competition_id=competition_id,
        name=name,
        season=season,
        teams=teams,
        source="google",
        notes=f"Google Sports via SerpAPI ({sports.get('title') or query_safe(raw)})",
    )


def query_safe(raw: dict[str, Any]) -> str:
    return str((raw.get("search_parameters") or {}).get("q") or "search")


def fetch_wikipedia_html(title: str) -> str:
    api = "https://pt.wikipedia.org/w/api.php"

    def wiki_get(params: dict[str, Any]) -> dict[str, Any]:
        resp = http_get(
            api,
            params=params,
            headers={"Accept": "application/json"},
            prefer_chrome=True,
        )
        return resp.json()

    data = wiki_get(
        {
            "action": "parse",
            "page": title,
            "prop": "text",
            "format": "json",
            "redirects": 1,
        }
    )
    if "error" not in data:
        return data["parse"]["text"]["*"]

    search = wiki_get(
        {
            "action": "query",
            "list": "search",
            "srsearch": title,
            "srlimit": 8,
            "format": "json",
        }
    )
    hits = (search.get("query") or {}).get("search") or []
    for hit in hits:
        cand = hit.get("title")
        if not cand:
            continue
        retry = wiki_get(
            {
                "action": "parse",
                "page": cand,
                "prop": "text",
                "format": "json",
                "redirects": 1,
            }
        )
        if "error" not in retry:
            return retry["parse"]["text"]["*"]
    raise ValueError(f"Wikipedia: {data['error']} (busca: {[h.get('title') for h in hits]})")


def fetch_google(
    pcfg: dict[str, Any],
    *,
    competition_id: str,
    name: str,
    season: int,
    aliases: dict[str, str],
) -> dict[str, Any]:
    query = str(pcfg.get("searchQuery") or f"{name} classificação {season}").replace(
        "{season}", str(season)
    )
    serp_key = os.environ.get("SERPAPI_KEY", "").strip()
    if serp_key:
        raw = fetch_google_serpapi(query, serp_key)
        try:
            return parse_serpapi_sports(
                raw,
                competition_id=competition_id,
                name=name,
                season=season,
                aliases=aliases,
            )
        except ValueError:
            pass

    title_tmpl = pcfg.get("wikipediaTitle") or name
    titles = [
        str(title_tmpl).replace("{season}", str(season)),
        str(title_tmpl).replace("{season}", str(season - 1)),
        f"{name} de {season}",
        name,
    ]
    last_err: Exception | None = None
    html = ""
    used_title = titles[0]
    for title in titles:
        try:
            html = fetch_wikipedia_html(title)
            used_title = title
            break
        except Exception as exc:  # noqa: BLE001
            last_err = exc
    if not html:
        raise ValueError(str(last_err or "Wikipedia indisponível")) from last_err

    teams = parse_wiki_league_table(html, aliases)
    return base_payload(
        competition_id=competition_id,
        name=name,
        season=season,
        teams=teams,
        source="google",
        notes=(
            f"Fallback Wikipedia «{used_title}» (página tipicamente rankeada no Google BR). "
            "Defina SERPAPI_KEY para Google Sports direto."
        ),
    )


def resolve_season(comp_cfg: dict[str, Any], override: int | None) -> int:
    if override is not None:
        return override
    if comp_cfg.get("seasonFromSite", True):
        site = load_json(CONTENT / "site.json")
        return int(site["season"])
    return int(datetime.now().year)


def list_active_competition_ids() -> list[str]:
    site = load_json(CONTENT / "site.json")
    active = list(site.get("activeCompetitions") or [])
    primary = site.get("primaryCompetition")
    if primary and primary not in active:
        active.insert(0, primary)
    return active


def update_competition(
    competition: str, provider: str | None, season: int | None, dry_run: bool
) -> dict[str, Any]:
    cfg = load_json(SOURCES_PATH)
    competitions = cfg["competitions"]
    if competition not in competitions:
        opts = ", ".join(competitions)
        raise SystemExit(f"Competição desconhecida: {competition}. Opções: {opts}")
    comp = competitions[competition]
    provider_id = provider or cfg.get("defaultProvider") or "sofascore"
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
            raw, competition_id=comp["id"], name=comp["name"], season=season_n, aliases=aliases
        )
        payload["sourceNotes"] = pcfg.get("notes", payload.get("sourceNotes"))
    elif provider_id == "api-football":
        key = os.environ.get(pcfg["envKey"], "").strip()
        if not key:
            raise SystemExit(f"Defina {pcfg['envKey']} no .env")
        raw = fetch_api_football(int(pcfg["leagueId"]), season_n, key)
        payload = parse_api_football(
            raw, competition_id=comp["id"], name=comp["name"], season=season_n, aliases=aliases
        )
    elif provider_id == "football-data":
        token = os.environ.get(pcfg["envKey"], "").strip()
        if not token:
            raise SystemExit(f"Defina {pcfg['envKey']} no .env")
        raw = fetch_football_data(pcfg["competitionCode"], token)
        payload = parse_football_data(
            raw, competition_id=comp["id"], name=comp["name"], season=season_n, aliases=aliases
        )
    elif provider_id == "sofascore":
        raw = fetch_sofascore(pcfg, season_n)
        if pcfg.get("mode") == "cuptree":
            payload = parse_sofascore_cuptree(
                raw, competition_id=comp["id"], name=comp["name"], season=season_n, aliases=aliases
            )
        else:
            payload = parse_sofascore_table(
                raw, competition_id=comp["id"], name=comp["name"], season=season_n, aliases=aliases
            )
        payload["sourceNotes"] = pcfg.get("notes", payload.get("sourceNotes"))
    elif provider_id == "google":
        payload = fetch_google(
            pcfg,
            competition_id=comp["id"],
            name=comp["name"],
            season=season_n,
            aliases=aliases,
        )
        if pcfg.get("notes"):
            payload["sourceNotes"] = f"{payload.get('sourceNotes')} | {pcfg['notes']}"
    else:
        raise SystemExit(f"Provider sem implementação: {provider_id}")

    core = {k: v for k, v in payload.items() if k in StandingsFile.model_fields}
    StandingsFile.model_validate(core)

    out = CONTENT / "standings" / f"{competition}.json"
    if dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return payload

    write_standings(out, payload)
    print(
        f"Atualizado {out} via {provider_id} "
        f"({len(payload['teams'])} times, temporada {season_n})"
    )
    top = ", ".join(f"{t['position']}º {t['name']} ({t['points']})" for t in payload["teams"][:5])
    print(f"Topo: {top}")

    if competition == "brasileirao":
        script = str(ROOT / "tools" / "compute_objectives.py")
        subprocess.run([sys.executable, script], check=False, cwd=ROOT)

    return payload


def load_dotenv() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Atualiza tabelas a partir de fontes configuradas")
    parser.add_argument("--competition", default=None, help="id da competição ou 'all-active'")
    parser.add_argument(
        "--provider",
        default=None,
        help="sofascore | google | espn | api-football | football-data",
    )
    parser.add_argument("--season", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--list-providers", action="store_true")
    args = parser.parse_args()
    load_dotenv()

    if args.list_providers:
        cfg = load_json(SOURCES_PATH)
        cfg["activeCompetitions"] = list_active_competition_ids()
        print(json.dumps(cfg, ensure_ascii=False, indent=2))
        return 0

    competition = args.competition or "brasileirao"
    if competition == "all-active":
        for comp_id in list_active_competition_ids():
            print(f"—— {comp_id} ——")
            update_competition(comp_id, args.provider, args.season, args.dry_run)
        return 0

    update_competition(competition, args.provider, args.season, args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
