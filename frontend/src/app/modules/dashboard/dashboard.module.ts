import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { DashboardRoutingModule } from './dashboard-routing.module';
import { DashboardComponent } from './dashboard/dashboard.component';
import { GestionPedidosComponent } from './gestion-pedidos/gestion-pedidos.component';
import { GestionProductosComponent } from './gestion-productos/gestion-productos.component';
import { GestionPromocionesComponent } from './gestion-promociones/gestion-promociones.component';
import { GestionSitioComponent } from './gestion-sitio/gestion-sitio.component';
import { GestionUsuariosComponent } from './gestion-usuarios/gestion-usuarios.component';

@NgModule({
  declarations: [
    DashboardComponent,
    GestionProductosComponent,
    GestionPedidosComponent,
    GestionPromocionesComponent,
    GestionSitioComponent,
    GestionUsuariosComponent
  ],
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    DashboardRoutingModule
  ]
})
export class DashboardModule { }
