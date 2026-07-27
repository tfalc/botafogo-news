import { Routes } from '@angular/router';
import { ShellComponent } from './layout/shell';

export const routes: Routes = [
  {
    path: '',
    component: ShellComponent,
    children: [
      {
        path: '',
        loadComponent: () => import('./pages/home/home').then((m) => m.HomeComponent),
      },
      {
        path: 'noticias',
        loadComponent: () =>
          import('./pages/news-list/news-list').then((m) => m.NewsListComponent),
      },
      {
        path: 'noticias/:slug',
        loadComponent: () =>
          import('./pages/news-detail/news-detail').then((m) => m.NewsDetailComponent),
      },
      {
        path: 'tabela',
        loadComponent: () =>
          import('./pages/standings/standings').then((m) => m.StandingsComponent),
      },
      {
        path: 'competicoes',
        loadComponent: () =>
          import('./pages/competitions/competitions').then((m) => m.CompetitionsComponent),
      },
      {
        path: 'objetivos',
        loadComponent: () =>
          import('./pages/objectives/objectives').then((m) => m.ObjectivesComponent),
      },
    ],
  },
  { path: '**', redirectTo: '' },
];
