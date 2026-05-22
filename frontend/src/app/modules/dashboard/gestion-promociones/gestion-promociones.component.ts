import { Component, OnInit } from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';
import { Promocion } from '../../../models/producto.model';
import { PromocionesService } from '../../../peticiones/promociones.service';

@Component({
  selector: 'app-gestion-promociones',
  template: `
    <section class="page-header">
      <div>
        <h1>Promociones</h1>
        <p>Crea y modifica promociones visibles en la pagina principal.</p>
      </div>
      <a class="btn btn-outline-secondary" routerLink="/dashboard">Dashboard</a>
    </section>

    <div class="alert alert-danger" *ngIf="error">{{ error }}</div>
    <div class="alert alert-success" *ngIf="mensaje">{{ mensaje }}</div>

    <section class="layout">
      <form class="panel" [formGroup]="form" (ngSubmit)="guardar()">
        <h2>{{ editandoId ? 'Editar promocion' : 'Nueva promocion' }}</h2>
        <label class="form-label">Titulo</label>
        <input class="form-control mb-2" formControlName="titulo">

        <label class="form-label">Descripcion</label>
        <textarea class="form-control mb-2" rows="3" formControlName="descripcion"></textarea>

        <label class="form-label">Descuento %</label>
        <input class="form-control mb-2" type="number" min="0" max="100" step="0.01" formControlName="descuento_porcentaje">

        <label class="form-label">Inicio</label>
        <input class="form-control mb-2" type="date" formControlName="fecha_inicio">

        <label class="form-label">Fin</label>
        <input class="form-control mb-2" type="date" formControlName="fecha_fin">

        <label class="form-check mb-3">
          <input class="form-check-input" type="checkbox" formControlName="activo">
          <span class="form-check-label">Activa</span>
        </label>

        <div class="d-flex gap-2">
          <button class="btn btn-primary" type="submit" [disabled]="form.invalid">Guardar</button>
          <button class="btn btn-outline-secondary" type="button" (click)="cancelar()">Cancelar</button>
        </div>
      </form>

      <div class="panel table-responsive">
        <table class="table align-middle">
          <thead>
            <tr>
              <th>Titulo</th>
              <th>Descuento</th>
              <th>Vigencia</th>
              <th>Estado</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let promo of promociones">
              <td>{{ promo.titulo }}</td>
              <td>{{ promo.descuento_porcentaje }}%</td>
              <td>{{ promo.fecha_inicio | date }} - {{ promo.fecha_fin ? (promo.fecha_fin | date) : 'Sin fin' }}</td>
              <td>{{ promo.activo ? 'Activa' : 'Inactiva' }}</td>
              <td class="text-end">
                <button class="btn btn-sm btn-outline-primary me-2" type="button" (click)="editar(promo)">Editar</button>
                <button class="btn btn-sm btn-outline-danger" type="button" (click)="eliminar(promo.id)">Eliminar</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  `,
  styleUrls: ['./gestion-promociones.component.scss']
})
export class GestionPromocionesComponent implements OnInit {
  promociones: Promocion[] = [];
  editandoId: number | null = null;
  error = '';
  mensaje = '';

  form = this.fb.nonNullable.group({
    titulo: ['', Validators.required],
    descripcion: [''],
    descuento_porcentaje: [0, [Validators.required, Validators.min(0), Validators.max(100)]],
    fecha_inicio: ['', Validators.required],
    fecha_fin: [''],
    activo: [true]
  });

  constructor(
    private fb: FormBuilder,
    private promocionesService: PromocionesService
  ) {}

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.promocionesService.obtenerPromociones().subscribe({
      next: response => this.promociones = response.data || [],
      error: err => this.error = err.error?.message || 'No se pudieron cargar promociones.'
    });
  }

  guardar(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const request = this.editandoId
      ? this.promocionesService.actualizarPromocion(this.editandoId, this.form.getRawValue())
      : this.promocionesService.crearPromocion(this.form.getRawValue());

    request.subscribe({
      next: () => {
        this.mensaje = this.editandoId ? 'Promocion actualizada.' : 'Promocion creada.';
        this.cancelar();
        this.cargar();
      },
      error: err => this.error = err.error?.message || 'No se pudo guardar la promocion.'
    });
  }

  editar(promo: Promocion): void {
    this.editandoId = promo.id;
    this.form.patchValue({
      titulo: promo.titulo,
      descripcion: promo.descripcion || '',
      descuento_porcentaje: promo.descuento_porcentaje,
      activo: promo.activo,
      fecha_inicio: promo.fecha_inicio?.substring(0, 10),
      fecha_fin: promo.fecha_fin?.substring(0, 10) || ''
    });
  }

  eliminar(id: number): void {
    if (!confirm('Eliminar promocion?')) {
      return;
    }
    this.promocionesService.eliminarPromocion(id).subscribe({
      next: () => {
        this.mensaje = 'Promocion eliminada.';
        this.cargar();
      },
      error: err => this.error = err.error?.message || 'No se pudo eliminar la promocion.'
    });
  }

  cancelar(): void {
    this.editandoId = null;
    this.form.reset({
      titulo: '',
      descripcion: '',
      descuento_porcentaje: 0,
      fecha_inicio: '',
      fecha_fin: '',
      activo: true
    });
  }
}
