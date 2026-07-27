"""Tests for build_objectives_dashboard helpers."""

from __future__ import annotations

from build_objectives_dashboard import abbrev, build_dashboard, team_points


def test_team_points_home_win() -> None:
    assert team_points("Botafogo", "Flamengo", 2, 0, "Botafogo") == 3
    assert team_points("Botafogo", "Flamengo", 2, 0, "Flamengo") == 0


def test_abbrev() -> None:
    assert abbrev("Botafogo") == "BOT"
    assert abbrev("Vasco da Gama") == "VAS"


def test_build_dashboard_block_points() -> None:
    config = {
        "season": 2026,
        "competition": "brasileirao",
        "team": "Botafogo",
        "totalRounds": 6,
        "thresholds": [
            {
                "id": "titulo",
                "label": "Título",
                "seasonPoints": 12,
                "color": "#7dff6a",
            }
        ],
        "blocks": [{"id": "fase-01", "label": "Fase 1", "rounds": [1, 2, 3, 4, 5, 6]}],
        "blockTargets": {"titulo": 4},
    }
    fixtures = {
        "matches": [
            {
                "id": "1",
                "round": 1,
                "home": "Botafogo",
                "away": "Cruzeiro",
                "status": "played",
                "homeScore": 2,
                "awayScore": 0,
            },
            {
                "id": "2",
                "round": 2,
                "home": "Flamengo",
                "away": "Botafogo",
                "status": "played",
                "homeScore": 1,
                "awayScore": 1,
            },
        ]
    }
    dashboard = build_dashboard(
        config,
        fixtures,
        {"goals": [], "assists": [], "sofascore": []},
        {"positions": [1, 2]},
        None,
    )
    assert dashboard["summary"]["points"] == 4
    assert dashboard["summary"]["wins"] == 1
    assert dashboard["blocks"][0]["points"] == 4
    assert dashboard["blocks"][0]["objectives"][0]["acumulado"] == 0
