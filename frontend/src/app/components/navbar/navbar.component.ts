import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { AuthService } from '../../autenticaciones/auth.service';
import { CarritoService } from '../../servicios/carrito.service';
import { SitioService } from '../../peticiones/sitio.service';
import { SitioConfig } from '../../models/producto.model';
import { Usuario } from '../../models/usuario.model';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './navbar.component.html',
  styleUrls: ['./navbar.component.scss']
})
export class NavbarComponent implements OnInit {
  usuario: Usuario | null = null;
  cantidadCarrito: number = 0;
  isLoggedIn: boolean = false;
  isAdmin: boolean = false;
  configuracion: SitioConfig | null = null;

  constructor(
    private authService: AuthService,
    private carritoService: CarritoService,
    private sitioService: SitioService
  ) {}

  ngOnInit(): void {
    // Suscribirse a cambios en el usuario
    this.authService.usuario$.subscribe(usuario => {
      this.usuario = usuario;
    });

    // Suscribirse a cambios en el login state
    this.authService.isLoggedIn$.subscribe(isLoggedIn => {
      this.isLoggedIn = isLoggedIn;
      this.isAdmin = this.authService.canAccessAdmin();
    });

    // Suscribirse a cambios en el carrito
    this.carritoService.itemsCarrito$.subscribe(items => {
      this.cantidadCarrito = items.length;
    });

    this.cargarMarca();
  }

  logout(): void {
    this.authService.logout();
  }

  cargarMarca(): void {
    this.sitioService.obtenerInicio().subscribe({
      next: response => this.configuracion = response.configuracion || null,
      error: () => this.configuracion = null
    });
  }

  get nombreEmpresa(): string {
    return this.configuracion?.nombre_empresa || 'DulceMiel';
  }

  get iniciales(): string {
    return this.nombreEmpresa
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map(parte => parte.charAt(0).toUpperCase())
      .join('') || 'DM';
  }
}
