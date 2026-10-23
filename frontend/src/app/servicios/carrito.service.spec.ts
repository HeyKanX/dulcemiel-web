import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { BehaviorSubject } from 'rxjs';
import { CarritoService } from './carrito.service';
import { AuthService } from '../autenticaciones/auth.service';
import { environment } from '../../environments/environment';

describe('CarritoService, auditoría de estado', () => {
  let service: CarritoService;
  let http: HttpTestingController;
  const session = new BehaviorSubject<boolean>(false);
  const auth = { isLoggedIn$: session.asObservable(), isLoggedIn: () => session.value };
  beforeEach(() => {
    session.next(false);
    TestBed.configureTestingModule({ imports: [HttpClientTestingModule], providers: [{ provide: AuthService, useValue: auth }] });
    service = TestBed.inject(CarritoService);
    http = TestBed.inject(HttpTestingController);
  });
  afterEach(() => http.verify());
  it('calcula total y limpia el carrito al cerrar sesión', () => {
    session.next(true);
    http.expectOne(`${environment.apiUrl}/carrito`).flush({ success: true, data: [
      { id: 1, producto_id: 3, cantidad: 2, precio: 10 },
      { id: 2, producto_id: 4, cantidad: 3, precio: 5 }
    ] });
    expect(service.obtenerTotal()).toBe(35);
    expect(service.obtenerCantidadItems()).toBe(2);
    session.next(false);
    expect(service.obtenerTotal()).toBe(0);
  });
  it('vacía datos locales ante error HTTP de carga', () => {
    session.next(true);
    http.expectOne(`${environment.apiUrl}/carrito`).flush('Error', { status: 500, statusText: 'Error' });
    expect(service.obtenerItemsCarrito()).toEqual([]);
  });
});
