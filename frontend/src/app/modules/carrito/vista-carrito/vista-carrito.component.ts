import { Component, OnInit } from '@angular/core';
import { CarritoItem } from '../../../models/producto.model';
import { CarritoService } from '../../../servicios/carrito.service';

@Component({
  selector: 'app-vista-carrito',
  template: `
    <section class="page-header">
      <div>
        <h1>Carrito</h1>
        <p>Revisa cantidades antes de confirmar tu compra.</p>
      </div>
      <button class="btn btn-outline-danger" type="button" [disabled]="items.length === 0" (click)="vaciar()">Vaciar carrito</button>
    </section>

    <div class="alert alert-danger" *ngIf="error">{{ error }}</div>
    <div class="alert alert-success" *ngIf="mensaje">{{ mensaje }}</div>

    <div class="cart-layout" *ngIf="items.length > 0; else empty">
      <section class="items">
        <article class="cart-item" *ngFor="let item of items">
          <img *ngIf="item.imagen_url" [src]="item.imagen_url" [alt]="item.nombre">
          <div class="item-fallback" *ngIf="!item.imagen_url">DM</div>
          <div>
            <h2>{{ item.nombre }}</h2>
            <span>{{ item.precio | currency:'PEN':'S/ ':'1.2-2' }} c/u</span>
          </div>
          <input class="form-control" type="number" min="1" [ngModel]="item.cantidad" (ngModelChange)="actualizar(item, $event)">
          <strong>{{ item.cantidad * item.precio | currency:'PEN':'S/ ':'1.2-2' }}</strong>
          <button class="btn btn-sm btn-outline-danger" type="button" (click)="eliminar(item.id)">Eliminar</button>
        </article>
      </section>

      <aside class="summary">
        <h2>Resumen</h2>
        <div class="line">
          <span>Items</span>
          <strong>{{ items.length }}</strong>
        </div>
        <div class="line total">
          <span>Total</span>
          <strong>{{ total | currency:'PEN':'S/ ':'1.2-2' }}</strong>
        </div>
        <a class="btn btn-primary w-100" routerLink="/carrito/checkout">Proceder al checkout</a>
      </aside>
    </div>

    <ng-template #empty>
      <div class="empty-state">
        <h2>Tu carrito esta vacio</h2>
        <a class="btn btn-primary" routerLink="/productos">Ver productos</a>
      </div>
    </ng-template>
  `,
  styleUrls: ['./vista-carrito.component.scss']
})
export class VistaCarritoComponent implements OnInit {
  items: CarritoItem[] = [];
  error = '';
  mensaje = '';

  constructor(private carritoService: CarritoService) {}

  ngOnInit(): void {
    this.carritoService.itemsCarrito$.subscribe(items => this.items = items);
    this.carritoService.cargarCarrito();
  }

  get total(): number {
    return this.items.reduce((sum, item) => sum + item.cantidad * item.precio, 0);
  }

  actualizar(item: CarritoItem, value: number): void {
    const cantidad = Math.max(1, Number(value) || 1);
    this.carritoService.actualizarCarrito(item.id, cantidad).subscribe({
      next: () => this.mensaje = 'Cantidad actualizada.',
      error: err => this.error = err.error?.message || 'No se pudo actualizar el carrito.'
    });
  }

  eliminar(id: number): void {
    this.carritoService.eliminarDelCarrito(id).subscribe({
      next: () => this.mensaje = 'Producto eliminado.',
      error: err => this.error = err.error?.message || 'No se pudo eliminar el producto.'
    });
  }

  vaciar(): void {
    this.carritoService.vaciarCarrito().subscribe({
      next: () => this.mensaje = 'Carrito vaciado.',
      error: err => this.error = err.error?.message || 'No se pudo vaciar el carrito.'
    });
  }
}
