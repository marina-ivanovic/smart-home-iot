import { Routes } from '@angular/router';
import { DashboardComponent } from './components/dashboard/dashboard.component';
import { TimerControlComponent } from './components/timer-control/timer-control.component';

export const routes: Routes = [
    { path: '', redirectTo: '/dashboard', pathMatch: 'full' },
    { path: 'dashboard', component: DashboardComponent },
    { path: 'timer-control', component: TimerControlComponent },
    { path: '**', redirectTo: '/dashboard' }
];
