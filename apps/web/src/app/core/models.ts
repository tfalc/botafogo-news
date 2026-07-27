export type NewsStatus = 'draft' | 'validated';
export type Tone = 'fogao' | 'rival';

export interface SiteConfig {
  name: string;
  tagline: string;
  team: string;
  teamFullName: string;
  season: number;
  activeCompetitions: string[];
  primaryCompetition: string;
  destaqueSemanal: string;
  social?: Record<string, string>;
}

export interface NewsItem {
  title: string;
  slug: string;
  publishedAt: string;
  status: NewsStatus;
  tags: string[];
  tone: Tone;
  sources: string[];
  summary: string;
  body?: string;
}

export interface StandingTeam {
  position: number;
  name: string;
  played: number;
  won: number;
  drawn: number;
  lost: number;
  goalsFor: number;
  goalsAgainst: number;
  goalDifference: number;
  points: number;
  note?: string;
}

export interface Standings {
  id: string;
  name: string;
  season: number;
  updatedAt: string;
  format?: string;
  stage?: string;
  teams: StandingTeam[];
}

export interface FixtureMatch {
  id: string;
  round?: number;
  date: string;
  home: string;
  away: string;
  status: 'scheduled' | 'played' | 'postponed';
  venue?: string;
  homeScore?: number;
  awayScore?: number;
}

export interface Fixtures {
  competition: string;
  season: number;
  matches: FixtureMatch[];
}

export interface ObjectiveResult {
  id: string;
  label: string;
  description: string;
  tone: string;
  type: string;
  currentPosition: number;
  currentPoints: number;
  remainingMatches: number;
  maxPoints: number;
  minPoints: number;
  cutoffPoints?: number;
  pointsGap?: number;
  pointsNeededOptimistic?: number;
  stillPossible: boolean;
  inZone?: boolean;
  inDanger?: boolean;
  referenceTeam?: string;
  safetyLinePoints?: number;
}

export interface ObjectivesSnapshot {
  team: string;
  competition: string;
  season: number;
  generatedAt: string;
  summary: {
    position: number;
    points: number;
    remainingMatches: number;
    maxPoints: number;
  };
  objectives: ObjectiveResult[];
}

export interface LeaderEntry {
  rank: number;
  name: string;
  value: number;
}

export interface DashboardMatch {
  round: number;
  home: string;
  away: string;
  homeAbbrev: string;
  awayAbbrev: string;
  homeScore: number | null;
  awayScore: number | null;
  status: string;
  result: 'W' | 'L' | 'D' | null;
  isHome: boolean | null;
}

export interface DashboardBlockObjective {
  id: string;
  label: string;
  color: string;
  meta: number;
  acumulado: number;
  metaPct: number;
  pointsPct: number;
}

export interface DashboardBlock {
  id: string;
  label: string;
  rounds: number[];
  points: number;
  maxPoints: number;
  state: 'upcoming' | 'partial' | 'complete';
  active: boolean;
  matches: DashboardMatch[];
  objectives: DashboardBlockObjective[];
}

export interface SeasonBarMarker {
  id: string;
  label: string;
  points: number;
  color: string;
  pctPoints: number;
  pctAproveitamento: number;
}

export interface ObjectivesDashboard {
  team: string;
  competition: string;
  season: number;
  generatedAt: string;
  summary: {
    round: number;
    totalRounds: number;
    position: number;
    points: number;
    wins: number;
    goals: number;
    aproveitamento: number;
    played: number;
  };
  leaders: {
    goals: LeaderEntry[];
    assists: LeaderEntry[];
    sofascore: LeaderEntry[];
  };
  positionByRound: Array<number | null>;
  seasonBars: {
    points: { value: number; max: number; label: string };
    aproveitamento: { value: number; max: number; label: string };
    markers: SeasonBarMarker[];
  };
  thresholds: Array<{ id: string; label: string; seasonPoints: number; color: string }>;
  blocks: DashboardBlock[];
}
