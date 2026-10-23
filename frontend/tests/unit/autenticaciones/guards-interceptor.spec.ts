import { TestBed } from '@angular/core/testing';
import { HttpClient, HTTP_INTERCEPTORS } from '@angular/common/http';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { Router } from '@angular/router';
import { AuthService } from '../../../src/app/autenticaciones/auth.service';
import { authGuard } from '../../../src/app/autenticaciones/auth.guard';
import { adminGuard } from '../../../src/app/autenticaciones/admin.guard';
import { JwtInterceptor } from '../../../src/app/autenticaciones/jwt.interceptor';

describe('Guards e interceptor', () => {
  const auth = jasmine.createSpyObj<AuthService>('AuthService', ['isLoggedIn', 'canAccessAdmin', 'getToken']);
  const router = jasmine.createSpyObj<Router>('Router', ['navigate']);
  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [HttpClientTestingModule], providers: [
      { provide: AuthService, useValue: auth }, { provide: Router, useValue: router },
      { provide: HTTP_INTERCEPTORS, useClass: JwtInterceptor, multi: true }
    ] });
  });
  afterEach(() => { auth.isLoggedIn.calls.reset(); auth.canAccessAdmin.calls.reset(); auth.getToken.calls.reset(); router.navigate.calls.reset(); });

  it('guard de sesión rechaza usuario anónimo', () => {
    auth.isLoggedIn.and.returnValue(false);
    expect(TestBed.runInInjectionContext(() => authGuard({} as any, {} as any))).toBeFalse();
    expect(router.navigate).toHaveBeenCalledWith(['/auth/login']);
  });
  it('guard administrativo permite empleado y rechaza cliente', () => {
    auth.canAccessAdmin.and.returnValue(true);
    expect(TestBed.runInInjectionContext(() => adminGuard({} as any, {} as any))).toBeTrue();
    auth.canAccessAdmin.and.returnValue(false);
    expect(TestBed.runInInjectionContext(() => adminGuard({} as any, {} as any))).toBeFalse();
    expect(router.navigate).toHaveBeenCalledWith(['/productos']);
  });
  it('interceptor añade el token y no inventa uno si falta', () => {
    const client = TestBed.inject(HttpClient);
    const http = TestBed.inject(HttpTestingController);
    auth.getToken.and.returnValue('abc');
    client.get('/uno').subscribe();
    expect(http.expectOne('/uno').request.headers.get('Authorization')).toBe('Bearer abc');
    auth.getToken.and.returnValue(null);
    client.get('/dos').subscribe();
    expect(http.expectOne('/dos').request.headers.has('Authorization')).toBeFalse();
    http.verify();
  });
});
