import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { FormBuilder, Validators } from '@angular/forms';
import { CarritoItem } from '../../../models/producto.model';
import { CarritoService } from '../../../servicios/carrito.service';
import { PedidosService } from '../../../peticiones/pedidos.service';

@Component({
  selector: 'app-checkout',
  template: `
    <a class="btn btn-link px-0 mb-3" routerLink="/carrito">Volver al carrito</a>

    <section class="checkout">
      <div class="panel">
        <h1>Checkout</h1>
        <p>Completa los datos de entrega para registrar tu pedido.</p>

        <div class="alert alert-danger" *ngIf="error">{{ error }}</div>
        <div class="alert alert-success" *ngIf="success">{{ success }}</div>

        <form [formGroup]="form" class="delivery-form">
          <label class="form-label">Persona de contacto</label>
          <input class="form-control mb-2" formControlName="contacto_nombre" autocomplete="name">

          <label class="form-label">Celular o telefono</label>
          <input class="form-control mb-2" formControlName="contacto_telefono" autocomplete="tel">

          <label class="form-label">Email de contacto</label>
          <input class="form-control mb-2" type="email" formControlName="contacto_email" autocomplete="email">

          <label class="form-label">Direccion de entrega</label>
          <input class="form-control mb-2" formControlName="direccion_entrega" autocomplete="street-address">

          <label class="form-label">Distrito o ciudad</label>
          <input class="form-control mb-2" formControlName="distrito">

          <label class="form-label">Referencia</label>
          <textarea class="form-control mb-2" rows="2" formControlName="referencia"></textarea>

          <label class="form-label">Notas para el pedido</label>
          <textarea class="form-control mb-3" rows="2" formControlName="notas"></textarea>
        </form>

        <ul class="list-group mb-3" *ngIf="items.length > 0">
          <li class="list-group-item d-flex justify-content-between align-items-center" *ngFor="let item of items">
            <span>{{ item.nombre }} x {{ item.cantidad }}</span>
            <strong>{{ item.cantidad * item.precio | currency:'PEN':'S/ ':'1.2-2' }}</strong>
          </li>
        </ul>

        <div class="total">
          <span>Total</span>
          <strong>{{ total | currency:'PEN':'S/ ':'1.2-2' }}</strong>
        </div>

        <button class="btn btn-primary btn-lg w-100 mt-3" type="button" [disabled]="items.length === 0 || loading" (click)="confirmar()">
          {{ loading ? 'Creando pedido...' : 'Confirmar pedido' }}
        </button>
      </div>
    </section>
  `,
  styleUrls: ['./checkout.component.scss']
})
export class CheckoutComponent implements OnInit {
  items: CarritoItem[] = [];
  loading = false;
  error = '';
  success = '';

  constructor(
    private fb: FormBuilder,
    private carritoService: CarritoService,
    private pedidosService: PedidosService,
    private router: Router
  ) {}

  form = this.fb.nonNullable.group({
    contacto_nombre: ['', Validators.required],
    contacto_telefono: ['', [Validators.required, Validators.pattern(/^[0-9+()\s-]{6,20}$/)]],
    contacto_email: ['', Validators.email],
    direccion_entrega: ['', Validators.required],
    distrito: ['', Validators.required],
    referencia: [''],
    notas: ['']
  });

  ngOnInit(): void {
    this.carritoService.itemsCarrito$.subscribe(items => this.items = items);
    this.carritoService.cargarCarrito();
  }

  get total(): number {
    return this.items.reduce((sum, item) => sum + item.cantidad * item.precio, 0);
  }

  confirmar(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      this.error = this.obtenerMensajeValidacion();
      return;
    }

    this.loading = true;
    this.error = '';
    this.success = '';

    this.pedidosService.crearPedido(this.form.getRawValue()).subscribe({
      next: response => {
        this.success = `Pedido ${response.pedido?.numero_pedido || ''} creado correctamente.`;
        this.carritoService.cargarCarrito();
        setTimeout(() => this.router.navigate(['/seguimiento']), 900);
      },
      error: err => {
        this.error = err.error?.message || 'No se pudo crear el pedido.';
        this.loading = false;
      }
    });
  }

  obtenerMensajeValidacion(): string {
    if (this.form.controls.contacto_nombre.invalid) {
      return 'Ingresa el nombre de la persona que recibira el pedido.';
    }
    if (this.form.controls.contacto_telefono.invalid) {
      return 'Ingresa un numero de celular o telefono valido.';
    }
    if (this.form.controls.contacto_email.invalid) {
      return 'Ingresa un email valido o deja el campo vacio.';
    }
    if (this.form.controls.direccion_entrega.invalid) {
      return 'Ingresa la direccion de entrega.';
    }
    if (this.form.controls.distrito.invalid) {
      return 'Ingresa el distrito o ciudad de entrega.';
    }
    return 'Revisa los datos de entrega antes de confirmar.';
  }
}
