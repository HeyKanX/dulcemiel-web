import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable } from 'rxjs';
import { tap } from 'rxjs/operators';
import { CarritoItem } from '../models/producto.model';
import { environment } from '../../environments/environment';
import { AuthService } from '../autenticaciones/auth.service';

@Injectable({
  providedIn: 'root'
})
export class CarritoService {
  private apiUrl = `${environment.apiUrl}/carrito`;
  private itemsCarritoSubject = new BehaviorSubject<CarritoItem[]>([]);
  public itemsCarrito$ = this.itemsCarritoSubject.asObservable();

  constructor(private http: HttpClient, private authService: AuthService) {
    this.authService.isLoggedIn$.subscribe(isLoggedIn => {
      if (isLoggedIn) {
        this.cargarCarrito();
      } else {
        this.itemsCarritoSubject.next([]);
      }
    });
  }

  cargarCarrito(): void {
    if (!this.authService.isLoggedIn()) {
      this.itemsCarritoSubject.next([]);
      return;
    }

    this.obtenerCarrito().subscribe({
      error: () => this.itemsCarritoSubject.next([])
    });
  }

  obtenerCarrito(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}`).pipe(
      tap(response => {
        if (response.success) {
          this.itemsCarritoSubject.next(response.data);
        }
      })
    );
  }

  agregarProducto(producto_id: number, cantidad: number): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/agregar`, { producto_id, cantidad }).pipe(
      tap(() => this.cargarCarrito())
    );
  }

  actualizarCarrito(carrito_id: number, cantidad: number): Observable<any> {
    return this.http.put<any>(`${this.apiUrl}/actualizar`, { carrito_id, cantidad }).pipe(
      tap(() => this.cargarCarrito())
    );
  }

  eliminarDelCarrito(carrito_id: number): Observable<any> {
    return this.http.delete<any>(`${this.apiUrl}/${carrito_id}`).pipe(
      tap(() => this.cargarCarrito())
    );
  }

  vaciarCarrito(): Observable<any> {
    return this.http.delete<any>(`${this.apiUrl}`).pipe(
      tap(() => this.cargarCarrito())
    );
  }

  obtenerItemsCarrito(): CarritoItem[] {
    return this.itemsCarritoSubject.value;
  }

  obtenerCantidadItems(): number {
    return this.itemsCarritoSubject.value.length;
  }

  obtenerTotal(): number {
    return this.itemsCarritoSubject.value.reduce((sum, item) => sum + (item.cantidad * item.precio), 0);
  }
}
