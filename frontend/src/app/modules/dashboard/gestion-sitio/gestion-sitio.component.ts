import { Component, OnInit } from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';
import { CarruselItem } from '../../../models/producto.model';
import { SitioService } from '../../../peticiones/sitio.service';

@Component({
  selector: 'app-gestion-sitio',
  template: `
    <section class="page-header">
      <div>
        <h1>Inicio y marca</h1>
        <p>Edita nombre, descripcion, logo, mision, vision y carrusel.</p>
      </div>
      <a class="btn btn-outline-secondary" routerLink="/dashboard">Dashboard</a>
    </section>

    <div class="alert alert-danger" *ngIf="error">{{ error }}</div>
    <div class="alert alert-success" *ngIf="mensaje">{{ mensaje }}</div>

    <section class="layout">
      <form class="panel" [formGroup]="configForm" (ngSubmit)="guardarConfig()">
        <h2>Configuracion principal</h2>
        <label class="form-label">Nombre empresa</label>
        <input class="form-control mb-2" formControlName="nombre_empresa">
        <label class="form-label">Descripcion inicio</label>
        <textarea class="form-control mb-2" rows="3" formControlName="descripcion_inicio"></textarea>
        <label class="form-label">Mision</label>
        <textarea class="form-control mb-2" rows="3" formControlName="mision"></textarea>
        <label class="form-label">Vision</label>
        <textarea class="form-control mb-2" rows="3" formControlName="vision"></textarea>
        <label class="form-label">Logo JPG, PNG o ICO</label>
        <input class="form-control mb-3" type="file" accept=".jpg,.jpeg,.png,.ico,image/jpeg,image/png,image/x-icon" (change)="seleccionarLogo($event)">
        <button class="btn btn-primary" type="submit">Guardar configuracion</button>
      </form>

      <form class="panel" [formGroup]="slideForm" (ngSubmit)="guardarSlide()">
        <h2>{{ editandoId ? 'Editar imagen' : 'Nueva imagen de carrusel' }}</h2>
        <input class="form-control mb-2" placeholder="Titulo" formControlName="titulo">
        <textarea class="form-control mb-2" rows="3" placeholder="Descripcion" formControlName="descripcion"></textarea>
        <input class="form-control mb-2" type="number" placeholder="Orden" formControlName="orden">
        <label class="form-check mb-2">
          <input class="form-check-input" type="checkbox" formControlName="activo">
          <span class="form-check-label">Activa</span>
        </label>
        <input class="form-control mb-3" type="file" accept=".jpg,.jpeg,.png,.ico,image/jpeg,image/png,image/x-icon" (change)="seleccionarImagen($event)">
        <div class="d-flex gap-2">
          <button class="btn btn-primary" type="submit">Guardar</button>
          <button class="btn btn-outline-secondary" type="button" (click)="cancelarSlide()">Cancelar</button>
        </div>
      </form>
    </section>

    <section class="panel slides">
      <article *ngFor="let item of carrusel">
        <img *ngIf="item.imagen_url" [src]="item.imagen_url" [alt]="item.titulo">
        <div>
          <strong>{{ item.titulo }}</strong>
          <span>{{ item.descripcion }}</span>
        </div>
        <button class="btn btn-sm btn-outline-primary" type="button" (click)="editarSlide(item)">Editar</button>
        <button class="btn btn-sm btn-outline-danger" type="button" (click)="eliminarSlide(item.id)">Eliminar</button>
      </article>
    </section>
  `,
  styleUrls: ['./gestion-sitio.component.scss']
})
export class GestionSitioComponent implements OnInit {
  carrusel: CarruselItem[] = [];
  logo: File | null = null;
  imagenSlide: File | null = null;
  editandoId: number | null = null;
  error = '';
  mensaje = '';

  configForm = this.fb.nonNullable.group({
    nombre_empresa: ['', Validators.required],
    descripcion_inicio: ['', Validators.required],
    mision: ['', Validators.required],
    vision: ['', Validators.required]
  });

  slideForm = this.fb.nonNullable.group({
    titulo: ['', Validators.required],
    descripcion: [''],
    orden: [0],
    activo: [true]
  });

