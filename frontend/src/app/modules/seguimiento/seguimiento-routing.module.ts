import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { DetallePedidoComponent } from './detalle-pedido/detalle-pedido.component';
import { ListadoPedidosComponent } from './listado-pedidos/listado-pedidos.component';

const routes: Routes = [
  {
    path: '',
    children: [
      {
        path: '',
        component: ListadoPedidosComponent
      },
      {
        path: ':id',
        component: DetallePedidoComponent
      }
    ]
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class SeguimientoRoutingModule { }
