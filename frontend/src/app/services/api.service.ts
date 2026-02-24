import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private apiUrl = 'http://localhost:5000';

  constructor(private http: HttpClient) { }

  toggleActuator(device: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/actuator/${device}/toggle`);
  }

  // PI2 Kontrole
  setTimer(seconds: number): Observable<any> {
    return this.http.post(`${this.apiUrl}/pi2/timer/set`, { seconds });
  }

  setAddAmount(amount: number): Observable<any> {
    return this.http.post(`${this.apiUrl}/pi2/timer/config`, { amount });
  }

  getLastReadings(): Observable<any> {
    return this.http.get(`${this.apiUrl}/api/state`);
  }

  // PI3 Kontrole
  setRgbColor(mode: number): Observable<any> {
    return this.http.post(`${this.apiUrl}/pi3/rgb`, { color: mode })
  }
}
