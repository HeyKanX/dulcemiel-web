import { Component, OnInit } from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';
import { Producto } from '../../../models/producto.model';
import { ProductosService } from '../../../peticiones/productos.service';

@Component({
  selector: 'app-gestion-productos',
  template: `
    <section class="page-header">
      <div>
        <h1>Gestion de productos</h1>
        <p>Crea, edita y elimina productos del catalogo.</p>
      </div>
      <a class="btn btn-outline-secondary" routerLink="/dashboard">Dashboard</a>
    </section>

    <div class="alert alert-danger" *ngIf="error">{{ error }}</div>
    <div class="alert alert-success" *ngIf="mensaje">{{ mensaje }}</div>

    <section class="layout">
      <form class="panel" [formGroup]="form" (ngSubmit)="guardar()">
        <h2>{{ editandoId ? 'Editar producto' : 'Nuevo producto' }}</h2>

        <label class="form-label">Nombre</label>
        <input class="form-control mb-2" formControlName="nombre">

        <label class="form-label">Descripcion</label>
        <textarea class="form-control mb-2" rows="3" formControlName="descripcion"></textarea>

        <div class="row">
          <div class="col-md-6">
            <label class="form-label">Precio</label>
            <input class="form-control mb-2" type="number" min="0" step="0.01" formControlName="precio">
          </div>
          <div class="col-md-6">
            <label class="form-label">Stock</label>
            <input class="form-control mb-2" type="number" min="0" formControlName="stock">
          </div>
        </div>

        <label class="form-label">Categoria</label>
        <input class="form-control mb-2" formControlName="categoria">

        <label class="form-label">Imagen JPG, PNG o ICO</label>
        <input class="form-control mb-2" type="file" accept=".jpg,.jpeg,.png,.ico,image/jpeg,image/png,image/x-icon" (change)="seleccionarImagen($event)">

        <label class="form-label">Estado</label>
        <select class="form-select mb-3" formControlName="estado">
          <option value="disponible">Disponible</option>
          <option value="agotado">Agotado</option>
          <option value="discontinuado">Discontinuado</option>
        </select>

        <div class="d-flex gap-2">
          <button class="btn btn-primary" type="submit" [disabled]="loading">
            {{ loading ? 'Guardando...' : 'Guardar' }}
          </button>
          <button class="btn btn-outline-secondary" type="button" (click)="cancelar()">Cancelar</button>
        </div>
      </form>

      <div class="table-responsive panel">
        <table class="table table-hover align-middle">
          <thead>
            <tr>
              <th>Producto</th>
              <th>Imagen</th>
              <th>Precio</th>
              <th>Stock</th>
              <th>Estado</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr [class.low-stock-row]="esStockBajo(producto)" *ngFor="let producto of productos">
              <td>{{ producto.nombre }}</td>
              <td>
                <img class="thumb" *ngIf="producto.imagen_url" [src]="producto.imagen_url" [alt]="producto.nombre">
                <span *ngIf="!producto.imagen_url">Sin imagen</span>
              </td>
              <td>{{ producto.precio | currency:'PEN':'S/ ':'1.2-2' }}</td>
              <td>
                <strong>{{ producto.stock }}</strong>
                <span class="stock-badge" *ngIf="esStockBajo(producto)">Stock bajo</span>
              </td>
              <td>{{ producto.estado }}</td>
              <td class="text-end">
                <button class="btn btn-sm btn-outline-primary me-2" type="button" (click)="editar(producto)">Editar</button>
                <button class="btn btn-sm btn-outline-danger" type="button" (click)="eliminar(producto.id)">Eliminar</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  `,
  styleUrls: ['./gestion-productos.component.scss']
})
export class GestionProductosComponent implements OnInit {
  productos: Producto[] = [];
  editandoId: number | null = null;
  loading = false;
  error = '';
  mensaje = '';
  imagenSeleccionada: File | null = null;

  form = this.fb.nonNullable.group({
    nombre: ['', Validators.required],
    descripcion: [''],
    precio: [0, [Validators.required, Validators.min(0)]],
    stock: [0, [Validators.required, Validators.min(0)]],
    categoria: [''],
    estado: ['disponible' as Producto['estado'], Validators.required]
  });

  constructor(
    private fb: FormBuilder,
    private productosService: ProductosService
  ) {}

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.productosService.obtenerTodosProductos().subscribe({
      next: response => this.productos = response.data || [],
      error: err => this.error = err.error?.message || 'No se pudieron cargar productos.'
    });
  }

  guardar(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      this.error = this.obtenerMensajeValidacion();
      return;
    }

    this.loading = true;
    this.error = '';
    this.mensaje = '';
    const producto = this.crearFormData();
    const request = this.editandoId
      ? this.productosService.actualizarProducto(this.editandoId, producto)
      : this.productosService.crearProducto(producto);

    request.subscribe({
      next: () => {
        this.mensaje = this.editandoId ? 'Producto actualizado.' : 'Producto creado.';
        this.cancelar();
        this.cargar();
      },
      error: err => {
        this.error = err.error?.message || 'No se pudo guardar el producto.';
        this.loading = false;
      }
    });
  }

  editar(producto: Producto): void {
    this.editandoId = producto.id;
    this.form.patchValue(producto);
    this.imagenSeleccionada = null;
  }

  esStockBajo(producto: Producto): boolean {
    return producto.stock > 0 && producto.stock <= 5;
  }

  eliminar(id: number): void {
    if (!confirm('Eliminar producto?')) {
      return;
    }

    this.productosService.eliminarProducto(id).subscribe({
      next: () => {
        this.mensaje = 'Producto eliminado.';
        this.cargar();
      },
      error: err => this.error = err.error?.message || 'No se pudo eliminar el producto.'
    });
  }

  cancelar(): void {
    this.editandoId = null;
    this.loading = false;
    this.form.reset({
      nombre: '',
      descripcion: '',
      precio: 0,
      stock: 0,
      categoria: '',
      estado: 'disponible'
    });
    this.imagenSeleccionada = null;
  }

  seleccionarImagen(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0] || null;

    if (!this.validarImagen(file)) {
      input.value = '';
      this.imagenSeleccionada = null;
      return;
    }

    this.error = '';
    this.imagenSeleccionada = file;
  }

  crearFormData(): FormData {
    const raw = this.form.getRawValue();
    const data = new FormData();
    Object.entries(raw).forEach(([key, value]) => data.append(key, String(value ?? '')));
    if (this.imagenSeleccionada) {
      data.append('imagen', this.imagenSeleccionada);
    }
    return data;
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

  obtenerMensajeValidacion(): string {
    if (this.form.controls.nombre.invalid) {
      return 'El nombre del producto es requerido.';
    }
    if (this.form.controls.precio.invalid) {
      return 'El precio es requerido y debe ser mayor o igual a 0.';
    }
    if (this.form.controls.stock.invalid) {
      return 'El stock es requerido y debe ser mayor o igual a 0.';
    }
    if (this.form.controls.estado.invalid) {
      return 'Selecciona un estado valido para el producto.';
    }
    return 'Revisa los campos del producto antes de guardar.';
  }
}
