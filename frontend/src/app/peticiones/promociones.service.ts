import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { Promocion } from '../models/producto.model';

@Injectable({
  providedIn: 'root'
})
export class PromocionesService {
  private apiUrl = `${environment.apiUrl}/promociones`;

  constructor(private http: HttpClient) {}

  obtenerPromociones(): Observable<any> {
    return this.http.get<any>(this.apiUrl);
  }

  crearPromocion(data: Partial<Promocion>): Observable<any> {
    return this.http.post<any>(this.apiUrl, data);
  }

  actualizarPromocion(id: number, data: Partial<Promocion>): Observable<any> {
    return this.http.put<any>(`${this.apiUrl}/${id}`, data);
  }

  eliminarPromocion(id: number): Observable<any> {
    return this.http.delete<any>(`${this.apiUrl}/${id}`);
  }
}
