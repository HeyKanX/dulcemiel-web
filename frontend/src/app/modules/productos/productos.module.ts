import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ProductosRoutingModule } from './productos-routing.module';
import { ListadoProductosComponent } from './listado-productos/listado-productos.component';
import { DetalleProductoComponent } from './detalle-producto/detalle-producto.component';

@NgModule({
  declarations: [
    ListadoProductosComponent,
    DetalleProductoComponent
  ],
  imports: [
    CommonModule,
    FormsModule,
    ProductosRoutingModule
  ]
})
export class ProductosModule { }
