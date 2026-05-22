import { Routes } from '@angular/router';
import { authGuard } from './autenticaciones/auth.guard';
import { adminGuard } from './autenticaciones/admin.guard';

export const appRoutes: Routes = [
  {
    path: '',
    redirectTo: 'productos',
    pathMatch: 'full'
  },
  {
    path: 'auth',
    loadChildren: () => import('./modules/auth/auth.module').then(m => m.AuthModule)
  },
  {
    path: 'productos',
    loadChildren: () => import('./modules/productos/productos.module').then(m => m.ProductosModule)
  },
  {
    path: 'carrito',
    canActivate: [authGuard],
    loadChildren: () => import('./modules/carrito/carrito.module').then(m => m.CarritoModule)
  },
  {
    path: 'seguimiento',
    canActivate: [authGuard],
    loadChildren: () => import('./modules/seguimiento/seguimiento.module').then(m => m.SeguimientoModule)
  },
  {
    path: 'dashboard',
    canActivate: [authGuard, adminGuard],
    loadChildren: () => import('./modules/dashboard/dashboard.module').then(m => m.DashboardModule)
  },
  {
    path: '**',
    redirectTo: 'productos'
  }
];
