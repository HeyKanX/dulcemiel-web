import { Component, OnInit } from '@angular/core';
import { DetallePedido, Pedido } from '../../../models/producto.model';
import { PedidosService } from '../../../peticiones/pedidos.service';

@Component({
  selector: 'app-gestion-pedidos',
  template: `
    <section class="page-header">
      <div>
        <h1>Gestion de pedidos</h1>
        <p>Revisa productos, direccion, contacto y estado de cada orden.</p>
      </div>
      <a class="btn btn-outline-secondary" routerLink="/dashboard">Dashboard</a>
    </section>

    <div class="alert alert-danger" *ngIf="error">{{ error }}</div>
    <div class="alert alert-success" *ngIf="mensaje">{{ mensaje }}</div>

    <section class="orders-by-status">
      <article class="panel status-panel" *ngFor="let estado of estados">
        <header class="status-header">
          <div>
            <span>{{ etiquetaEstado(estado) }}</span>
            <strong>{{ pedidosPorEstado(estado).length }}</strong>
          </div>
        </header>

        <div class="table-responsive" *ngIf="pedidosPorEstado(estado).length; else sinPedidos">
          <table class="table table-hover align-middle">
            <thead>
              <tr>
                <th>Pedido</th>
                <th>Cliente</th>
                <th>Contacto</th>
                <th>Destino</th>
                <th>Fecha</th>
                <th>Total</th>
                <th>Estado</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr *ngFor="let pedido of pedidosPorEstado(estado)">
                <td>{{ pedido.numero_pedido }}</td>
                <td>{{ usuarioPedido(pedido) }}</td>
                <td>
                  <strong>{{ pedido.contacto_nombre || 'Sin contacto' }}</strong>
                  <small>{{ pedido.contacto_telefono || 'Sin telefono' }}</small>
                </td>
                <td>
                  <strong>{{ pedido.distrito || 'Sin distrito' }}</strong>
                  <small>{{ pedido.direccion_entrega || 'Sin direccion' }}</small>
                </td>
                <td>{{ pedido.fecha_pedido | date:'short' }}</td>
                <td>{{ pedido.total | currency:'PEN':'S/ ':'1.2-2' }}</td>
                <td>
                  <select class="form-select form-select-sm" [ngModel]="pedido.estado" (ngModelChange)="actualizar(pedido, $event)">
                    <option *ngFor="let opcion of estados" [value]="opcion">{{ etiquetaEstado(opcion) }}</option>
                  </select>
                </td>
                <td class="text-end">
                  <button class="btn btn-sm btn-outline-primary" type="button" (click)="verDetalle(pedido)">Ver detalle</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <ng-template #sinPedidos>
          <p class="empty-status">No hay pedidos en este estado.</p>
        </ng-template>
      </article>
    </section>

    <section class="panel detail-panel" *ngIf="pedidoSeleccionado">
      <div class="detail-header">
        <div>
          <h2>{{ pedidoSeleccionado.numero_pedido }}</h2>
          <p>{{ pedidoSeleccionado.fecha_pedido | date:'medium' }}</p>
        </div>
        <button class="btn btn-sm btn-outline-secondary" type="button" (click)="cerrarDetalle()">Cerrar</button>
      </div>

      <div class="info-grid">
        <article>
          <span>Cliente</span>
          <strong>{{ usuarioPedido(pedidoSeleccionado) }}</strong>
          <small>{{ pedidoSeleccionado.contacto_email || pedidoSeleccionado.email || 'Sin email' }}</small>
        </article>
        <article>
          <span>Contacto</span>
          <strong>{{ pedidoSeleccionado.contacto_nombre || 'Sin contacto' }}</strong>
          <small>{{ pedidoSeleccionado.contacto_telefono || 'Sin telefono' }}</small>
        </article>
        <article>
          <span>Direccion</span>
          <strong>{{ pedidoSeleccionado.direccion_entrega || 'Sin direccion' }}</strong>
          <small>{{ pedidoSeleccionado.distrito || '' }} {{ pedidoSeleccionado.referencia ? '- ' + pedidoSeleccionado.referencia : '' }}</small>
        </article>
      </div>

      <p class="notes" *ngIf="pedidoSeleccionado.notas"><strong>Notas:</strong> {{ pedidoSeleccionado.notas }}</p>

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
    </section>
  `,
  styleUrls: ['./gestion-pedidos.component.scss']
})
export class GestionPedidosComponent implements OnInit {
  pedidos: (Pedido & { nombre?: string; email?: string })[] = [];
  pedidoSeleccionado: (Pedido & { nombre?: string; email?: string }) | null = null;
  detalles: DetallePedido[] = [];
  estados: Pedido['estado'][] = ['pendiente', 'procesando', 'enviado', 'entregado', 'cancelado'];
  error = '';
  mensaje = '';

  constructor(private pedidosService: PedidosService) {}

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.pedidosService.obtenerTodosPedidos().subscribe({
      next: response => this.pedidos = response.data || [],
      error: err => this.error = err.error?.message || 'No se pudieron cargar pedidos.'
    });
  }

  actualizar(pedido: Pedido, estado: string): void {
    this.pedidosService.actualizarEstadoPedido(pedido.id, estado).subscribe({
      next: () => {
        pedido.estado = estado as Pedido['estado'];
        this.mensaje = 'Estado actualizado.';
      },
      error: err => this.error = err.error?.message || 'No se pudo actualizar el pedido.'
    });
  }

  pedidosPorEstado(estado: Pedido['estado']): (Pedido & { nombre?: string; email?: string })[] {
    return this.pedidos.filter(pedido => pedido.estado === estado);
  }

  etiquetaEstado(estado: string): string {
    const etiquetas: Record<string, string> = {
      pendiente: 'Pendientes',
      procesando: 'En proceso',
      enviado: 'Enviados',
      entregado: 'Entregados',
      cancelado: 'Cancelados'
    };
    return etiquetas[estado] || estado;
  }

  usuarioPedido(pedido: Pedido): string {
    const extendido = pedido as Pedido & { nombre?: string; email?: string };
    return extendido.nombre || extendido.email || 'Cliente';
  }

  verDetalle(pedido: Pedido): void {
    this.error = '';
    this.pedidosService.obtenerDetallePedido(pedido.id).subscribe({
      next: response => {
        this.pedidoSeleccionado = response.pedido;
        this.detalles = response.detalles || [];
      },
      error: err => this.error = err.error?.message || 'No se pudo cargar el detalle del pedido.'
    });
  }

  cerrarDetalle(): void {
    this.pedidoSeleccionado = null;
    this.detalles = [];
  }
}
