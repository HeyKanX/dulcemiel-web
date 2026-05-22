import { Component, OnInit } from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';
import { Usuario } from '../../../models/usuario.model';
import { AuthService } from '../../../autenticaciones/auth.service';

@Component({
  selector: 'app-gestion-usuarios',
  template: `
    <section class="page-header">
      <div>
        <h1>Usuarios y empleados</h1>
        <p>Administra clientes y registra empleados con acceso al panel.</p>
      </div>
      <a class="btn btn-outline-secondary" routerLink="/dashboard">Dashboard</a>
    </section>

    <div class="alert alert-danger" *ngIf="error">{{ error }}</div>
    <div class="alert alert-success" *ngIf="mensaje">{{ mensaje }}</div>

    <section class="layout">
      <form class="panel" [formGroup]="form" (ngSubmit)="registrarEmpleado()" *ngIf="esAdmin">
        <h2>Registrar empleado</h2>
        <input class="form-control mb-2" placeholder="Nombre" formControlName="nombre">
        <input class="form-control mb-2" placeholder="Email" type="email" formControlName="email">
        <input class="form-control mb-2" placeholder="Contrasena" type="password" formControlName="password">
        <select class="form-select mb-3" formControlName="rol">
          <option value="empleado">Empleado</option>
          <option value="admin">Administrador</option>
        </select>
        <button class="btn btn-primary" type="submit" [disabled]="form.invalid">Crear acceso</button>
      </form>

      <div class="panel table-responsive">
        <table class="table align-middle">
          <thead>
            <tr>
              <th>Nombre</th>
              <th>Email</th>
              <th>Rol</th>
              <th>Estado</th>
              <th *ngIf="esAdmin"></th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let usuario of usuarios">
              <td><input class="form-control form-control-sm" [(ngModel)]="usuario.nombre" [disabled]="!esAdmin"></td>
              <td><input class="form-control form-control-sm" [(ngModel)]="usuario.email" [disabled]="!esAdmin"></td>
              <td>
                <select class="form-select form-select-sm" [(ngModel)]="usuario.rol" [disabled]="!esAdmin">
                  <option value="usuario">Usuario</option>
                  <option value="empleado">Empleado</option>
                  <option value="admin">Administrador</option>
                </select>
              </td>
              <td>
                <select class="form-select form-select-sm" [(ngModel)]="usuario.estado" [disabled]="!esAdmin">
                  <option value="activo">Activo</option>
                  <option value="inactivo">Inactivo</option>
                </select>
              </td>
              <td class="text-end" *ngIf="esAdmin">
                <button class="btn btn-sm btn-outline-primary" type="button" (click)="guardarUsuario(usuario)">Guardar</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  `,
  styleUrls: ['./gestion-usuarios.component.scss']
})
export class GestionUsuariosComponent implements OnInit {
  usuarios: Usuario[] = [];
  error = '';
  mensaje = '';
  esAdmin = false;

  form = this.fb.nonNullable.group({
    nombre: ['', Validators.required],
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(6)]],
    rol: ['empleado' as 'admin' | 'empleado', Validators.required]
  });

  constructor(
    private fb: FormBuilder,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    this.esAdmin = this.authService.isAdmin();
    this.cargar();
  }

  cargar(): void {
    this.authService.obtenerUsuarios().subscribe({
      next: response => this.usuarios = response.data || [],
      error: err => this.error = err.error?.message || 'No se pudieron cargar usuarios.'
    });
  }

  registrarEmpleado(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.authService.registrarEmpleado(this.form.getRawValue()).subscribe({
      next: () => {
        this.mensaje = 'Empleado registrado.';
        this.form.reset({ nombre: '', email: '', password: '', rol: 'empleado' });
        this.cargar();
      },
      error: err => this.error = err.error?.message || 'No se pudo registrar el empleado.'
    });
  }

  guardarUsuario(usuario: Usuario): void {
    this.authService.actualizarUsuario(usuario.id, usuario).subscribe({
      next: () => this.mensaje = 'Usuario actualizado.',
      error: err => this.error = err.error?.message || 'No se pudo actualizar el usuario.'
    });
  }
}
