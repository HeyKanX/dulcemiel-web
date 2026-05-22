import { Component } from '@angular/core';
import { AbstractControl, FormBuilder, ValidationErrors, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../../autenticaciones/auth.service';

function passwordMatch(control: AbstractControl): ValidationErrors | null {
  const password = control.get('password')?.value;
  const passwordConfirm = control.get('passwordConfirm')?.value;
  return password && passwordConfirm && password !== passwordConfirm ? { passwordMismatch: true } : null;
}

@Component({
  selector: 'app-register',
  template: `
    <section class="auth-shell fade-in">
      <div class="auth-panel">
        <h1>Crear cuenta</h1>
        <p>Registrate para guardar tu carrito y hacer pedidos.</p>

        <div class="alert alert-danger" *ngIf="error">{{ error }}</div>
        <div class="alert alert-success" *ngIf="success">{{ success }}</div>

        <form [formGroup]="form" (ngSubmit)="submit()">
          <div class="mb-3">
            <label class="form-label">Nombre</label>
            <input class="form-control" formControlName="nombre" autocomplete="name">
          </div>

          <div class="mb-3">
            <label class="form-label">Email</label>
            <input class="form-control" type="email" formControlName="email" autocomplete="email">
          </div>

          <div class="mb-3">
            <label class="form-label">Contrasena</label>
            <input class="form-control" type="password" formControlName="password" autocomplete="new-password">
          </div>

          <div class="mb-3">
            <label class="form-label">Confirmar contrasena</label>
            <input class="form-control" type="password" formControlName="passwordConfirm" autocomplete="new-password">
            <small class="text-danger" *ngIf="form.touched && form.hasError('passwordMismatch')">
              Las contrasenas no coinciden.
            </small>
          </div>

          <button class="btn btn-primary w-100" type="submit" [disabled]="form.invalid || loading">
            {{ loading ? 'Creando...' : 'Registrarme' }}
          </button>
        </form>

        <a class="d-block mt-3" routerLink="/auth/login">Ya tengo una cuenta</a>
      </div>
    </section>
  `,
  styleUrls: ['./register.component.scss']
})
export class RegisterComponent {
  loading = false;
  error = '';
  success = '';

  form = this.fb.nonNullable.group({
    nombre: ['', [Validators.required, Validators.minLength(2)]],
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(6)]],
    passwordConfirm: ['', Validators.required]
  }, { validators: passwordMatch });

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
    this.success = '';

    this.authService.register(this.form.getRawValue()).subscribe({
      next: () => {
        this.success = 'Cuenta creada. Ahora puedes iniciar sesion.';
        setTimeout(() => this.router.navigate(['/auth/login']), 900);
      },
      error: (err) => {
        this.error = err.error?.message || 'No se pudo registrar el usuario.';
        this.loading = false;
      }
    });
  }
}
