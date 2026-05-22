import { Component, OnInit } from '@angular/core';
import { Pedido } from '../../../models/producto.model';
import { PedidosService } from '../../../peticiones/pedidos.service';

@Component({
  selector: 'app-listado-pedidos',
  template: `
    <section class="page-header">
      <div>
        <h1>Mis pedidos</h1>
        <p>Consulta el estado de tus compras.</p>
      </div>
    </section>

    <div class="alert alert-danger" *ngIf="error">{{ error }}</div>

    <div class="text-center py-5" *ngIf="loading">
      <div class="spinner-border text-primary"></div>
    </div>

    <div class="table-responsive" *ngIf="!loading && pedidos.length > 0">
      <table class="table table-hover align-middle bg-white">
        <thead>
          <tr>
            <th>Pedido</th>
            <th>Fecha</th>
            <th>Total</th>
            <th>Estado</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr *ngFor="let pedido of pedidos">
            <td>{{ pedido.numero_pedido }}</td>
            <td>{{ pedido.fecha_pedido | date:'short' }}</td>
            <td>{{ pedido.total | currency:'PEN':'S/ ':'1.2-2' }}</td>
            <td><span class="badge" [ngClass]="estadoClase(pedido.estado)">{{ pedido.estado }}</span></td>
            <td class="text-end"><a class="btn btn-sm btn-outline-primary" [routerLink]="['/seguimiento', pedido.id]">Detalle</a></td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="empty-state" *ngIf="!loading && pedidos.length === 0">
      <h2>Aun no tienes pedidos</h2>
      <a class="btn btn-primary" routerLink="/productos">Comprar ahora</a>
    </div>
  `,
  styleUrls: ['./listado-pedidos.component.scss']
})
export class ListadoPedidosComponent implements OnInit {
  pedidos: Pedido[] = [];
  loading = true;
  error = '';

  constructor(private pedidosService: PedidosService) {}

  ngOnInit(): void {
    this.pedidosService.obtenerPedidosUsuario().subscribe({
      next: response => {
        this.pedidos = response.data || [];
        this.loading = false;
      },
      error: err => {
        this.error = err.error?.message || 'No se pudieron cargar los pedidos.';
        this.loading = false;
      }
    });
  }

  estadoClase(estado: string): string {
    const clases: Record<string, string> = {
      pendiente: 'text-bg-warning',
      procesando: 'text-bg-info',
      enviado: 'text-bg-primary',
      entregado: 'text-bg-success',
      cancelado: 'text-bg-danger'
    };
    return clases[estado] || 'text-bg-secondary';
  }
}
