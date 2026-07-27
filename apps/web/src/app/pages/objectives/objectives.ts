import { DatePipe } from '@angular/common';
import { Component, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { catchError, of } from 'rxjs';
import { ContentService } from '../../core/content.service';

@Component({
  selector: 'app-objectives',
  imports: [DatePipe],
  templateUrl: './objectives.html',
  styleUrl: './objectives.scss',
})
export class ObjectivesComponent {
  private readonly content = inject(ContentService);

  readonly snapshot = toSignal(
    this.content.getObjectivesSnapshot().pipe(catchError(() => of(null))),
    { initialValue: undefined },
  );
}
