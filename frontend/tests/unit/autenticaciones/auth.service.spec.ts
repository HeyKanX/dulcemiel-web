import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { Router } from '@angular/router';
import { AuthService } from '../../../src/app/autenticaciones/auth.service';
import { environment } from '../../../src/environments/environment';
import { Usuario } from '../../../src/app/models/usuario.model';

// Verificaciones unitarias relacionadas con TC-F-003, TC-F-004 y TC-F-018.
describe('AuthService, auditoría de sesión', () => {
  let service: AuthService;
  let http: HttpTestingController;
  const router = jasmine.createSpyObj<Router>('Router', ['navigate']);
  const user: Usuario = { id: 1, nombre: 'Ana', email: 'ana@audit.co', rol: 'usuario', estado: 'activo', fecha_creacion: '' };

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({ imports: [HttpClientTestingModule], providers: [{ provide: Router, useValue: router }] });
    service = TestBed.inject(AuthService);
    http = TestBed.inject(HttpTestingController);
  });
  afterEach(() => { http.verify(); localStorage.clear(); router.navigate.calls.reset(); });

  it('guarda token y sesión al iniciar, y los borra al salir', () => {
    service.login({ email: 'ana@audit.co', password: 'clave' }).subscribe();
    http.expectOne(`${environment.apiUrl}/auth/login`).flush({ success: true, token: 'abc', usuario: user });
    expect(service.isLoggedIn()).toBeTrue();
    expect(service.getToken()).toBe('abc');
    expect(localStorage.getItem('token')).toBe('abc');
    service.logout();
    expect(service.isLoggedIn()).toBeFalse();
    expect(service.getToken()).toBeNull();
    expect(router.navigate).toHaveBeenCalledWith(['/auth/login']);
  });

  it('no abre sesión ante respuesta fallida', () => {
    service.login({ email: 'ana@audit.co', password: 'mala' }).subscribe();
    http.expectOne(`${environment.apiUrl}/auth/login`).flush({ success: false, message: 'Error' });
    expect(service.isLoggedIn()).toBeFalse();
  });

  it('distingue permisos de empleado y administrador', () => {
    service.login({ email: 'ana@audit.co', password: 'clave' }).subscribe();
    http.expectOne(`${environment.apiUrl}/auth/login`).flush({ success: true, token: 'abc', usuario: { ...user, rol: 'empleado' } });
    expect(service.canAccessAdmin()).toBeTrue();
    expect(service.isAdmin()).toBeFalse();
  });
});
