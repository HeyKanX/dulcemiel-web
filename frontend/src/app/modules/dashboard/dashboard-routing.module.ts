import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { DashboardComponent } from './dashboard/dashboard.component';
import { GestionPedidosComponent } from './gestion-pedidos/gestion-pedidos.component';
import { GestionProductosComponent } from './gestion-productos/gestion-productos.component';
import { GestionPromocionesComponent } from './gestion-promociones/gestion-promociones.component';
import { GestionSitioComponent } from './gestion-sitio/gestion-sitio.component';
import { GestionUsuariosComponent } from './gestion-usuarios/gestion-usuarios.component';

const routes: Routes = [
  {
    path: '',
    children: [
      {
        path: '',
        component: DashboardComponent
      },
      {
        path: 'productos',
        component: GestionProductosComponent
      },
      {
        path: 'pedidos',
        component: GestionPedidosComponent
      },
      {
        path: 'promociones',
        component: GestionPromocionesComponent
      },
      {
        path: 'usuarios',
        component: GestionUsuariosComponent
      },
      {
        path: 'sitio',
        component: GestionSitioComponent
      }
    ]
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class DashboardRoutingModule { }
