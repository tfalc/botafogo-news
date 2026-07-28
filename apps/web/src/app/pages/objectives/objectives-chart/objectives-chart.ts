import { Component, computed, input } from '@angular/core';
import { ObjectivesDashboard } from '../../../core/models';

@Component({
  selector: 'app-objectives-chart',
  templateUrl: './objectives-chart.html',
  styleUrl: './objectives-chart.scss',
})
export class ObjectivesChartComponent {
  readonly dashboard = input.required<ObjectivesDashboard>();

  readonly chart = computed(() => {
    const dash = this.dashboard();
    const positions = dash.positionByRound;
    const total = dash.summary.totalRounds || 38;
    const width = 760;
    const height = 240;
    const padL = 40;
    const padR = 14;
    const padT = 18;
    const padB = 30;
    const plotW = width - padL - padR;
    const plotH = height - padT - padB;

    const xAt = (round: number) => padL + ((round - 1) / Math.max(1, total - 1)) * plotW;
    const yAt = (pos: number) => padT + ((pos - 1) / 19) * plotH;

    const pts: Array<{ x: number; y: number }> = [];
    positions.forEach((pos, i) => {
      if (pos == null) return;
      pts.push({ x: xAt(i + 1), y: yAt(pos) });
    });

    const points = pts.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ');
    let area = '';
    if (pts.length) {
      const first = pts[0];
      const last = pts[pts.length - 1];
      const base = padT + plotH;
      area = [
        `${first.x.toFixed(1)},${base}`,
        ...pts.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`),
        `${last.x.toFixed(1)},${base}`,
      ].join(' ');
    }

    const xTicks = [1, 5, 10, 15, 20, 25, 30, 35, 38].filter((r) => r <= total);
    const yTicks = [1, 5, 10, 15, 20];

    return {
      width,
      height,
      padL,
      padT,
      padB,
      plotW,
      plotH,
      points,
      area,
      xTicks,
      yTicks,
      xAt,
      yAt,
    };
  });

  pointsFillPct(): number {
    const bar = this.dashboard().seasonBars.points;
    if (!bar.max) return 0;
    return Math.min(100, (bar.value / bar.max) * 100);
  }

  aproveitamentoFillPct(): number {
    return Math.min(100, this.dashboard().seasonBars.aproveitamento.value);
  }

  markerSummary(): string {
    return this.dashboard()
      .seasonBars.markers.map((m) => `${m.label} ${m.points} pts`)
      .join(', ');
  }
}
