import { DecimalPipe } from '@angular/common';
import { Component, input } from '@angular/core';
import { DashboardBlock, DashboardMatch } from '../../../core/models';

@Component({
  selector: 'app-objectives-block-detail',
  imports: [DecimalPipe],
  templateUrl: './objectives-block-detail.html',
  styleUrl: './objectives-block-detail.scss',
})
export class ObjectivesBlockDetailComponent {
  readonly block = input.required<DashboardBlock>();

  scoreText(match: DashboardMatch): string {
    if (match.status !== 'played' || match.homeScore == null || match.awayScore == null) {
      return '—';
    }
    return `${match.homeScore}–${match.awayScore}`;
  }
}
