import { Component, OnInit } from '@angular/core';
import { CarruselItem, Producto, Promocion, SitioConfig } from '../../../models/producto.model';
import { AuthService } from '../../../autenticaciones/auth.service';
import { CarritoService } from '../../../servicios/carrito.service';
import { ProductosService } from '../../../peticiones/productos.service';
import { SitioService } from '../../../peticiones/sitio.service';

@Component({
  selector: 'app-listado-productos',
  template: `
    <section class="hero">
      <div class="hero-copy">
        <span class="eyebrow">Apicola artesanal</span>
        <h1>{{ configuracion?.nombre_empresa || 'DulceMiel' }}</h1>
        <p>{{ configuracion?.descripcion_inicio || 'Miel pura, derivados apicolas y productos naturales para tu mesa.' }}</p>
        <div class="hero-actions">
          <button class="btn btn-primary" type="button" (click)="irCatalogo()">
            Ver catalogo
          </button>
          <a class="btn btn-outline-dark" routerLink="/seguimiento" *ngIf="isLoggedIn">Mis pedidos</a>
        </div>
      </div>
      <div class="hero-media">
        <img *ngIf="slideActivo?.imagen_url" [src]="slideActivo?.imagen_url" [alt]="slideActivo?.titulo">
        <div class="honey-placeholder" *ngIf="!slideActivo?.imagen_url">
          <span>DulceMiel</span>
        </div>
        <div class="slide-caption" *ngIf="slideActivo">
          <strong>{{ slideActivo.titulo }}</strong>
          <span>{{ slideActivo.descripcion }}</span>
        </div>
      </div>
    </section>

    <section class="story-band">
      <article>
        <span>Mision</span>
        <p>{{ configuracion?.mision }}</p>
      </article>
      <article>
        <span>Vision</span>
        <p>{{ configuracion?.vision }}</p>
      </article>
      <article class="promo" *ngIf="promociones.length">
        <span>Promocion activa</span>
        <p><strong>{{ promociones[0].descuento_porcentaje }}% OFF</strong> {{ promociones[0].titulo }}</p>
      </article>
    </section>

    <section class="carousel-strip" *ngIf="carrusel.length > 1">
      <button class="round-btn" type="button" (click)="moverSlide(-1)" aria-label="Anterior">‹</button>
      <div class="carousel-track">
        <button
          class="thumb"
          type="button"
          *ngFor="let item of carrusel; let i = index"
          [class.active]="i === slideIndex"
          (click)="slideIndex = i">
          <img *ngIf="item.imagen_url" [src]="item.imagen_url" [alt]="item.titulo">
          <span>{{ item.titulo }}</span>
        </button>
      </div>
      <button class="round-btn" type="button" (click)="moverSlide(1)" aria-label="Siguiente">›</button>
    </section>

    <section class="catalog-header" id="catalogo">
      <div>
        <span class="eyebrow">Catalogo</span>
        <h2>Productos de la colmena</h2>
      </div>
      <div class="filters">
        <input class="form-control" placeholder="Buscar producto" [(ngModel)]="busqueda">
        <select class="form-select" [(ngModel)]="categoria">
          <option value="">Todas las categorias</option>
          <option *ngFor="let item of categorias" [value]="item">{{ item }}</option>
        </select>
      </div>
    </section>

    <div class="alert alert-danger mx-3" *ngIf="error">{{ error }}</div>
    <div class="alert alert-success mx-3" *ngIf="mensaje">{{ mensaje }}</div>

    <div class="text-center py-5" *ngIf="loading">
      <div class="spinner-border text-warning"></div>
    </div>

    <section class="product-grid" *ngIf="!loading">
      <article class="product-card" [class.low-stock]="esStockBajo(producto)" *ngFor="let producto of productosFiltrados">
        <div class="product-image">
          <img *ngIf="producto.imagen_url" [src]="producto.imagen_url" [alt]="producto.nombre">
          <div class="image-fallback" *ngIf="!producto.imagen_url">{{ producto.categoria || 'Miel' }}</div>
          <span class="stock-alert" *ngIf="esStockBajo(producto)">Stock bajo</span>
        </div>
        <div class="product-body">
          <span class="tag">{{ producto.categoria || 'Natural' }}</span>
          <h3>{{ producto.nombre }}</h3>
          <p>{{ producto.descripcion || 'Producto apicola disponible.' }}</p>
          <div class="meta">
            <strong>{{ producto.precio | currency:'PEN':'S/ ':'1.2-2' }}</strong>
            <span [class.stock-low-text]="esStockBajo(producto)">{{ producto.stock }} und.</span>
          </div>
          <div class="actions">
            <a class="btn btn-outline-dark" [routerLink]="['/productos', producto.id]">Ver</a>
            <button class="btn btn-primary" type="button" [disabled]="!isLoggedIn || producto.stock <= 0" (click)="agregar(producto)">
              Agregar
            </button>
          </div>
        </div>
      </article>
    </section>

    <p class="empty-state" *ngIf="!loading && productosFiltrados.length === 0">No hay productos para mostrar.</p>
  `,
  styleUrls: ['./listado-productos.component.scss']
})
export class ListadoProductosComponent implements OnInit {
  productos: Producto[] = [];
  configuracion: SitioConfig | null = null;
  carrusel: CarruselItem[] = [];
  promociones: Promocion[] = [];
  busqueda = '';
  categoria = '';
  slideIndex = 0;
  loading = true;
  error = '';
  mensaje = '';
  isLoggedIn = false;

