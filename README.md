# WebDulceMiel

Aplicacion web para DulceMiel con frontend en Angular 17 y backend en Java Spring Boot MVC conectado a SQL Server.

## Estructura

```text
WebDulceMiel/
├── backend/      API REST con Java, Spring Boot y MVC
├── frontend/     Aplicacion Angular
└── docs/         Documentacion tecnica del proyecto
```

## Requisitos

- Java 21
- Node.js 18 o superior
- npm
- SQL Server con TCP/IP habilitado
- Base de datos SQL Server `DulceMielBD`

## 1. Configurar base de datos

El script principal esta en:

```text
backend/database/schema.sql
```

Ejecutalo desde SQL Server Management Studio sobre tu servidor SQL Server.

Importante: este script recrea tablas y datos iniciales. Usalo para preparar una base nueva o de prueba.

## 2. Configurar backend

Crea el archivo `.env` desde el ejemplo:

```powershell
cd backend
copy .env.example .env
```

Edita `backend/.env` con tu servidor SQL Server. Ejemplo:

```env
PORT=5000
DB_SERVER=HEYKAN
DB_NAME=DulceMielBD
MSSQL_JDBC_URL=jdbc:sqlserver://HEYKAN;databaseName=DulceMielBD;integratedSecurity=true;encrypt=true;trustServerCertificate=true
DB_DRIVER=com.microsoft.sqlserver.jdbc.SQLServerDriver
JWT_SECRET=cambia_esta_clave_en_tu_equipo
JWT_EXPIRATION_MS=604800000
```

El proyecto incluye el DLL necesario para autenticacion integrada de Windows con SQL Server en `backend/lib/`.

Levanta el backend:

```powershell
cd backend
.\mvnw.cmd spring-boot:run
```

Prueba rapida:

```powershell
Invoke-RestMethod http://localhost:5000/api/health
Invoke-RestMethod http://localhost:5000/api/productos
```

## 3. Configurar frontend

Instala dependencias:

```powershell
cd frontend
npm install
```

Levanta Angular:

```powershell
npm start
```

Abre:

```text
http://localhost:4200
```

El frontend consume la API desde:

```text
frontend/src/environments/environment.ts
```

Por defecto usa:

```text
http://localhost:5000/api
```

## Builds

Backend:

```powershell
cd backend
.\mvnw.cmd -DskipTests package
```

Frontend:

```powershell
cd frontend
npm run build
```

## Notas

- Si el backend no conecta a SQL Server, confirma que TCP/IP este habilitado y que el puerto `1433` responda.
- Si cambias imagenes de productos, el backend versiona la URL para evitar cache del navegador.
- La documentacion ampliada esta en `docs/`.
- La preparacion y secuencia de despliegue gratuito en Azure esta en `docs/AZURE_DEPLOYMENT.md`.
