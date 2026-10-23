# Pruebas de calidad de Dulce Miel

Esta carpeta concentra los artefactos de prueba y mantiene separado el código productivo. El código auditado corresponde al commit `9e46844`. Las pruebas del backend Java están en `backend/src/test`, conforme a la estructura Maven; las pruebas unitarias de Angular están en `frontend/tests/unit`.

## Organización

```text
qa/
  test-design/                 Catálogo de casos diseñados
  test-runs/                   Resultados por corrida
  tests/
    functional/
      api/                     Colección Newman
      features/                Escenarios Gherkin (palabras clave en inglés, pasos en español)
        steps/                 Definiciones Behave separadas por funcionalidad
      pages/                   BasePage y Page Objects Selenium
      testsupport/             Fábrica y configuración del navegador
    non-functional/
      accessibility/           Lista manual para axe DevTools y revisión humana
      compatibility/           Playwright
      performance/k6/          Escenario de carga local
  infra/                       SQL de prueba y arranque aislado
  utils/                       Exportación, consolidación y reportes
```

`test-design/cases.csv` describe los casos: base, tipo, nivel, requisito o criterio, precondiciones, datos, pasos y resultado esperado. `test-runs/executions.csv` registra la corrida, el resultado observado, la evidencia y el defecto asociado. Una fila del catálogo no significa que el caso se haya ejecutado.

La guía de términos, la relación con los criterios de la rúbrica y la interpretación del conteo se encuentra en `docs/terminologia-y-rubrica.md`.

El flujo que conecta requisito, criterio, caso diseñado, escenario automatizado, ejecución, evidencia y defecto se documenta en `docs/flujo-de-automatizacion.md`. Sigue los patrones pertinentes de las prácticas disponibles de las semanas 5, 8 y 9, adaptados al entorno y a los tipos de prueba de Dulce Miel.

## Herramientas

El proyecto organiza las comprobaciones con JUnit 5, Mockito, Spring Boot Test, MockMvc, Testcontainers, JaCoCo, Jasmine/Karma, Karma Coverage, Behave/Selenium, Playwright, Postman/Newman, Grafana k6, axe DevTools Extension y axe-core.

JaCoCo se ejecuta en el backend y genera cobertura de las clases Java probadas; Karma Coverage se usa para Angular. Las métricas deben informarse por componente y acompañarse de lectura de los casos límite y del código no cubierto.

## Preparación del entorno local

Desde `qa/`, instalar las dependencias de Node y Python:

```powershell
npm ci
py -m pip install -r requirements.txt
py -m playwright install chromium firefox webkit
```

Ejecutar `./infra/bootstrap.ps1` una vez para crear exclusivamente la base aislada `dulce-miel-qa-c5` en `127.0.0.1:14333`. El script del esquema elimina tablas, por lo que el contenedor de QA no se debe apuntar a la base de trabajo.

En una terminal de `qa/`, iniciar el backend con `./infra/run-backend.ps1`. En otra terminal, desde `frontend/`, iniciar Angular con `npm start -- --host 127.0.0.1 --port 4200`. Confirmar la disponibilidad de la API local y el catálogo en el navegador.

## Ejecución de pruebas

Desde la raíz `qa/`, para Gherkin y Selenium:

```powershell
$env:QA_ISOLATED_DB = '1'
$env:QA_RUN_ID = (Get-Date -Format 'yyyyMMdd-HHmmss')
$env:QA_ARTIFACTS = '..\..\evidencias-criterio5'
py -m behave tests/functional/features --lang en --junit --junit-directory '..\..\evidencias-criterio5' -f progress
```

Para la colección API y las verificaciones de compatibilidad:

```powershell
.\node_modules\.bin\newman.cmd run .\tests\functional\api\dulcemiel.postman_collection.json -r cli,junit --reporter-junit-export '..\..\evidencias-criterio5\api-newman.xml'
py tests/non-functional/compatibility/playwright_compatibility.py
```

Para el perfil local de rendimiento:

```powershell
& 'C:\Program Files\k6\k6.exe' run -e QA_LOAD_PROFILE=smoke -e QA_K6_SUMMARY=..\..\evidencias-criterio5\k6-smoke.json .\tests\non-functional\performance\k6\catalogo.js
```

Los perfiles smoke, baseline y moderate usan solo localhost. Las metas previas son p95 de API ≤ 2000 ms, p95 de página HTTP ≤ 3000 ms y errores < 5 %. La latencia de página mide la respuesta HTTP inicial, no el tiempo de renderizado o interacción.

Para las pruebas unitarias y la cobertura:

```powershell
# En frontend/
npm run test:coverage

# En backend/
.\mvnw.cmd clean verify
```

JaCoCo deja el informe HTML en `backend/target/site/jacoco/index.html` y datos en formato XML junto al informe. La suite de integración necesita Docker para levantar SQL Server con Testcontainers.

## Accesibilidad

La verificación con axe DevTools Extension y las tareas manuales de teclado, foco, zoom, contraste y lector de pantalla se describen en `tests/non-functional/accessibility/axe-devtools-checklist.md`. Registrar cada resultado y su evidencia en `tests/non-functional/accessibility/manual_review.csv`. Los hallazgos automáticos necesitan revisión humana antes de clasificarse como defectos.

La revisión automatizada reproducible con axe-core se ejecuta mediante `tests/non-functional/accessibility/axe_core_scan.py`. La corrida del 23 de octubre de 2026 sobre las pantallas públicas desplegadas y sus límites se documenta en `test-runs/axe-core-2026-10-23.md`. Sus resultados no completan por sí solos las tareas manuales de `manual_review.csv`.

La medición Lighthouse del catálogo desplegado del mismo día está resumida en `test-runs/lighthouse-2026-10-23.md`, con el PDF original en `../../evidencias-criterio5/lighthouse/20261023-publico/`. Su puntuación de accesibilidad y la corrida axe-core se informan como mediciones distintas; ambas señalan el selector de categoría sin nombre accesible.

## Evidencia y estados

Por corrida, conservar fecha, commit, ambiente, datos sintéticos, salida, capturas, métricas y decisión humana bajo `../../evidencias-criterio5/`. No guardar credenciales ni tokens en Git. Los estados parciales no cuentan como aprobación íntegra del criterio; los casos no ejecutados quedan fuera de los porcentajes de aprobación.

El ciclo de Behave/Selenium inicia un navegador por escenario, comprueba el aislamiento para los escenarios `@writes`, guarda captura y texto de página al terminar, y cierra el navegador. La preparación de datos vía API se usa cuando el escenario requiere una cuenta previamente creada; las acciones de interfaz se verifican en Selenium. Consulta `docs/flujo-de-automatizacion.md` antes de añadir casos para conservar esta separación.