  constructor(
    private productosService: ProductosService,
    private carritoService: CarritoService,
    private authService: AuthService,
    private sitioService: SitioService
  ) {}

  ngOnInit(): void {
    this.isLoggedIn = this.authService.isLoggedIn();
    this.authService.isLoggedIn$.subscribe(value => this.isLoggedIn = value);
    this.cargarInicio();
    this.cargarProductos();
  }

  get slideActivo(): CarruselItem | null {
    return this.carrusel[this.slideIndex] || null;
  }

  get categorias(): string[] {
    return [...new Set(this.productos.map(p => p.categoria).filter(Boolean))];
  }

  get productosFiltrados(): Producto[] {
    const texto = this.busqueda.trim().toLowerCase();
    return this.productos.filter(producto => {
      const coincideTexto = !texto || producto.nombre.toLowerCase().includes(texto) || producto.descripcion?.toLowerCase().includes(texto);
      const coincideCategoria = !this.categoria || producto.categoria === this.categoria;
      return coincideTexto && coincideCategoria;
    });
  }

  cargarInicio(): void {
    this.sitioService.obtenerInicio().subscribe({
      next: response => {
        this.configuracion = response.configuracion;
        this.carrusel = response.carrusel || [];
        this.promociones = response.promociones || [];
      },
      error: () => {
        this.configuracion = null;
      }
    });
  }

  cargarProductos(): void {
    this.loading = true;
    this.productosService.obtenerProductos().subscribe({
      next: response => {
        this.productos = response.data || [];
        this.loading = false;
      },
      error: err => {
        this.error = err.error?.message || 'No se pudieron cargar los productos.';
        this.loading = false;
      }
    });
  }

  moverSlide(delta: number): void {
    if (!this.carrusel.length) {
      return;
    }
    this.slideIndex = (this.slideIndex + delta + this.carrusel.length) % this.carrusel.length;
  }

  irCatalogo(): void {
    document.getElementById('catalogo')?.scrollIntoView({
      behavior: 'smooth'
    });
  }

  esStockBajo(producto: Producto): boolean {
    return producto.stock > 0 && producto.stock <= 5;
  }

  agregar(producto: Producto): void {
    this.mensaje = '';
    this.error = '';
    this.carritoService.agregarProducto(producto.id, 1).subscribe({
      next: () => this.mensaje = `${producto.nombre} agregado al carrito.`,
      error: err => this.error = err.error?.message || 'No se pudo agregar al carrito.'
    });
  }
}