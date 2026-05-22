import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { HttpErrorResponse } from '@angular/common/http';
import { Router } from '@angular/router';
import { BehaviorSubject, Observable } from 'rxjs';
import { tap } from 'rxjs/operators';
import { environment } from '../../environments/environment';

import { Usuario, LoginRequest, RegisterRequest, AuthResponse } from '../models/usuario.model';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = `${environment.apiUrl}/auth`;
  private usuarioSubject = new BehaviorSubject<Usuario | null>(null);
  private tokenSubject = new BehaviorSubject<string | null>(null);
  private isLoggedInSubject = new BehaviorSubject<boolean>(false);

  public usuario$ = this.usuarioSubject.asObservable();
  public token$ = this.tokenSubject.asObservable();
  public isLoggedIn$ = this.isLoggedInSubject.asObservable();

  constructor(private http: HttpClient, private router: Router) {
    this.verificarToken();
  }

  verificarToken(): void {
    const token = localStorage.getItem('token');
    if (token) {
      this.tokenSubject.next(token);
      this.isLoggedInSubject.next(true);
      this.obtenerPerfil().subscribe({
        error: error => {
          if (this.isAuthError(error)) {
            this.limpiarSesion(false);
          }
        }
      });
    }
  }

  login(loginRequest: LoginRequest): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${this.apiUrl}/login`, loginRequest).pipe(
      tap(response => {
        if (response.success && response.token && response.usuario) {
          localStorage.setItem('token', response.token);
          this.tokenSubject.next(response.token);
          this.usuarioSubject.next(response.usuario);
          this.isLoggedInSubject.next(true);
        }
      })
    );
  }

  register(registerRequest: RegisterRequest): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${this.apiUrl}/register`, registerRequest);
  }

  obtenerPerfil(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/perfil`).pipe(
      tap(response => {
        if (response.success && response.usuario) {
          this.usuarioSubject.next(response.usuario);
        }
      })
    );
  }

  logout(): void {
    this.limpiarSesion(true);
  }

  private limpiarSesion(redirigir: boolean): void {
    localStorage.removeItem('token');
    this.tokenSubject.next(null);
    this.usuarioSubject.next(null);
    this.isLoggedInSubject.next(false);
    if (redirigir) {
      this.router.navigate(['/auth/login']);
    }
  }

  private isAuthError(error: unknown): boolean {
    return error instanceof HttpErrorResponse && [401, 403, 404].includes(error.status);
  }

  getToken(): string | null {
    return this.tokenSubject.value;
  }

  getUsuario(): Usuario | null {
    return this.usuarioSubject.value;
  }

  isLoggedIn(): boolean {
    return this.isLoggedInSubject.value;
  }

  isAdmin(): boolean {
    const usuario = this.usuarioSubject.value;
    return usuario ? usuario.rol === 'admin' : false;
  }

  canAccessAdmin(): boolean {
    const usuario = this.usuarioSubject.value;
    return usuario ? ['admin', 'empleado'].includes(usuario.rol) : false;
  }

  obtenerUsuarios(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/usuarios`);
  }

  registrarEmpleado(data: { nombre: string; email: string; password: string; rol: 'admin' | 'empleado' }): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/empleados`, data);
  }

  actualizarUsuario(id: number, data: Partial<Usuario>): Observable<any> {
    return this.http.put<any>(`${this.apiUrl}/usuarios/${id}`, data);
  }
}
