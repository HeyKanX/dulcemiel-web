# Arquitectura

## Vista general

```text
Angular 17
  |
  | HTTP JSON
  v
Spring Boot MVC - puerto 5000
  |
  | JDBC
  v
SQL Server - DulceMielBD
```

El proyecto quedo separado en tres areas:

- `frontend/`: aplicacion Angular.
- `backend/`: API Java Spring Boot.
- `docs/`: documentacion vigente del proyecto.

## Backend Spring Boot MVC

Ruta principal:

```text
backend/src/main/java/com/dulcemiel/backend
```

Capas:

- `controller/`: recibe las rutas HTTP y responde al frontend.
- `service/`: logica auxiliar compartida, JWT, respuestas y soporte de autenticacion.
- `model/`: modelos usados por la API.
- `config/`: seguridad, CORS y carga del archivo `.env`.

Configuracion:

- `backend/.env`: puerto, SQL Server y JWT.
- `backend/src/main/resources/application.properties`: propiedades Spring.
- `backend/lib/mssql-jdbc_auth-12.10.0.x64.dll`: DLL para autenticacion integrada de Windows con SQL Server.

Endpoints principales:

```text
GET    /api/health
POST   /api/auth/register
POST   /api/auth/login
GET    /api/auth/perfil
GET    /api/auth/usuarios
POST   /api/auth/empleados
PUT    /api/auth/usuarios/{id}

GET    /api/productos
GET    /api/productos/admin/todos
GET    /api/productos/{id}
POST   /api/productos
PUT    /api/productos/{id}
DELETE /api/productos/{id}

GET    /api/carrito
POST   /api/carrito/agregar
PUT    /api/carrito/actualizar
DELETE /api/carrito/{carritoId}
DELETE /api/carrito

POST   /api/pedidos
GET    /api/pedidos
GET    /api/pedidos/admin/todos
GET    /api/pedidos/{pedidoId}
PUT    /api/pedidos/{pedidoId}

GET    /api/promociones
POST   /api/promociones
PUT    /api/promociones/{id}
DELETE /api/promociones/{id}

GET    /api/sitio/inicio
PUT    /api/sitio/configuracion
POST   /api/sitio/carrusel
PUT    /api/sitio/carrusel/{id}
DELETE /api/sitio/carrusel/{id}

GET    /api/dashboard/resumen
GET    /api/imagenes/{tipo}/{id}
```

## Frontend Angular

Ruta principal:

```text
frontend/src/app
```

Organizacion:

- `autenticaciones/`: `AuthService`, guards e interceptor JWT.
- `peticiones/`: servicios HTTP para productos, pedidos, dashboard, promociones y sitio.
- `servicios/`: servicios internos que no son solamente peticiones HTTP.
- `components/`: componentes visuales.
- `modules/`: modulos funcionales.
- `models/`: interfaces y tipos.

El frontend consume el backend desde:

```text
frontend/src/environments/environment.ts
```

```text
apiUrl: 'http://localhost:5000/api'
```

## Flujo de autenticacion

1. El usuario inicia sesion desde Angular.
2. Angular llama a `/api/auth/login`.
3. Spring Boot valida el usuario contra SQL Server.
4. El backend devuelve un JWT.
5. El interceptor de Angular adjunta el token en las peticiones protegidas.
6. Los guards controlan acceso a rutas segun autenticacion y rol.

## Base de datos

La API usa la base existente `DulceMielBD` en SQL Server. No se requiere recrear la base si ya existe y tiene las tablas del proyecto.

La conexion activa usa:

```text
jdbc:sqlserver://HEYKAN;databaseName=DulceMielBD;integratedSecurity=true;encrypt=true;trustServerCertificate=true
```
