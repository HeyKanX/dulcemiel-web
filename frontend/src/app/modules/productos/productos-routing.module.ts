import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { DetalleProductoComponent } from './detalle-producto/detalle-producto.component';
import { ListadoProductosComponent } from './listado-productos/listado-productos.component';

const routes: Routes = [
  {
    path: '',
    children: [
      {
        path: '',
        component: ListadoProductosComponent
      },
      {
        path: ':id',
        component: DetalleProductoComponent
      }
    ]
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class ProductosRoutingModule { }
