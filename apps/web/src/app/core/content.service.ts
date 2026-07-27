import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map, shareReplay } from 'rxjs';
import {
  Fixtures,
  NewsItem,
  ObjectivesDashboard,
  ObjectivesSnapshot,
  SiteConfig,
  Standings,
} from './models';

@Injectable({ providedIn: 'root' })
export class ContentService {
  private readonly http = inject(HttpClient);
  private readonly base = 'content';

  private site$?: Observable<SiteConfig>;
  private news$?: Observable<NewsItem[]>;

  getSite(): Observable<SiteConfig> {
    this.site$ ??= this.http.get<SiteConfig>(`${this.base}/site.json`).pipe(shareReplay(1));
    return this.site$;
  }

  getValidatedNews(): Observable<NewsItem[]> {
    this.news$ ??= this.http
      .get<NewsItem[]>(`${this.base}/news.validated.json`)
      .pipe(shareReplay(1));
    return this.news$;
  }

  getNewsBySlug(slug: string): Observable<NewsItem> {
    return this.http.get<NewsItem>(`${this.base}/news/${slug}.json`).pipe(
      map((item) => {
        if (item.status !== 'validated') {
          throw new Error('Notícia não validada');
        }
        return item;
      }),
    );
  }

  getStandings(competitionId: string): Observable<Standings> {
    return this.http.get<Standings>(`${this.base}/standings/${competitionId}.json`);
  }

  getFixtures(competitionId: string): Observable<Fixtures> {
    return this.http.get<Fixtures>(`${this.base}/fixtures/${competitionId}.json`);
  }

  getObjectivesSnapshot(): Observable<ObjectivesSnapshot> {
    return this.http.get<ObjectivesSnapshot>(`${this.base}/objectives/snapshot.json`);
  }

  getObjectivesDashboard(): Observable<ObjectivesDashboard> {
    return this.http.get<ObjectivesDashboard>(`${this.base}/objectives/dashboard.json`);
  }

  nextMatch(fixtures: Fixtures, team: string): Fixtures['matches'][number] | undefined {
    const now = Date.now();
    return fixtures.matches
      .filter(
        (m) =>
          m.status === 'scheduled' &&
          (m.home === team || m.away === team) &&
          new Date(m.date).getTime() >= now - 3 * 60 * 60 * 1000,
      )
      .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())[0];
  }
}
