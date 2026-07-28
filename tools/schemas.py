"""Pydantic schemas mirroring content/ files."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class NewsStatus(str, Enum):
    draft = "draft"
    validated = "validated"


class Tone(str, Enum):
    fogao = "fogao"
    rival = "rival"


class NewsFrontmatter(BaseModel):
    title: str = Field(min_length=3)
    slug: str = Field(min_length=3, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    publishedAt: datetime
    status: NewsStatus
    tags: list[str] = Field(default_factory=list)
    tone: Tone
    sources: list[str] = Field(default_factory=list)
    summary: str = Field(min_length=10)


class StandingTeam(BaseModel):
    position: int = Field(ge=1)
    name: str
    played: int = Field(ge=0)
    won: int = Field(ge=0)
    drawn: int = Field(ge=0)
    lost: int = Field(ge=0)
    goalsFor: int = Field(ge=0)
    goalsAgainst: int = Field(ge=0)
    goalDifference: int
    points: int = Field(ge=0)
    note: str | None = None

    @field_validator("points")
    @classmethod
    def points_match_results(cls, v: int, info) -> int:
        data = info.data
        if all(k in data for k in ("won", "drawn")):
            expected = data["won"] * 3 + data["drawn"]
            if v != expected:
                raise ValueError(f"points {v} != 3*W+D ({expected})")
        return v


class StandingsFile(BaseModel):
    id: str
    name: str
    season: int
    updatedAt: datetime
    format: str | None = None
    stage: str | None = None
    teams: list[StandingTeam]


class FixtureMatch(BaseModel):
    id: str
    round: int | None = None
    date: datetime
    home: str
    away: str
    status: Literal["scheduled", "played", "postponed"]
    venue: str | None = None
    homeScore: int | None = None
    awayScore: int | None = None


class FixturesFile(BaseModel):
    competition: str
    season: int
    matches: list[FixtureMatch]


class ObjectiveDef(BaseModel):
    id: str
    label: str
    description: str
    type: Literal["reach_top", "reach_range", "avoid_bottom"]
    maxPosition: int | None = None
    minPosition: int | None = None
    minDangerPosition: int | None = None
    tone: str


class ThresholdDef(BaseModel):
    id: str
    label: str
    seasonPoints: int = Field(ge=0)
    color: str


class BlockDef(BaseModel):
    id: str
    label: str
    rounds: list[int] = Field(min_length=1)

    @field_validator("rounds")
    @classmethod
    def rounds_positive(cls, v: list[int]) -> list[int]:
        if any(r < 1 for r in v):
            raise ValueError("rounds must be >= 1")
        return v


class ObjectivesConfig(BaseModel):
    season: int
    competition: str
    team: str
    totalRounds: int = 38
    objectives: list[ObjectiveDef]
    thresholds: list[ThresholdDef] = Field(default_factory=list)
    blocks: list[BlockDef] = Field(default_factory=list)
    blockTargets: dict[str, int] = Field(default_factory=dict)


class LeaderEntry(BaseModel):
    rank: int = Field(ge=1)
    name: str
    value: float | int


class LeadersFile(BaseModel):
    updatedAt: str | None = None
    goals: list[LeaderEntry] = Field(default_factory=list)
    assists: list[LeaderEntry] = Field(default_factory=list)
    sofascore: list[LeaderEntry] = Field(default_factory=list)


class PositionByRoundFile(BaseModel):
    season: int
    competition: str
    team: str
    positions: list[int | None]


class SiteConfig(BaseModel):
    name: str
    tagline: str
    team: str
    teamFullName: str
    season: int
    activeCompetitions: list[str]
    primaryCompetition: str
    destaqueSemanal: str
    social: dict[str, str] = Field(default_factory=dict)
