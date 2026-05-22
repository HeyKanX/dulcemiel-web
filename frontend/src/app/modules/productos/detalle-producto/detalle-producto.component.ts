import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Producto } from '../../../models/producto.model';
import { AuthService } from '../../../autenticaciones/auth.service';
import { CarritoService } from '../../../servicios/carrito.service';
import { ProductosService } from '../../../peticiones/productos.service';

@Component({
  selector: 'app-detalle-producto',
  template: `
    <a class="btn btn-link px-0 mb-3" routerLink="/productos">Volver a productos</a>

    <div class="alert alert-danger" *ngIf="error">{{ error }}</div>
    <div class="alert alert-success" *ngIf="mensaje">{{ mensaje }}</div>

    <div class="text-center py-5" *ngIf="loading">
      <div class="spinner-border text-primary"></div>
    </div>

    <section class="detail" *ngIf="!loading && producto">
      <div class="image">
        <img *ngIf="producto.imagen_url" [src]="producto.imagen_url" [alt]="producto.nombre">
        <div class="image-fallback" *ngIf="!producto.imagen_url">{{ producto.categoria || 'DulceMiel' }}</div>
      </div>
      <div class="info">
        <span class="badge text-bg-secondary">{{ producto.categoria || 'General' }}</span>
        <h1>{{ producto.nombre }}</h1>
        <p>{{ producto.descripcion || 'Producto disponible en tienda.' }}</p>
        <strong class="price">{{ producto.precio | currency:'PEN':'S/ ':'1.2-2' }}</strong>
        <span class="d-block mb-3">Stock disponible: {{ producto.stock }}</span>

        <div class="quantity">
          <label class="form-label">Cantidad</label>
          <input class="form-control" type="number" min="1" [max]="producto.stock" [(ngModel)]="cantidad">
        </div>

        <button class="btn btn-primary btn-lg mt-3" type="button" [disabled]="!isLoggedIn || producto.stock <= 0" (click)="agregar()">
          Agregar al carrito
        </button>
        <p class="text-muted mt-2" *ngIf="!isLoggedIn">Inicia sesion para comprar.</p>
      </div>
    </section>
  `,
  styleUrls: ['./detalle-producto.component.scss']
})
export class DetalleProductoComponent implements OnInit {
  producto: Producto | null = null;
  cantidad = 1;
  loading = true;
  error = '';
  mensaje = '';
  isLoggedIn = false;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private productosService: ProductosService,
    private carritoService: CarritoService,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    this.isLoggedIn = this.authService.isLoggedIn();
    const id = Number(this.route.snapshot.paramMap.get('id'));
    if (!id) {
      this.router.navigate(['/productos']);
      return;
    }

    this.productosService.obtenerProductoPorId(id).subscribe({
      next: response => {
        this.producto = response.data;
        this.loading = false;
      },
      error: err => {
        this.error = err.error?.message || 'Producto no encontrado.';
        this.loading = false;
      }
    });
  }

  agregar(): void {
    if (!this.producto) {
      return;
    }

    const cantidad = Math.max(1, Math.min(Number(this.cantidad) || 1, this.producto.stock));
    this.carritoService.agregarProducto(this.producto.id, cantidad).subscribe({
      next: () => this.mensaje = 'Producto agregado al carrito.',
      error: err => this.error = err.error?.message || 'No se pudo agregar al carrito.'
    });
  }
}
