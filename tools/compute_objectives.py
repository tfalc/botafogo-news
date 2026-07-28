#!/usr/bin/env python3
"""Compute points-needed scenarios for season objectives."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def remaining_matches(fixtures: dict, team: str) -> list[dict]:
    return [
        m
        for m in fixtures.get("matches", [])
        if m.get("status") == "scheduled" and team in (m.get("home"), m.get("away"))
    ]


def remaining_for_team(fixtures: dict, team: str) -> int:
    return len(remaining_matches(fixtures, team))


def compute(standings: dict, fixtures: dict, config: dict) -> dict:
    team_name = config["team"]
    teams = sorted(standings["teams"], key=lambda t: t["position"])
    by_name = {t["name"]: t for t in teams}
    if team_name not in by_name:
        raise ValueError(f"Team '{team_name}' not in standings")

    us = by_name[team_name]
    our_remaining = remaining_for_team(fixtures, team_name)
    our_max = us["points"] + our_remaining * 3
    our_min = us["points"]  # assume 0 pts from remaining in pessimist floor

    results = []
    for obj in config["objectives"]:
        entry = {
            "id": obj["id"],
            "label": obj["label"],
            "description": obj["description"],
            "tone": obj.get("tone", ""),
            "type": obj["type"],
            "currentPosition": us["position"],
            "currentPoints": us["points"],
            "remainingMatches": our_remaining,
            "maxPoints": our_max,
            "minPoints": our_min,
        }

        if obj["type"] == "reach_top":
            max_pos = obj["maxPosition"]
            zone = [t for t in teams if t["position"] <= max_pos]
            cutoff = zone[-1]
            # Points of the last team currently inside the zone
            cutoff_points = cutoff["points"]
            # Optimistic: we win all; teams currently above us get 0 from remaining
            # Still possible if our max points can reach/exceed current cutoff
            # and we can mathematically finish in zone (simplified).
            gap_to_cutoff = max(0, cutoff_points - us["points"])
            # Leader / zone edge remaining
            rivals_above = [t for t in teams if t["position"] < us["position"] and t["position"] <= max_pos]
            rivals_min = []
            for r in rivals_above:
                r_rem = remaining_for_team(fixtures, r["name"])
                rivals_min.append(r["points"])  # they get 0 remaining (optimistic for us)
            leader = teams[0]
            leader_remaining = remaining_for_team(fixtures, leader["name"])
            leader_min = leader["points"]  # optimistic: leader stalls
            possible = our_max >= cutoff_points or us["position"] <= max_pos
            # Stricter title check: can we catch leader?
            if max_pos == 1:
                possible = our_max >= leader_min
                gap_to_cutoff = max(0, leader["points"] - us["points"])
                cutoff_points = leader["points"]

            entry.update(
                {
                    "cutoffPoints": cutoff_points,
                    "pointsGap": gap_to_cutoff,
                    "pointsNeededOptimistic": gap_to_cutoff,
                    "stillPossible": possible,
                    "inZone": us["position"] <= max_pos,
                    "referenceTeam": cutoff["name"] if max_pos > 1 else leader["name"],
                }
            )

        elif obj["type"] == "reach_range":
            min_pos = obj["minPosition"]
            max_pos = obj["maxPosition"]
            in_zone = min_pos <= us["position"] <= max_pos
            # Lower edge of zone (worst position still in Sula)
            edge = next((t for t in teams if t["position"] == max_pos), teams[-1])
            top_edge = next((t for t in teams if t["position"] == min_pos), teams[0])
            gap = max(0, edge["points"] - us["points"]) if us["position"] > max_pos else 0
            possible = our_max >= edge["points"] or us["position"] <= max_pos
            entry.update(
                {
                    "cutoffPoints": edge["points"],
                    "pointsGap": gap,
                    "pointsNeededOptimistic": gap,
                    "stillPossible": possible,
                    "inZone": in_zone,
                    "referenceTeam": edge["name"],
                    "zoneTopPoints": top_edge["points"],
                }
            )

        elif obj["type"] == "avoid_bottom":
            danger = obj["minDangerPosition"]
            safety = next((t for t in teams if t["position"] == danger - 1), None)
            first_danger = next((t for t in teams if t["position"] == danger), teams[-1])
            in_danger = us["position"] >= danger
            # Need to stay at or above safety line points (optimistic: danger zone stalls)
            safety_points = safety["points"] if safety else first_danger["points"] + 1
            gap = max(0, first_danger["points"] + 1 - us["points"]) if in_danger else 0
            # Still possible to avoid if max points can exceed current Z4 threshold
            z4_max_if_they_win_all = first_danger["points"] + remaining_for_team(
                fixtures, first_danger["name"]
            ) * 3
            possible = our_max > first_danger["points"] or not in_danger
            entry.update(
                {
                    "cutoffPoints": first_danger["points"],
                    "safetyLinePoints": safety_points,
                    "pointsGap": gap,
                    "pointsNeededOptimistic": gap,
                    "stillPossible": possible,
                    "inZone": not in_danger,
                    "inDanger": in_danger,
                    "referenceTeam": first_danger["name"],
                    "dangerMaxPossible": z4_max_if_they_win_all,
                }
            )

        results.append(entry)

    return {
        "team": team_name,
        "competition": config["competition"],
        "season": config["season"],
        "generatedAt": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
        "summary": {
            "position": us["position"],
            "points": us["points"],
            "remainingMatches": our_remaining,
            "maxPoints": our_max,
        },
        "objectives": results,
    }


def main() -> int:
    config = load_json(CONTENT / "objectives" / "config.json")
    competition = config["competition"]
    standings = load_json(CONTENT / "standings" / f"{competition}.json")
    fixtures_path = CONTENT / "fixtures" / f"{competition}.json"
    fixtures = load_json(fixtures_path) if fixtures_path.exists() else {"matches": []}

    snapshot = compute(standings, fixtures, config)
    out = CONTENT / "objectives" / "snapshot.json"
    text = json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n"
    if out.exists():
        try:
            previous = json.loads(out.read_text(encoding="utf-8"))
            previous.pop("generatedAt", None)
            comparable = {**snapshot}
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
    for obj in snapshot["objectives"]:
        flag = "OK" if obj["stillPossible"] else "—"
        zone = "IN" if obj.get("inZone") else "OUT"
        print(
            f"  [{flag}] {obj['label']}: gap={obj.get('pointsGap', '?')} "
            f"max={obj['maxPoints']} zone={zone}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
