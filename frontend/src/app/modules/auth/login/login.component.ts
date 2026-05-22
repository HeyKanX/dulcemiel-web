import { Component } from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../../autenticaciones/auth.service';

@Component({
  selector: 'app-login',
  template: `
    <section class="auth-shell fade-in">
      <div class="auth-panel">
        <h1>Iniciar sesion</h1>
        <p>Accede para comprar, revisar tu carrito y seguir tus pedidos.</p>

        <div class="alert alert-danger" *ngIf="error">{{ error }}</div>

        <form [formGroup]="form" (ngSubmit)="submit()">
          <div class="mb-3">
            <label class="form-label">Email</label>
            <input class="form-control" type="email" formControlName="email" autocomplete="email">
            <small class="text-danger" *ngIf="form.controls.email.touched && form.controls.email.invalid">
              Ingresa un email valido.
            </small>
          </div>

          <div class="mb-3">
            <label class="form-label">Contrasena</label>
            <input class="form-control" type="password" formControlName="password" autocomplete="current-password">
            <small class="text-danger" *ngIf="form.controls.password.touched && form.controls.password.invalid">
              La contrasena es requerida.
            </small>
          </div>

          <button class="btn btn-primary w-100" type="submit" [disabled]="form.invalid || loading">
            {{ loading ? 'Ingresando...' : 'Ingresar' }}
          </button>
        </form>

        <a class="d-block mt-3" routerLink="/auth/register">Crear una cuenta</a>
      </div>
    </section>
  `,
  styleUrls: ['./login.component.scss']
})
export class LoginComponent {
  loading = false;
  error = '';

  form = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', Validators.required]
  });

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private router: Router
  ) {}

  submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.loading = true;
    this.error = '';

    this.authService.login(this.form.getRawValue()).subscribe({
      next: () => this.router.navigate([this.authService.canAccessAdmin() ? '/dashboard' : '/productos']),
      error: (err) => {
        this.error = err.error?.message || 'No se pudo iniciar sesion.';
        this.loading = false;
      }
    });
  }
}
