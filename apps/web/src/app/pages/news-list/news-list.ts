import { DatePipe } from '@angular/common';
import { Component, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { ContentService } from '../../core/content.service';

@Component({
  selector: 'app-news-list',
  imports: [RouterLink, DatePipe],
  templateUrl: './news-list.html',
  styleUrl: './news-list.scss',
})
export class NewsListComponent {
  private readonly content = inject(ContentService);
  readonly news = toSignal(this.content.getValidatedNews(), { initialValue: [] });
}
