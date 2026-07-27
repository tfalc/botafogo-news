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
  copoMeioCheio: string;
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
