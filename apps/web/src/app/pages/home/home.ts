import { DatePipe } from '@angular/common';
import { Component, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { catchError, combineLatest, map, of, switchMap } from 'rxjs';
import { ContentService } from '../../core/content.service';

@Component({
  selector: 'app-home',
  imports: [RouterLink, DatePipe],
  templateUrl: './home.html',
  styleUrl: './home.scss',
})
export class HomeComponent {
  private readonly content = inject(ContentService);

  readonly vm = toSignal(
    this.content.getSite().pipe(
      switchMap((site) =>
        combineLatest({
          site: of(site),
          news: this.content.getValidatedNews().pipe(map((n) => n.slice(0, 3))),
          next: this.content.getFixtures(site.primaryCompetition).pipe(
            map((fx) => this.content.nextMatch(fx, site.team) ?? null),
            catchError(() => of(null)),
          ),
        }),
      ),
    ),
    { initialValue: null },
  );
}
