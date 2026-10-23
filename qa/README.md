# Auditoría del criterio 5 de Dulce Miel

Esta carpeta es la única raíz de pruebas funcionales, de aceptación y no funcionales añadidas al checkout `Auditoria/codigo-auditado`. El código productivo auditado corresponde a `9e46844`; los resultados negativos son hallazgos de la auditoría. La fuente de HU/CA es la Tabla C2 del Anexo C del informe. `cases.csv` contiene 34 casos CA y 10 casos no funcionales adicionales, con precondiciones, datos, pasos, esperado, técnica, prioridad y trazabilidad. `estado=no ejecutado` se sustituye solo a partir de evidencia de una corrida identificada.

## Mapa de herramientas

| Ruta | Propósito |
|---|---|
| `features/*.feature` y `features/steps/` | Aceptación Gherkin con Behave y Selenium; selectores compartidos en `pages/`. |
| `tests/functional/dulcemiel.postman_collection.json` | API funcional con Postman/Newman: 32 solicitudes diseñadas, incluyendo CA11, pedido, seguimiento y permisos administrativos. |
| `tests/non-functional/playwright_compatibility.py` | Compatibilidad de motores y anchos; cobertura complementaria RNF04/CA32. |
| `tests/non-functional/accessibility_audit.py` | Exploración con axe-core; requiere confirmación manual para un defecto. |
| `tests/non-functional/k6/catalogo.js` | Rendimiento de lectura local con perfiles smoke, baseline y moderate. |
| `infra/` | SQL Server aislado, producto Miel QA y cuenta administrativa sintética. |

## Preparación del ambiente Windows

Desde `qa/`, ejecutar `npm ci` y `py -m pip install -r requirements.txt`. Instalar los navegadores con `py -m playwright install chromium firefox webkit`. Behave usa Chrome instalado mediante Selenium Manager. Para k6, usar `C:\Program Files\k6\k6.exe` si no aparece en PATH.

Ejecutar `./infra/bootstrap.ps1` una vez. Crea exclusivamente `dulce-miel-qa-c5` en `127.0.0.1:14333`, aplica `backend/database/schema.sql` y añade `Miel QA` (precio 12.50, stock 5) y `qa_admin@example.test` para las solicitudes administrativas. El script del esquema elimina tablas: nunca apuntarlo al contenedor habitual. El secreto SQL se guarda solo en `qa/.local/connection.json`, ignorado por Git. El script no restablece una instancia existente; para repetir con base limpia se necesita inspeccionar y retirar explícitamente el contenedor QA identificado.

En una terminal iniciar `./infra/run-backend.ps1`. Empaqueta el backend y lo ejecuta en `127.0.0.1:5000` con conexión a la instancia QA; no depende de `.env` del proyecto original. En otra terminal, desde `frontend/`, iniciar `npm start -- --host 127.0.0.1 --port 4200`. Confirmar que `http://127.0.0.1:5000/api/productos` contiene `Miel QA` y que la tienda local abre en `http://127.0.0.1:4200/productos`.

## Corridas

En PowerShell desde `qa/`:

```powershell
$env:QA_ISOLATED_DB = '1'
$env:QA_RUN_ID = (Get-Date -Format 'yyyyMMdd-HHmmss')
$env:QA_ARTIFACTS = '..\..\evidencias-criterio5'
py -m behave features --lang es --junit --junit-directory '..\..\evidencias-criterio5' -f progress
.\node_modules\.bin\newman.cmd run .\tests\functional\dulcemiel.postman_collection.json -r cli,junit --reporter-junit-export '..\..\evidencias-criterio5\api-newman.xml'
py tests/non-functional/playwright_compatibility.py
py tests/non-functional/accessibility_audit.py
& 'C:\Program Files\k6\k6.exe' run -e QA_LOAD_PROFILE=smoke -e QA_K6_SUMMARY=..\..\evidencias-criterio5\k6-smoke.json .\tests\non-functional\k6\catalogo.js
```

Para `baseline` y `moderate`, repetir k6 con el perfil y un nombre de resumen propio, después de revisar CPU, memoria y estabilidad del SQL QA. No aplicar carga a servicios publicados. Los umbrales de RNF03 están declarados antes de medir: API p95 ≤ 2 s y página p95 ≤ 3 s. k6 mide la respuesta HTTP de la página, no tiempo de renderizado; esa limitación debe constar en el informe. `QA_WEB_URL` y `QA_API_URL` solo aceptan localhost o 127.0.0.1.

## Evidencia y revisión humana

Por cada corrida registrar fecha, commit, versión de herramientas, contenedor SQL, perfiles, datos, salidas, capturas, métricas y decisión humana en `../../evidencias-criterio5/`. Los fallos de aserción se conservan. Si una corrida es inválida por preparación o herramienta, se archiva como tal y se repite con una nueva identificación. No registrar tokens, contraseñas ni respuestas que incluyan datos de usuarios en los artefactos compartidos. Las salidas axe son hallazgos automáticos por regla y elemento; completar la lista manual de teclado, foco, zoom 200 %, lector y contraste antes de atribuir conformidad WCAG.

La cobertura de diseño se calcula sobre los 34 CA de la Tabla C2. Informar por separado casos automatizados, ejecutados, aprobados, fallidos, bloqueados y no ejecutados. Una prueba parcial no aprueba el CA completo. En la corrida registrada, la creación administrativa sin imagen respondió 500 y bloqueó las dos solicitudes que dependían de su identificador; `cases.csv` y el informe técnico documentan el alcance exacto.
