# Inicio Rapido

## 1. Backend

Abre una terminal en la raiz del proyecto:

```powershell
cd backend
.\mvnw.cmd spring-boot:run
```

El backend queda disponible en:

```text
http://localhost:5000/api
```

Prueba rapida:

```powershell
Invoke-RestMethod http://localhost:5000/api/health
Invoke-RestMethod http://localhost:5000/api/productos
```

## 2. Frontend

En otra terminal:

```powershell
cd frontend
npm start
```

Angular normalmente abre en:

```text
http://localhost:4200
```

## 3. Base de datos

El backend espera SQL Server con:

```text
Servidor: HEYKAN
Base: DulceMielBD
TCP: habilitado
```

La cadena esta en `backend/.env`:

```text
MSSQL_JDBC_URL=jdbc:sqlserver://HEYKAN;databaseName=DulceMielBD;integratedSecurity=true;encrypt=true;trustServerCertificate=true
```

## 4. Build

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

Nota: el frontend puede mostrar una advertencia de presupuesto de estilos SCSS. No bloquea el build.
