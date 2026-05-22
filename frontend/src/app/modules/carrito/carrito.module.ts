import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { CarritoRoutingModule } from './carrito-routing.module';
import { CheckoutComponent } from './checkout/checkout.component';
import { VistaCarritoComponent } from './vista-carrito/vista-carrito.component';

@NgModule({
  declarations: [
    VistaCarritoComponent,
    CheckoutComponent
  ],
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    CarritoRoutingModule
  ]
})
export class CarritoModule { }
