import { DecimalPipe } from '@angular/common';
import { Component, input } from '@angular/core';
import { DashboardBlock, ObjectivesDashboard } from '../../../core/models';

@Component({
  selector: 'app-objectives-blocks-summary',
  imports: [DecimalPipe],
  templateUrl: './objectives-blocks-summary.html',
  styleUrl: './objectives-blocks-summary.scss',
})
export class ObjectivesBlocksSummaryComponent {
  readonly dashboard = input.required<ObjectivesDashboard>();

  fillPct(block: DashboardBlock): number {
    if (!block.maxPoints || block.state === 'upcoming') return 0;
    return Math.min(100, (block.points / block.maxPoints) * 100);
  }
}
