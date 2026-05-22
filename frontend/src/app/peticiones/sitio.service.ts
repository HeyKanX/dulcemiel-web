import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class SitioService {
  private apiUrl = `${environment.apiUrl}/sitio`;

  constructor(private http: HttpClient) {}

  obtenerInicio(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/inicio`);
  }

  actualizarConfiguracion(data: FormData): Observable<any> {
    return this.http.put<any>(`${this.apiUrl}/configuracion`, data);
  }

  crearCarrusel(data: FormData): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/carrusel`, data);
  }

  actualizarCarrusel(id: number, data: FormData): Observable<any> {
    return this.http.put<any>(`${this.apiUrl}/carrusel/${id}`, data);
  }

  eliminarCarrusel(id: number): Observable<any> {
    return this.http.delete<any>(`${this.apiUrl}/carrusel/${id}`);
  }
}
