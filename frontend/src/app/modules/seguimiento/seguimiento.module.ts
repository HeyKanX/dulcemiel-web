import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SeguimientoRoutingModule } from './seguimiento-routing.module';
import { DetallePedidoComponent } from './detalle-pedido/detalle-pedido.component';
import { ListadoPedidosComponent } from './listado-pedidos/listado-pedidos.component';

@NgModule({
  declarations: [
    ListadoPedidosComponent,
    DetallePedidoComponent
  ],
  imports: [
    CommonModule,
    SeguimientoRoutingModule
  ]
})
export class SeguimientoModule { }
