import { Component } from '@angular/core';
import { ApiService } from '../../services/api.service';
import { FormsModule } from '@angular/forms'; // Dodaj u imports ako je standalone

@Component({
  selector: 'app-timer-control',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './timer-control.component.html',
  styleUrl: './timer-control.component.css'
})
export class TimerControlComponent {
  timerValue: number = 60;
  addAmount: number = 10;

  constructor(private api: ApiService) {}

  setTimer() {
    this.api.setTimer(this.timerValue).subscribe(res => {
      console.log('Timer set', res);
      alert('Tajmer postavljen!');
    });
  }

  configureAdd() {
    this.api.setAddAmount(this.addAmount).subscribe(res => {
      console.log('Config set', res);
      alert('Konfiguracija sačuvana!');
    });
  }
}
