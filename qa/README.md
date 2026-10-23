# Ejecución de pruebas de Dulce Miel

Las pruebas están separadas del código de la aplicación en `qa/`, salvo las suites unitarias ubicadas en las rutas habituales de Maven y Angular. El diseño y la trazabilidad de los 41 casos se presentan en el anexo del informe del proyecto. Las salidas se guardan en `../../Evidencias/`, organizadas por tipo de prueba y herramienta.

## Preparación

Desde `qa/`:

```powershell
npm ci
py -m pip install -r requirements.txt
py -m playwright install chromium firefox webkit
.\infra\bootstrap.ps1
```

El script de preparación usa la base aislada `dulce-miel-qa-c5` en `127.0.0.1:14333`. Ejecuta `./infra/run-backend.ps1` desde `qa/` y `npm start -- --host 127.0.0.1 --port 4200` desde `frontend/` en otra terminal. Si el backend de QA ya está activo en el puerto 5000, el script lo informa y termina sin iniciar una segunda instancia.

## Pruebas funcionales de interfaz con Behave y Selenium

Desde `qa/`:

```powershell
$env:QA_ISOLATED_DB = '1'
$env:QA_RUN_ID = (Get-Date -Format 'yyyyMMdd-HHmmss')
$env:QA_ARTIFACTS = "..\..\Evidencias\funcionales-ui\behave-selenium\$env:QA_RUN_ID"
New-Item -ItemType Directory -Force $env:QA_ARTIFACTS | Out-Null
py -m behave tests/functional/features --lang en --junit --junit-directory $env:QA_ARTIFACTS -f progress 2>&1 | Tee-Object "$env:QA_ARTIFACTS\behave.log"
```

El navegador se crea y cierra por escenario. Los escenarios `@writes` requieren la base aislada. Las palabras clave de Gherkin están en inglés y el comportamiento se describe en español.

## Pruebas funcionales de API con Newman

```powershell
$e = "..\..\Evidencias\funcionales-api\postman-newman\$(Get-Date -Format 'yyyyMMdd-HHmmss')"
New-Item -ItemType Directory -Force $e | Out-Null
.\node_modules\.bin\newman.cmd run .\tests\functional\api\dulcemiel.postman_collection.json -r cli,junit --reporter-junit-export "$e\api-newman.xml" 2>&1 | Tee-Object "$e\api-newman.log"
```

## Pruebas unitarias, integración y cobertura

Detén el backend de QA con `Ctrl+C` en la terminal donde se ejecuta `run-backend.ps1` antes de lanzar `.\mvnw.cmd clean verify` desde `backend/`. En Windows, el proceso mantiene abierto el JAR de `target` e impide que Maven limpie esa carpeta. La suite de integración usa Docker y Testcontainers para SQL Server.

Si las aserciones fallan, conserva los XML de `backend/target/surefire-reports/` y ejecuta `.\mvnw.cmd jacoco:report` desde `backend/` para generar el reporte de cobertura con los datos recogidos antes del fallo. Para volver a usar la aplicación, ejecuta `.\mvnw.cmd package -DskipTests` desde `backend/` y luego `./infra/run-backend.ps1` desde `qa/`.

Desde `frontend/`, ejecuta `npm ci` y `npm run test:coverage`; Karma genera el reporte de cobertura Angular. Conserva los XML y registros de cada corrida.

## Compatibilidad, rendimiento y accesibilidad

Desde `qa/`:

```powershell
$run = Get-Date -Format 'yyyyMMdd-HHmmss'
$compat = "..\..\Evidencias\compatibilidad\playwright\$run"
New-Item -ItemType Directory -Force $compat | Out-Null
py tests/non-functional/compatibility/playwright_compatibility.py 2>&1 | Tee-Object "$compat\playwright.log"
$perf = "..\..\Evidencias\rendimiento\k6\$run"
New-Item -ItemType Directory -Force $perf | Out-Null
& 'C:\Program Files\k6\k6.exe' run -e QA_LOAD_PROFILE=smoke -e QA_K6_SUMMARY="$perf\k6-smoke.json" .\tests\non-functional\performance\k6\catalogo.js 2>&1 | Tee-Object "$perf\k6-smoke.log"
py tests/non-functional/accessibility/axe_core_scan.py --base-url https://jolly-smoke-017f42010.5.azurestaticapps.net --output "..\..\Evidencias\accesibilidad\axe-core\$run"
```

Repite k6 con los perfiles `baseline` y `moderate`, cambiando el nombre del JSON y el registro de salida para cada perfil. k6 usa las URL locales configuradas; la exploración pública de axe-core recibe expresamente la URL desplegada y guarda resultados exportables en JSON y CSV. Para examinar la interfaz con axe DevTools Extension, abre la página desplegada en el navegador con la extensión instalada, ejecuta el escaneo desde DevTools y conserva una captura del panel en `Evidencias/accesibilidad/axe-devtools-extension/`. El informe Lighthouse se obtiene con Chrome DevTools sobre `/productos` y se conserva como PDF en `Evidencias/auditoria-web/lighthouse/`.

Cada nueva ejecución debe registrar fecha, versión probada, ambiente, resultado y archivos producidos en `Evidencias/registro-ejecuciones.csv`. Los resultados ya obtenidos, sus límites y la relación con los casos se exponen en el informe del proyecto.
