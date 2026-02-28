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
  
  // TODO: promeniti url u zavisnosti od pi-a koji se dobije na odbrani
  cameraUrl: string = 'http://192.168.107.145:8080/?action=stream';

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
        this.alarmSystemEnabled = res.system
        this.globalAlarmActive = res.alarm
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
        measurement: record["_measurement"],
        value: record["_value"],
        name: record["name"],
        runs_on: record["runs_on"],
        time: record["_time"],
        displayValue: typeof record["_value"] === 'number' ? record["_value"].toFixed(2) : record["_value"] 
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
    this.api.setAlarm(false).subscribe(() => {alert('Alarm deactivated successfully via Web App.');})
  }

  toggleAlarmSystem() {
    this.alarmSystemEnabled = !this.alarmSystemEnabled;
    console.log(`Alarm system is now ${this.alarmSystemEnabled ? 'ENABLED' : 'DISABLED'}.`);
    this.api.setSystem(this.alarmSystemEnabled).subscribe(() => {console.log("Successfully toggled alarm system")})
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
