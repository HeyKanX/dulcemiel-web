export interface Usuario {
  id: number;
  nombre: string;
  email: string;
  rol: 'usuario' | 'admin' | 'empleado';
  estado: 'activo' | 'inactivo';
  fecha_creacion: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  nombre: string;
  email: string;
  password: string;
  passwordConfirm: string;
}

export interface AuthResponse {
  success: boolean;
  message: string;
  token?: string;
  usuario?: Usuario;
}
