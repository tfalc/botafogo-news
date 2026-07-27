import { DatePipe } from '@angular/common';
import { Component, computed, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { DomSanitizer } from '@angular/platform-browser';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { marked } from 'marked';
import { catchError, of, switchMap } from 'rxjs';
import { ContentService } from '../../core/content.service';

@Component({
  selector: 'app-news-detail',
  imports: [RouterLink, DatePipe],
  templateUrl: './news-detail.html',
  styleUrl: './news-detail.scss',
})
export class NewsDetailComponent {
  private readonly content = inject(ContentService);
  private readonly route = inject(ActivatedRoute);
  private readonly sanitizer = inject(DomSanitizer);

  readonly article = toSignal(
    this.route.paramMap.pipe(
      switchMap((params) => {
        const slug = params.get('slug');
        if (!slug) {
          return of(null);
        }
        return this.content.getNewsBySlug(slug).pipe(catchError(() => of(null)));
      }),
    ),
    { initialValue: undefined },
  );

  readonly html = computed(() => {
    const body = this.article()?.body;
    if (!body) {
      return this.sanitizer.bypassSecurityTrustHtml('');
    }
    const parsed = marked.parse(body, { async: false }) as string;
    return this.sanitizer.bypassSecurityTrustHtml(parsed);
  });
}
