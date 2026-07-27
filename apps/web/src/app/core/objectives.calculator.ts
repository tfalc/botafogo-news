import { Injectable } from '@angular/core';
import { FixtureMatch, ObjectiveResult, StandingTeam } from './models';

/** Client-side mirror of tools/compute_objectives.py for live recalculation if needed. */
@Injectable({ providedIn: 'root' })
export class ObjectivesCalculator {
  remainingForTeam(matches: FixtureMatch[], team: string): number {
    return matches.filter(
      (m) => m.status === 'scheduled' && (m.home === team || m.away === team),
    ).length;
  }

  summarize(
    teams: StandingTeam[],
    matches: FixtureMatch[],
    teamName: string,
    objectives: Array<{
      id: string;
      label: string;
      description: string;
      type: string;
      maxPosition?: number;
      minPosition?: number;
      minDangerPosition?: number;
      tone: string;
    }>,
  ): ObjectiveResult[] {
    const sorted = [...teams].sort((a, b) => a.position - b.position);
    const us = sorted.find((t) => t.name === teamName);
    if (!us) {
      return [];
    }
    const remaining = this.remainingForTeam(matches, teamName);
    const maxPoints = us.points + remaining * 3;
    const minPoints = us.points;

    return objectives.map((obj) => {
      const base: ObjectiveResult = {
        id: obj.id,
        label: obj.label,
        description: obj.description,
        tone: obj.tone,
        type: obj.type,
        currentPosition: us.position,
        currentPoints: us.points,
        remainingMatches: remaining,
        maxPoints,
        minPoints,
        stillPossible: true,
      };

      if (obj.type === 'reach_top' && obj.maxPosition) {
        const zone = sorted.filter((t) => t.position <= obj.maxPosition!);
        const cutoff = zone[zone.length - 1];
        const leader = sorted[0];
        const cutoffPoints = obj.maxPosition === 1 ? leader.points : cutoff.points;
        const gap = Math.max(0, cutoffPoints - us.points);
        const possible = maxPoints >= cutoffPoints || us.position <= obj.maxPosition;
        return {
          ...base,
          cutoffPoints,
          pointsGap: gap,
          pointsNeededOptimistic: gap,
          stillPossible: possible,
          inZone: us.position <= obj.maxPosition,
          referenceTeam: obj.maxPosition === 1 ? leader.name : cutoff.name,
        };
      }

      if (obj.type === 'reach_range' && obj.minPosition && obj.maxPosition) {
        const edge = sorted.find((t) => t.position === obj.maxPosition) ?? sorted[sorted.length - 1];
        const inZone = us.position >= obj.minPosition && us.position <= obj.maxPosition;
        const gap = us.position > obj.maxPosition ? Math.max(0, edge.points - us.points) : 0;
        return {
          ...base,
          cutoffPoints: edge.points,
          pointsGap: gap,
          pointsNeededOptimistic: gap,
          stillPossible: maxPoints >= edge.points || us.position <= obj.maxPosition,
          inZone,
          referenceTeam: edge.name,
        };
      }

      if (obj.type === 'avoid_bottom' && obj.minDangerPosition) {
        const firstDanger =
          sorted.find((t) => t.position === obj.minDangerPosition) ?? sorted[sorted.length - 1];
        const inDanger = us.position >= obj.minDangerPosition;
        const gap = inDanger ? Math.max(0, firstDanger.points + 1 - us.points) : 0;
        return {
          ...base,
          cutoffPoints: firstDanger.points,
          pointsGap: gap,
          pointsNeededOptimistic: gap,
          stillPossible: maxPoints > firstDanger.points || !inDanger,
          inZone: !inDanger,
          inDanger,
          referenceTeam: firstDanger.name,
        };
      }

      return base;
    });
  }
}
