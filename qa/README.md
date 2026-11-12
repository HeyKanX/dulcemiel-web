# Ejecutar las pruebas de Dulce Miel

Todos los comandos de esta página se ejecutan en **PowerShell desde `codigo-auditado/`**. Se necesita Java 21 o posterior (validado también con Java 25), Node.js/npm, Python (`py`), Docker, k6 y Chrome/Chromium para Selenium y Karma; la prueba axe-core requiere conexión al despliegue público. El diseño de los casos está en el Anexo F del informe; aquí solo se indica cómo ejecutar los tests.

## Preparar una vez

```powershell
.\qa\run-tests.ps1 -Suite setup
```

Este comando instala las dependencias de `qa/` y `frontend/`, instala los navegadores de Playwright y prepara la base SQL aislada. Si la base ya existe, conserva sus datos.

Para las pruebas de interfaz, API, compatibilidad y rendimiento, deja abiertos estos dos procesos en **terminales separadas**:

```powershell
.\qa\infra\run-backend.ps1
```

```powershell
cd frontend
npm start -- --host 127.0.0.1 --port 4200
```

Vuelve a `codigo-auditado/` en una tercera terminal para ejecutar las pruebas.

## Una suite o todas

| Prueba | Comando desde `codigo-auditado/` |
|---|---|
| Unitarias e integración Java; cobertura JaCoCo | `.\qa\run-tests.ps1 -Suite backend` |
| Unitarias Angular; cobertura Karma | `.\qa\run-tests.ps1 -Suite frontend` |
| Funcionales de interfaz, Behave/Selenium | `.\qa\run-tests.ps1 -Suite ui` |
| Funcionales de API, Newman | `.\qa\run-tests.ps1 -Suite api` |
| Compatibilidad, Playwright | `.\qa\run-tests.ps1 -Suite compat` |
| Rendimiento, k6 | `.\qa\run-tests.ps1 -Suite k6 -Profile smoke` |
| Accesibilidad exportable, axe-core | `.\qa\run-tests.ps1 -Suite axe` |
| **Todas las suites automatizadas** | **`.\qa\run-tests.ps1 -Suite all`** |

Para ejecutar **un caso o clase concreta**:

```powershell
.\qa\run-tests.ps1 -Suite ui -Tag TC-F-001
.\qa\run-tests.ps1 -Suite backend -Test JwtServiceTest
```

Para k6, cambia `smoke` por `baseline` o `moderate`. Los valores actuales están en `qa/tests/non-functional/performance/k6/catalogo.js`: `smoke` = 1000 usuarios virtuales durante 30 s; `baseline` = 500 durante 2 min; `moderate` = 100 durante 3 min. Cada ejecución usa un solo perfil. axe-core analiza el despliegue público por defecto; usa `-BaseUrl` para indicar otro origen.

El lanzador muestra el resultado en consola y guarda logs, XML, capturas y reportes en `../Evidencias/<tipo>/<herramienta>/<fecha-hora>/`. Una suite con fallos conserva sus archivos y el comando completo termina con error; en `-Suite all` las demás suites continúan. Las pruebas Java usan `mvnw test` y `jacoco:report`, de modo que se pueden ejecutar con el backend de QA activo sin intentar limpiar el JAR en uso.

axe DevTools Extension y Lighthouse se ejecutan desde el navegador; sus capturas y PDF se conservan en `../Evidencias/accesibilidad/axe-devtools-extension/` y `../Evidencias/auditoria-web/lighthouse/`.
