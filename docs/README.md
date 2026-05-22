# Dulce Miel

Proyecto organizado con frontend en Angular 17 y backend en Java Spring Boot MVC. El backend anterior en Node.js fue reemplazado por Spring Boot y la carpeta principal del servidor ahora es `backend`.

## Estructura principal

```text
WebDulceMiel/
├── backend/      API Java Spring Boot MVC
├── frontend/     Aplicacion Angular
└── docs/         Documentacion del proyecto
```

## Backend

El backend esta en `backend/` y usa:

- Java 21
- Spring Boot 3.5
- Spring MVC
- Spring Security
- JDBC con SQL Server
- JWT para autenticacion
- Maven Wrapper

La base de datos configurada es SQL Server:

```text
Servidor: HEYKAN
Base de datos: DulceMielBD
Puerto API: 5000
```

La conexion esta en `backend/.env` mediante `MSSQL_JDBC_URL`. Se usa autenticacion integrada de Windows con el driver oficial de Microsoft y el DLL nativo ubicado en `backend/lib/`.

## Frontend

El frontend esta en `frontend/` y usa Angular 17. La URL del backend esta en:

```text
frontend/src/environments/environment.ts
```

Actualmente apunta a:

```text
http://localhost:5000/api
```

La organizacion interna quedo asi:

- `autenticaciones/`: login, JWT, guards e interceptor.
- `peticiones/`: servicios que hacen solicitudes HTTP a la API.
- `servicios/`: servicios internos de la aplicacion, como carrito.
- `components/`, `modules/`, `models/`: vistas, modulos y modelos.

## Documentos utiles

- `README.md`: resumen del estado actual.
- `QUICK_START.md`: comandos para levantar frontend y backend.
- `ARQUITECTURA.md`: explicacion tecnica de la estructura MVC y Angular.
