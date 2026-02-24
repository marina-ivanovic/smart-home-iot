import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../services/api.service';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent implements OnInit {
  activeTab: string = 'PI1';
  sensorData: any[] = [];
  
  // PI2 Kontrole
  timerValue: number = 0;
  timerAddAmount: number = 10;
  timerRunning: boolean = false;

  // PI3 Stanja
  //rgbState: boolean = false;
  rgbColorValue: number = 8;
  lcdMessage: string = 'Initialization...';

  globalAlarmActive: boolean = false;
  alarmSystemEnabled: boolean = true;

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.fetchData();
    setInterval(() => this.fetchData(), 2000);
  }

  setTab(tab: string) {
    this.activeTab = tab;
  }

  fetchData() {
    this.api.getLastReadings().subscribe((res: any) => {
      if (res.status === 'success') {
        this.sensorData = this.parseInfluxData(res.data);
      }
    });
  }

  get filteredData() {
    return this.sensorData.filter(item => item.runs_on === this.activeTab);
  }

  parseInfluxData(data: any[]): any[] {
    const parsedData = [];
    for (const record of data) {
      if (!record || record.length < 5) continue;
      parsedData.push({
        measurement: record[7],
        value: record[5],
        name: record[8],
        runs_on: record[9],
        time: record[4],
        displayValue: typeof record[5] === 'number' ? record[5].toFixed(2) : record[5] 
      });
    }
    return parsedData;
  }

  getSensorValue(measurement: string, name: string, field: string = 'value'): any {
    const sensor = this.sensorData.find(item => item.measurement === measurement && item.name === name);
    if (!sensor) return '--';
    if (field !== 'value' && sensor[field] !== undefined) return sensor[field];
    return sensor.value !== undefined ? sensor.value : sensor.displayValue;
  }

  // PI1 Kontrole
  toggleLight() { this.api.toggleActuator('DL').subscribe(); }
  toggleBuzzer() { this.api.toggleActuator('DB').subscribe(); }

  // PI2 Kontrole
  setTimer() { this.api.setTimer(this.timerValue).subscribe(() => alert('Timer set!')); }
  configureAdd() { this.api.setAddAmount(this.timerAddAmount).subscribe(() => alert('Configuration saved!')); }

  // PI3 Metode
  //toggleRGB() { this.rgbState = !this.rgbState; }
  setRGBColor() { console.log('RGB Color:', this.rgbColorValue); this.api.setRgbColor(this.rgbColorValue).subscribe(() => alert('Color changed!')) }


  deactivateGlobalAlarm() {
    this.globalAlarmActive = false;
    alert('Alarm deactivated successfully via Web App.');
  }

  toggleAlarmSystem() {
    this.alarmSystemEnabled = !this.alarmSystemEnabled;
    console.log(`Alarm system is now ${this.alarmSystemEnabled ? 'ENABLED' : 'DISABLED'}.`);
  }

  triggerManualScenario(scenario: string) {
    console.log('Triggering scenario locally:', scenario);
    
    if(this.alarmSystemEnabled) {
      this.globalAlarmActive = true;
    } else {
      alert(`Scenario "${scenario}" executed locally, but alarm system is DISABLED for testing.`);
    }
  }
}
