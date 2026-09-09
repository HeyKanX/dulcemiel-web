# Despliegue gratuito en Azure

Arquitectura prevista:

- Angular en Azure Static Web Apps Free.
- Spring Boot Java 21 en Azure App Service F1.
- SQL Server en Azure SQL Database Free Offer.

Esta guia prepara el despliegue, pero no crea recursos ni activa servicios facturables.

## 1. Preparar Azure SQL

1. Crea una base con la opcion **Start free** y selecciona **Auto-pause the database until next month** cuando alcance el limite gratuito.
2. Conserva el nombre del servidor, base, usuario y contrasena. No los guardes en Git.
3. En el portal abre el servidor `sql-webdulcemiel-2026`, selecciona la base `db-webdulcemiel` y entra en **Query editor**. Comprueba que el selector de base muestra exactamente `db-webdulcemiel`.
4. Copia y ejecuta completo `backend/database/azure-schema.sql`. Este archivo no contiene `CREATE DATABASE`, `USE` ni separadores `GO`, y adapta triggers y procedimientos para que el editor web pueda procesarlos como una sola consulta.
5. El script de Azure es una inicializacion de una sola ejecucion: no elimina objetos ni datos, usa una transaccion y se detiene antes de cambiar nada si detecta que `dbo.usuarios` ya existe. Si falla, revisa el error antes de reintentarlo.
6. Por peticion del responsable del proyecto, el script crea estas cuentas temporales para las pruebas del curso:

| Rol | Usuario | Contrasena temporal |
| --- | --- | --- |
| Administrador | `admin@dulcemiel.local` | `AdminCurso2026!` |
| Empleado | `empleado@dulcemiel.local` | `EmpleadoCurso2026!` |
| Cliente | `cliente@dulcemiel.local` | `ClienteCurso2026!` |

Estas contrasenas se definieron expresamente para Azure porque el repositorio original solo contenia un hash BCrypt y no permitia recuperar ni verificar el texto claro anterior. Los hashes nuevos se generaron con `BCryptPasswordEncoder` y se comprobaron contra las contrasenas de la tabla.

Las cuentas son exclusivamente para una web temporal de calidad y pruebas. Antes de reutilizar el sistema con usuarios o datos reales, elimina las tres cuentas o cambia todas sus contrasenas y sustituye los correos de ejemplo.

El archivo original `backend/database/schema.sql` se conserva solo para el entorno local y sigue siendo destructivo. No lo ejecutes en Azure.

Cadena JDBC esperada:

```text
jdbc:sqlserver://SERVIDOR.database.windows.net:1433;database=NOMBRE_BASE;encrypt=true;trustServerCertificate=false;hostNameInCertificate=*.database.windows.net;loginTimeout=30
```

## 2. Desplegar el backend

Build local:

```powershell
cd backend
.\mvnw.cmd clean package
```

Crea un App Service F1 con Java SE 21 y configura estas Application settings:

```text
MSSQL_JDBC_URL=<cadena JDBC de Azure SQL>
DB_USER=<usuario SQL>
DB_PASSWORD=<contrasena SQL>
JWT_SECRET=<secreto aleatorio largo, al menos 32 bytes>
JWT_EXPIRATION_MS=604800000
FRONTEND_URL=https://REEMPLAZAR-FRONTEND.azurestaticapps.net
DB_POOL_MAX_SIZE=5
DB_POOL_MIN_IDLE=0
JAVA_OPTS=-Xms128m -Xmx512m
```

Azure establece `PORT`; no es necesario fijarlo manualmente. Despliega `backend/target/backend-0.0.1-SNAPSHOT.jar` como aplicacion Java SE. La URL publica sera similar a `https://NOMBRE.azurewebsites.net`.

Comprueba:

```text
GET https://NOMBRE.azurewebsites.net/api/health
GET https://NOMBRE.azurewebsites.net/api/productos
```

## 3. Desplegar el frontend

1. Confirma que `frontend/src/environments/environment.prod.ts` apunte a `https://api-webdulcemiel-2026-cna2g8h7fmb6g3gu.brazilsouth-01.azurewebsites.net/api`.
2. Valida el build:

```powershell
cd frontend
npm ci
npm run build
```

3. Crea Static Web Apps Free conectado al repositorio con:

```text
App location: frontend
Output location: dist/ihc-frontend
Build command: npm run build
```

El build de produccion reemplaza `environment.ts` por `environment.prod.ts`. `staticwebapp.config.json` se copia al resultado y resuelve las rutas Angular hacia `index.html`.

4. Cuando conozcas la URL de Static Web Apps, actualiza `FRONTEND_URL` en App Service exactamente con su origen HTTPS, sin barra final, y reinicia el backend.

## 4. Verificacion final

- Abrir directamente una ruta Angular distinta de `/` y recargarla.
- Registrar e iniciar sesion; comprobar que el JWT se adjunta.
- Listar productos y cargar imagenes por HTTPS sin contenido mixto.
- Probar carrito, checkout y panel administrativo.
- Confirmar en Azure SQL que la opcion al agotar cuota es pausar, no continuar con cargos.
- Crear presupuesto y alertas de coste en Azure Cost Management.

El plan F1 descarga la aplicacion despues de inactividad y tiene una cuota de CPU reducida; el primer acceso puede tardar. Azure SQL serverless tambien puede necesitar tiempo para reanudarse.
