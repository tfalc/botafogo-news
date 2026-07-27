import { DatePipe } from '@angular/common';
import { Component, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { catchError, map, of, switchMap } from 'rxjs';
import { ContentService } from '../../core/content.service';

@Component({
  selector: 'app-standings',
  imports: [DatePipe],
  templateUrl: './standings.html',
  styleUrl: './standings.scss',
})
export class StandingsComponent {
  private readonly content = inject(ContentService);

  readonly vm = toSignal(
    this.content.getSite().pipe(
      switchMap((site) =>
        this.content.getStandings(site.primaryCompetition).pipe(
          map((standings) => ({ site, standings })),
          catchError(() => of(null)),
        ),
      ),
    ),
    { initialValue: undefined },
  );
}
