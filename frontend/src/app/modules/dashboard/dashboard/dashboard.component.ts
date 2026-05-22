import { Component, OnInit } from '@angular/core';
import { AuthService } from '../../../autenticaciones/auth.service';
import { DashboardService } from '../../../peticiones/dashboard.service';

@Component({
  selector: 'app-dashboard',
  template: `
    <section class="admin-shell">
      <aside class="admin-sidebar">
        <div class="brand">
          <span>DM</span>
          <div>
            <strong>DulceMiel</strong>
            <small>Panel administrativo</small>
          </div>
        </div>
        <nav>
          <a routerLink="/dashboard" routerLinkActive="active" [routerLinkActiveOptions]="{ exact: true }">Dashboard</a>
          <a routerLink="/dashboard/productos" routerLinkActive="active">Productos</a>
          <a routerLink="/dashboard/pedidos" routerLinkActive="active">Pedidos</a>
          <a routerLink="/dashboard/promociones" routerLinkActive="active">Promociones</a>
          <a routerLink="/dashboard/sitio" routerLinkActive="active">Inicio y marca</a>
          <a routerLink="/dashboard/usuarios" routerLinkActive="active">Usuarios</a>
          <a routerLink="/productos">Ver tienda</a>
        </nav>
        <button class="btn btn-outline-light" type="button" (click)="logout()">Cerrar sesion</button>
      </aside>

      <main class="admin-content">
        <header class="admin-header">
          <div>
            <span class="eyebrow">Operacion</span>
            <h1>Dashboard</h1>
          </div>
          <p>Resumen de ventas, pedidos, clientes y alertas del catalogo.</p>
        </header>

        <div class="alert alert-danger" *ngIf="error">{{ error }}</div>

        <section class="stats">
          <article><span>Ventas entregadas</span><strong>{{ resumen?.ventas || 0 | currency:'PEN':'S/ ':'1.2-2' }}</strong></article>
          <article><span>Pedidos</span><strong>{{ resumen?.pedidos || 0 }}</strong></article>
          <article><span>Clientes</span><strong>{{ resumen?.clientes || 0 }}</strong></article>
          <article><span>Stock bajo</span><strong>{{ resumen?.stock_bajo || 0 }}</strong></article>
        </section>

        <section class="dashboard-grid">
          <article class="panel">
            <h2>Pedidos por estado</h2>
            <div class="status-row" *ngFor="let item of porEstado">
              <span>{{ item.estado }}</span>
              <strong>{{ item.total }}</strong>
            </div>
          </article>

          <article class="panel">
            <h2>Ultimos pedidos</h2>
            <div class="order-row" *ngFor="let pedido of recientes">
              <div>
                <strong>{{ pedido.numero_pedido }}</strong>
                <span>{{ pedido.nombre || pedido.email }}</span>
              </div>
              <span>{{ pedido.estado }}</span>
              <strong>{{ pedido.total | currency:'PEN':'S/ ':'1.2-2' }}</strong>
            </div>
          </article>
        </section>
      </main>
    </section>
  `,
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent implements OnInit {
  resumen: any;
  porEstado: any[] = [];
  recientes: any[] = [];
  error = '';

  constructor(
    private dashboardService: DashboardService,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    this.dashboardService.obtenerResumen().subscribe({
      next: response => {
        this.resumen = response.resumen;
        this.porEstado = response.porEstado || [];
        this.recientes = response.recientes || [];
      },
      error: err => this.error = err.error?.message || 'No se pudo cargar el dashboard.'
    });
  }

  logout(): void {
    this.authService.logout();
  }
}
