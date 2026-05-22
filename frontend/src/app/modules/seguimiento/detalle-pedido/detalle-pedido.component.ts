import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { DetallePedido, Pedido } from '../../../models/producto.model';
import { PedidosService } from '../../../peticiones/pedidos.service';

@Component({
  selector: 'app-detalle-pedido',
  template: `
    <a class="btn btn-link px-0 mb-3" routerLink="/seguimiento">Volver a mis pedidos</a>

    <div class="alert alert-danger" *ngIf="error">{{ error }}</div>

    <div class="text-center py-5" *ngIf="loading">
      <div class="spinner-border text-primary"></div>
    </div>

    <section class="panel" *ngIf="!loading && pedido">
      <div class="header">
        <div>
          <h1>{{ pedido.numero_pedido }}</h1>
          <p>{{ pedido.fecha_pedido | date:'medium' }}</p>
        </div>
        <span class="badge text-bg-primary">{{ pedido.estado }}</span>
      </div>

      <table class="table align-middle">
        <thead>
          <tr>
            <th>Producto</th>
            <th>Cantidad</th>
            <th>Precio</th>
            <th>Subtotal</th>
          </tr>
        </thead>
        <tbody>
          <tr *ngFor="let item of detalles">
            <td class="product-cell">
              <img *ngIf="item.imagen_url" [src]="item.imagen_url" [alt]="item.nombre">
              <span>{{ item.nombre }}</span>
            </td>
            <td>{{ item.cantidad }}</td>
            <td>{{ item.precio_unitario | currency:'PEN':'S/ ':'1.2-2' }}</td>
            <td>{{ item.subtotal | currency:'PEN':'S/ ':'1.2-2' }}</td>
          </tr>
        </tbody>
      </table>

      <div class="total">
        <span>Total</span>
        <strong>{{ pedido.total | currency:'PEN':'S/ ':'1.2-2' }}</strong>
      </div>
    </section>
  `,
  styleUrls: ['./detalle-pedido.component.scss']
})
export class DetallePedidoComponent implements OnInit {
  pedido: Pedido | null = null;
  detalles: DetallePedido[] = [];
  loading = true;
  error = '';

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private pedidosService: PedidosService
  ) {}

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    if (!id) {
      this.router.navigate(['/seguimiento']);
      return;
    }

    this.pedidosService.obtenerDetallePedido(id).subscribe({
      next: response => {
        this.pedido = response.pedido;
        this.detalles = response.detalles || [];
        this.loading = false;
      },
      error: err => {
        this.error = err.error?.message || 'No se pudo cargar el pedido.';
        this.loading = false;
      }
    });
  }
}
