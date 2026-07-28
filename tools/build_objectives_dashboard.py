#!/usr/bin/env python3
"""Build season-objectives dashboard JSON from fixtures + editorial inputs."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def team_points(home: str, away: str, hs: int, aws: int, team: str) -> int:
    if team == home:
        if hs > aws:
            return 3
        if hs == aws:
            return 1
        return 0
    if team == away:
        if aws > hs:
            return 3
        if aws == hs:
            return 1
        return 0
    return 0


def team_goals_for(home: str, away: str, hs: int, aws: int, team: str) -> int:
    if team == home:
        return hs
    if team == away:
        return aws
    return 0


def match_result_for_team(
    home: str, away: str, hs: int | None, aws: int | None, team: str
) -> str | None:
    if hs is None or aws is None:
        return None
    if team == home:
        if hs > aws:
            return "W"
        if hs < aws:
            return "L"
        return "D"
    if team == away:
        if aws > hs:
            return "W"
        if aws < hs:
            return "L"
        return "D"
    return None


def team_matches(fixtures: dict, team: str) -> list[dict]:
    return [
        m
        for m in fixtures.get("matches", [])
        if team in (m.get("home"), m.get("away")) and m.get("round") is not None
    ]


def abbrev(name: str) -> str:
    special = {
        "Botafogo": "BOT",
        "Flamengo": "FLA",
        "Fluminense": "FLU",
        "Palmeiras": "PAL",
        "São Paulo": "SAO",
        "Santos": "SAN",
        "Corinthians": "COR",
        "Grêmio": "GRE",
        "Internacional": "INT",
        "Cruzeiro": "CRU",
        "Atlético-MG": "CAM",
        "Athletico-PR": "CAP",
        "Bahia": "BAH",
        "Bragantino": "RBB",
        "Vasco da Gama": "VAS",
        "Vitória": "VIT",
        "Coritiba": "CFC",
        "Mirassol": "MIR",
        "Remo": "REM",
        "Chapecoense": "CHA",
    }
    if name in special:
        return special[name]
    parts = name.replace("-", " ").split()
    if len(parts) == 1:
        return parts[0][:3].upper()
    return "".join(p[0] for p in parts[:3]).upper()


def build_dashboard(
    config: dict,
    fixtures: dict,
    leaders: dict,
    position_by_round: dict,
    standings: dict | None,
) -> dict:
    team = config["team"]
    total_rounds = int(config.get("totalRounds", 38))
    matches = sorted(team_matches(fixtures, team), key=lambda m: m["round"])

    played = [m for m in matches if m.get("status") == "played"]
    points = 0
    wins = 0
    goals = 0
    for m in played:
        hs = m.get("homeScore")
        aws = m.get("awayScore")
        if hs is None or aws is None:
            continue
        pts = team_points(m["home"], m["away"], hs, aws, team)
        points += pts
        if pts == 3:
            wins += 1
        goals += team_goals_for(m["home"], m["away"], hs, aws, team)

    played_count = len(played)
    max_from_played = played_count * 3
    aproveitamento = round((points / max_from_played) * 100) if max_from_played else 0

    positions = list(position_by_round.get("positions", []))
    while len(positions) < total_rounds:
        positions.append(None)
    positions = positions[:total_rounds]

    current_round = 0
    for m in matches:
        if m.get("status") == "played":
            current_round = max(current_round, int(m["round"]))
    if current_round == 0:
        scheduled = [m for m in matches if m.get("status") == "scheduled"]
        if scheduled:
            current_round = min(int(m["round"]) for m in scheduled) - 1
    current_round = max(0, min(current_round, total_rounds))

    position = None
    for p in reversed(positions[:current_round] if current_round else positions):
        if p is not None:
            position = p
            break
    if position is None and standings:
        for t in standings.get("teams", []):
            if t.get("name") == team:
                position = t.get("position")
                break
    if position is None:
        position = 0

    thresholds = config.get("thresholds", [])
    season_max_marker = max((t["seasonPoints"] for t in thresholds), default=114)
    season_bar_max = max(season_max_marker, points, total_rounds * 3)

    season_bars = {
        "points": {
            "value": points,
            "max": season_bar_max,
            "label": f"{points} pts.",
        },
        "aproveitamento": {
            "value": aproveitamento,
            "max": 100,
            "label": f"{aproveitamento}%",
        },
        "markers": [
            {
                "id": t["id"],
                "label": t["label"],
                "points": t["seasonPoints"],
                "color": t["color"],
                "pctPoints": round((t["seasonPoints"] / season_bar_max) * 100, 2),
                "pctAproveitamento": round((t["seasonPoints"] / (total_rounds * 3)) * 100, 2),
            }
            for t in thresholds
        ],
    }

    block_targets: dict[str, int] = config.get("blockTargets", {})
    blocks_out: list[dict] = []

    for block in config.get("blocks", []):
        rounds = list(block["rounds"])
        block_matches = [m for m in matches if int(m["round"]) in rounds]
        # Ensure one slot per round even if missing fixture
        by_round = {int(m["round"]): m for m in block_matches}
        slots: list[dict] = []
        block_pts = 0
        any_played = False
        any_future = False

        for rnd in rounds:
            m = by_round.get(rnd)
            if not m:
                slots.append(
                    {
                        "round": rnd,
                        "home": "—",
                        "away": "—",
                        "homeAbbrev": "—",
                        "awayAbbrev": "—",
                        "homeScore": None,
                        "awayScore": None,
                        "status": "scheduled",
                        "result": None,
                        "isHome": None,
                    }
                )
                any_future = True
                continue

            hs = m.get("homeScore")
            aws = m.get("awayScore")
            status = m.get("status", "scheduled")
            result = None
            if status == "played" and hs is not None and aws is not None:
                any_played = True
                result = match_result_for_team(m["home"], m["away"], hs, aws, team)
                block_pts += team_points(m["home"], m["away"], hs, aws, team)
            else:
                any_future = True

            slots.append(
                {
                    "round": rnd,
                    "home": m["home"],
                    "away": m["away"],
                    "homeAbbrev": abbrev(m["home"]),
                    "awayAbbrev": abbrev(m["away"]),
                    "homeScore": hs if status == "played" else None,
                    "awayScore": aws if status == "played" else None,
                    "status": status,
                    "result": result,
                    "isHome": m["home"] == team,
                }
            )

        max_pts = len(rounds) * 3
        active = any_played or (not any_future and bool(slots))
        # Block is "started" if any played; "upcoming" if none played
        state = "upcoming"
        if any_played and any_future:
            state = "partial"
        elif any_played:
            state = "complete"
        elif not any_future and slots:
            state = "complete"

        objectives_meta = []
        for thr in thresholds:
            oid = thr["id"]
            target = int(block_targets.get(oid, 0))
            # Scale block target for larger blocks (e.g. 8 rounds)
            base_rounds = 6
            if len(rounds) != base_rounds and base_rounds:
                target = round(target * (len(rounds) / base_rounds))
            acumulado = block_pts - target if state != "upcoming" else 0
            objectives_meta.append(
                {
                    "id": oid,
                    "label": thr["label"],
                    "color": thr["color"],
                    "meta": target,
                    "acumulado": acumulado,
                    "metaPct": min(100, round((target / max_pts) * 100)) if max_pts else 0,
                    "pointsPct": min(100, round((block_pts / max_pts) * 100)) if max_pts else 0,
                }
            )

        blocks_out.append(
            {
                "id": block["id"],
                "label": block["label"],
                "rounds": rounds,
                "points": block_pts if state != "upcoming" else 0,
                "maxPoints": max_pts,
                "state": state,
                "active": state != "upcoming",
                "matches": slots,
                "objectives": objectives_meta,
            }
        )

    return {
        "team": team,
        "competition": config["competition"],
        "season": config["season"],
        "generatedAt": datetime.now().isoformat(timespec="seconds"),
        "summary": {
            "round": current_round,
            "totalRounds": total_rounds,
            "position": position,
            "points": points,
            "wins": wins,
            "goals": goals,
            "aproveitamento": aproveitamento,
            "played": played_count,
        },
        "leaders": {
            "goals": leaders.get("goals", []),
            "assists": leaders.get("assists", []),
            "sofascore": leaders.get("sofascore", []),
        },
        "positionByRound": positions,
        "seasonBars": season_bars,
        "thresholds": thresholds,
        "blocks": blocks_out,
    }


def main() -> int:
    config_path = CONTENT / "objectives" / "config.json"
    config = load_json(config_path)
    competition = config["competition"]

    fixtures_path = CONTENT / "fixtures" / f"{competition}.json"
    fixtures = load_json(fixtures_path) if fixtures_path.exists() else {"matches": []}

    leaders_path = CONTENT / "objectives" / "leaders.json"
    leaders = load_json(leaders_path) if leaders_path.exists() else {}

    pos_path = CONTENT / "objectives" / "position_by_round.json"
    position_by_round = load_json(pos_path) if pos_path.exists() else {"positions": []}

    standings_path = CONTENT / "standings" / f"{competition}.json"
    standings = load_json(standings_path) if standings_path.exists() else None

    dashboard = build_dashboard(config, fixtures, leaders, position_by_round, standings)
    out = CONTENT / "objectives" / "dashboard.json"
    text = json.dumps(dashboard, ensure_ascii=False, indent=2) + "\n"
    if out.exists():
        try:
            previous = json.loads(out.read_text(encoding="utf-8"))
            previous.pop("generatedAt", None)
            comparable = {**dashboard}
            comparable.pop("generatedAt", None)
            if previous == comparable:
                print(f"Unchanged {out}")
            else:
                out.write_text(text, encoding="utf-8")
                print(f"Wrote {out}")
        except (json.JSONDecodeError, OSError):
            out.write_text(text, encoding="utf-8")
            print(f"Wrote {out}")
    else:
        out.write_text(text, encoding="utf-8")
        print(f"Wrote {out}")
    s = dashboard["summary"]
    print(
        f"  Rodada {s['round']}/{s['totalRounds']} | "
        f"{s['position']}º | {s['points']} pts | "
        f"{s['wins']} V | {s['goals']} gols | {s['aproveitamento']}%"
    )
    for b in dashboard["blocks"]:
        print(f"  {b['label']}: {b['points']}/{b['maxPoints']} ({b['state']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
