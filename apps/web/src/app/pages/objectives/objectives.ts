import { Component, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { catchError, of } from 'rxjs';
import { ContentService } from '../../core/content.service';
import { ObjectivesBlockDetailComponent } from './objectives-block-detail/objectives-block-detail';
import { ObjectivesBlocksSummaryComponent } from './objectives-blocks-summary/objectives-blocks-summary';
import { ObjectivesChartComponent } from './objectives-chart/objectives-chart';
import { ObjectivesResumoComponent } from './objectives-resumo/objectives-resumo';

@Component({
  selector: 'app-objectives',
  imports: [
    ObjectivesResumoComponent,
    ObjectivesChartComponent,
    ObjectivesBlocksSummaryComponent,
    ObjectivesBlockDetailComponent,
  ],
  templateUrl: './objectives.html',
  styleUrl: './objectives.scss',
})
export class ObjectivesComponent {
  private readonly content = inject(ContentService);

  readonly snapshot = toSignal(
    this.content.getObjectivesSnapshot().pipe(catchError(() => of(null))),
    { initialValue: undefined },
  );

  readonly dashboard = toSignal(
    this.content.getObjectivesDashboard().pipe(catchError(() => of(null))),
    { initialValue: undefined },
  );

  objectiveEmoji(id: string): string {
    const map: Record<string, string> = {
      titulo: '🏆',
      libertadores: '⭐',
      'pre-libertadores': '🎟️',
      sulamericana: '🌎',
      permanencia: '🛡️',
    };
    return map[id] ?? '🎯';
  }
}
