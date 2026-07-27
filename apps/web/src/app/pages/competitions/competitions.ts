import { DatePipe } from '@angular/common';
import { Component, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { catchError, forkJoin, map, of, switchMap } from 'rxjs';
import { ContentService } from '../../core/content.service';
import { Standings } from '../../core/models';

@Component({
  selector: 'app-competitions',
  imports: [DatePipe],
  templateUrl: './competitions.html',
  styleUrl: './competitions.scss',
})
export class CompetitionsComponent {
  private readonly content = inject(ContentService);

  readonly vm = toSignal(
    this.content.getSite().pipe(
      switchMap((site) => {
        const others = site.activeCompetitions.filter((id) => id !== site.primaryCompetition);
        if (!others.length) {
          return of({ site, tables: [] as Standings[] });
        }
        return forkJoin(
          others.map((id) => this.content.getStandings(id).pipe(catchError(() => of(null)))),
        ).pipe(
          map((tables) => ({
            site,
            tables: tables.filter((t): t is Standings => !!t),
          })),
        );
      }),
    ),
    { initialValue: null },
  );
}
