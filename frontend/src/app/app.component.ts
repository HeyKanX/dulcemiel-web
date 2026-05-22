import { Component, OnInit } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { NavbarComponent } from './components/navbar/navbar.component';
import { AuthService } from './autenticaciones/auth.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, CommonModule, NavbarComponent],
  template: `
    <app-navbar *ngIf="!isAdminArea"></app-navbar>
    <main [class]="isAdminArea ? 'admin-main' : 'public-main'">
      <router-outlet></router-outlet>
    </main>
  `,
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnInit {
  title = 'IHC - Sistema de Compras';

  constructor(private authService: AuthService, private router: Router) {}

  ngOnInit() {
    // Verificar si hay token al cargar la app
    this.authService.verificarToken();
  }

  get isAdminArea(): boolean {
    return this.router.url.startsWith('/dashboard');
  }
}
