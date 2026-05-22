export interface Producto {
  id: number;
  nombre: string;
  descripcion: string;
  precio: number;
  stock: number;
  imagen_url: string | null;
  categoria: string;
  estado: 'disponible' | 'agotado' | 'discontinuado';
}

export interface CarritoItem {
  id: number;
  producto_id: number;
  cantidad: number;
  precio_unitario: number;
  nombre: string;
  imagen_url: string | null;
  precio: number;
}

export interface Pedido {
  id: number;
  numero_pedido: string;
  total: number;
  estado: 'pendiente' | 'procesando' | 'enviado' | 'entregado' | 'cancelado';
  fecha_pedido: string;
  fecha_entrega: string | null;
  contacto_nombre?: string;
  contacto_telefono?: string;
  contacto_email?: string | null;
  direccion_entrega?: string;
  distrito?: string;
  referencia?: string | null;
  notas?: string | null;
}

export interface DetallePedido {
  id: number;
  pedido_id: number;
  producto_id: number;
  nombre: string;
  cantidad: number;
  precio_unitario: number;
  subtotal: number;
  imagen_url?: string | null;
}

export interface SitioConfig {
  id: number;
  nombre_empresa: string;
  descripcion_inicio: string;
  mision: string;
  vision: string;
  logo_url: string | null;
}

export interface CarruselItem {
  id: number;
  titulo: string;
  descripcion: string | null;
  orden: number;
  activo: boolean;
  imagen_url: string | null;
}

export interface Promocion {
  id: number;
  titulo: string;
  descripcion: string | null;
  descuento_porcentaje: number;
  fecha_inicio: string;
  fecha_fin: string | null;
  activo: boolean;
}
