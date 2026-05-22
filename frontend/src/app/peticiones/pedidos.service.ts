import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Pedido } from '../models/producto.model';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class PedidosService {
  private apiUrl = `${environment.apiUrl}/pedidos`;

  constructor(private http: HttpClient) {}

  crearPedido(data: {
    contacto_nombre: string;
    contacto_telefono: string;
    contacto_email?: string;
    direccion_entrega: string;
    distrito: string;
    referencia?: string;
    notas?: string;
  }): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}`, data);
  }

  obtenerPedidosUsuario(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}`);
  }

  obtenerDetallePedido(pedido_id: number): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/${pedido_id}`);
  }

  obtenerTodosPedidos(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/admin/todos`);
  }

  actualizarEstadoPedido(pedido_id: number, estado: string): Observable<any> {
    return this.http.put<any>(`${this.apiUrl}/${pedido_id}`, { estado });
  }
}
