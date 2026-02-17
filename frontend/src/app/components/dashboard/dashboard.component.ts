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
  
  // Za PI2 kontrole
  timerValue: number = 0;
  timerAddAmount: number = 10;

    // PI3 Stanja
  rgbState: boolean = false;
  rgbColor: string = '#ffffff';
  lcdMessage: string = 'Initialization...';

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
    
    // InfluxDB vraća niz zapisa (records)
    // Svaki zapis je niz vrednosti. Moramo znati redosled kolona ili pretpostaviti standardni Influx format.
    // Obično: 
    // index 5 = _value
    // index 6 = _field (npr. "value", "measurement", "temperature")
    // index 7 = _measurement (npr. "Temperature", "Humidity")
    // index 8 = name (tag koji smo dodali: "DHT1", "DS1"...)
    // index 9 = runs_on (tag: "PI1", "PI2")
    // index 10 = simulated (tag)

    // Najbolje je da u console.log(data) vidiš tačnu strukturu prvog elementa
    // Ali evo generičke logike koja traži ključne podatke:

    for (const record of data) {
      // Filtriramo samo validne zapise
      if (!record || record.length < 5) continue;

      const measurement = record[7]; // _measurement
      const value = record[5];       // _value
      const name = record[8];        // name tag
      const runsOn = record[9];      // runs_on tag
      const time = record[4];        // _time

      parsedData.push({
        measurement: measurement,
        value: value,
        name: name,
        runs_on: runsOn,
        time: time,
        // Dodatno formatiranje za prikaz
        displayValue: typeof value === 'number' ? value.toFixed(2) : value 
      });
    }

    return parsedData;
  }


    // Helper metoda za dohvatanje vrednosti senzora po imenu i merenju
  getSensorValue(measurement: string, name: string, field: string = 'value'): any {
    const sensor = this.sensorData.find(item => 
      item.measurement === measurement && item.name === name
    );

    if (!sensor) return '--';

    // Ako tražimo specifično polje (za žiroskop npr. accel_x)
    if (field !== 'value' && sensor[field] !== undefined) {
      return sensor[field];
    }
    
    // Default value polje
    return sensor.value !== undefined ? sensor.value : sensor.displayValue;
  }
  
  // Reset Alarma (Samo vizuelno u UI, ili poziv API-ja ako postoji)
  resetAlarm() {
    this.alarmTriggered = false;
  }
  
  // Status promenljive
  timerRunning: boolean = false;
  alarmTriggered: boolean = false; // Ovo treba ažurirati iz podataka (GSG significant_movement)



  // PI1 Kontrole
  toggleLight() { this.api.toggleActuator('DL').subscribe(); }
  toggleBuzzer() { this.api.toggleActuator('DB').subscribe(); }

  // PI2 Kontrole
  setTimer() { 
    this.api.setTimer(this.timerValue).subscribe(() => alert('Timer set!')); 
  }
  
  configureAdd() { 
    this.api.setAddAmount(this.timerAddAmount).subscribe(() => alert('Configuration saved!')); 
  }

  // PI3 Metode
  toggleRGB() {
    this.rgbState = !this.rgbState;
    // Poziv API-ja: this.api.toggleRGB(this.rgbState).subscribe();
    console.log('RGB Toggle:', this.rgbState);
  }

  setRGBColor() {
    // Poziv API-ja: this.api.setRGBColor(this.rgbColor).subscribe();
    console.log('RGB Boja:', this.rgbColor);
  }
}