  constructor(
    private fb: FormBuilder,
    private sitioService: SitioService
  ) {}

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.sitioService.obtenerInicio().subscribe({
      next: response => {
        this.configForm.patchValue(response.configuracion);
        this.carrusel = response.carrusel || [];
      },
      error: err => this.error = err.error?.message || 'No se pudo cargar la configuracion.'
    });
  }

  guardarConfig(): void {
    if (this.configForm.invalid) {
      this.configForm.markAllAsTouched();
      this.error = this.obtenerMensajeConfig();
      return;
    }

    const data = new FormData();
    Object.entries(this.configForm.getRawValue()).forEach(([key, value]) => data.append(key, String(value)));
    if (this.logo) {
      data.append('logo', this.logo);
    }
    this.sitioService.actualizarConfiguracion(data).subscribe({
      next: () => {
        this.mensaje = 'Configuracion actualizada.';
        this.logo = null;
        this.cargar();
      },
      error: err => this.error = err.error?.message || 'No se pudo guardar la configuracion.'
    });
  }

  guardarSlide(): void {
    if (this.slideForm.invalid) {
      this.slideForm.markAllAsTouched();
      this.error = this.slideForm.controls.titulo.invalid
        ? 'El titulo del carrusel es requerido.'
        : 'Revisa los campos del carrusel antes de guardar.';
      return;
    }

    if (!this.editandoId && !this.imagenSlide) {
      this.error = 'Debes seleccionar una imagen JPG, PNG o ICO para crear el carrusel.';
      return;
    }

    const data = new FormData();
    Object.entries(this.slideForm.getRawValue()).forEach(([key, value]) => data.append(key, String(value)));
    if (this.imagenSlide) {
      data.append('imagen', this.imagenSlide);
    }

    const request = this.editandoId
      ? this.sitioService.actualizarCarrusel(this.editandoId, data)
      : this.sitioService.crearCarrusel(data);

    request.subscribe({
      next: () => {
        this.mensaje = 'Carrusel actualizado.';
        this.cancelarSlide();
        this.cargar();
      },
      error: err => this.error = err.error?.message || 'No se pudo guardar el carrusel.'
    });
  }

  seleccionarLogo(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0] || null;

    if (!this.validarImagen(file)) {
      input.value = '';
      this.logo = null;
      return;
    }

    this.error = '';
    this.logo = file;
  }

  seleccionarImagen(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0] || null;

    if (!this.validarImagen(file)) {
      input.value = '';
      this.imagenSlide = null;
      return;
    }

    this.error = '';
    this.imagenSlide = file;
  }

  editarSlide(item: CarruselItem): void {
    this.editandoId = item.id;
    this.imagenSlide = null;
    this.slideForm.patchValue({
      titulo: item.titulo,
      descripcion: item.descripcion || '',
      orden: item.orden,
      activo: item.activo
    });
  }

  eliminarSlide(id: number): void {
    if (!confirm('Eliminar imagen del carrusel?')) {
      return;
    }
    this.sitioService.eliminarCarrusel(id).subscribe({
      next: () => {
        this.mensaje = 'Imagen eliminada.';
        this.cargar();
      },
      error: err => this.error = err.error?.message || 'No se pudo eliminar la imagen.'
    });
  }

  cancelarSlide(): void {
    this.editandoId = null;
    this.imagenSlide = null;
    this.slideForm.reset({ titulo: '', descripcion: '', orden: 0, activo: true });
  }

  validarImagen(file: File | null): boolean {
    if (!file) {
      return true;
    }

    const tiposPermitidos = ['image/jpeg', 'image/png', 'image/x-icon', 'image/vnd.microsoft.icon'];
    if (!tiposPermitidos.includes(file.type)) {
      this.error = 'Formato no permitido. Sube una imagen JPG, PNG o ICO.';
      return false;
    }

    if (file.size > 5 * 1024 * 1024) {
      this.error = 'La imagen supera el limite permitido de 5 MB.';
      return false;
    }

    return true;
  }

  obtenerMensajeConfig(): string {
    if (this.configForm.controls.nombre_empresa.invalid) {
      return 'El nombre de la empresa es requerido.';
    }
    if (this.configForm.controls.descripcion_inicio.invalid) {
      return 'La descripcion de inicio es requerida.';
    }
    if (this.configForm.controls.mision.invalid) {
      return 'La mision es requerida.';
    }
    if (this.configForm.controls.vision.invalid) {
      return 'La vision es requerida.';
    }
    return 'Revisa la configuracion principal antes de guardar.';
  }
}
