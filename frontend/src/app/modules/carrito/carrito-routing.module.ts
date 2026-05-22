import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { CheckoutComponent } from './checkout/checkout.component';
import { VistaCarritoComponent } from './vista-carrito/vista-carrito.component';

const routes: Routes = [
  {
    path: '',
    children: [
      {
        path: '',
        component: VistaCarritoComponent
      },
      {
        path: 'checkout',
        component: CheckoutComponent
      }
    ]
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class CarritoRoutingModule { }
