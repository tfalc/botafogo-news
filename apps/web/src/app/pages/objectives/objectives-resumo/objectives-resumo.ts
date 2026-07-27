import { DecimalPipe } from '@angular/common';
import { Component, input } from '@angular/core';
import { ObjectivesDashboard } from '../../../core/models';

@Component({
  selector: 'app-objectives-resumo',
  imports: [DecimalPipe],
  templateUrl: './objectives-resumo.html',
  styleUrl: './objectives-resumo.scss',
})
export class ObjectivesResumoComponent {
  readonly dashboard = input.required<ObjectivesDashboard>();
}
