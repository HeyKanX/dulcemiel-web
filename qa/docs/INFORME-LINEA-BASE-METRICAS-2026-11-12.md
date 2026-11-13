# Línea base de métricas de calidad — Dulce Miel

**Fecha:** 12 de noviembre de 2026

**Ambiente:** QA local; backend probado con SQL Server efímero de Testcontainers.

**Build:** `local-metrics-2026-11-12`
**Alcance:** Maven/JUnit, Angular/Karma y ocho casos Playwright seleccionados. No equivale a una ejecución completa de todas las suites de Jenkins.

## Resultados ejecutados

| Medida | Resultado | Lectura |
|---|---:|---|
| Backend JUnit | 20/21 aprobadas; 1 no aprobada | Pass rate 95,24%; falla la validación de cantidad cero, que esperaba HTTP 400 y recibió HTTP 201. Las cinco pruebas con SQL Server pasaron. |
| Frontend unitario | 8/8 aprobadas | Pass rate 100% en esta corrida. |
| Playwright seleccionado | 5/8 aprobadas; 3 no aprobadas | Fallan TC-NF-ACC-004, TC-NF-ACC-008 y TC-NF-ACC-009, reproducidas en tres corridas. |
| Resultados trazables a TestLink en este resumen | 10 aprobados; 4 no aprobados, 14 IDs únicos | Pass rate 71,43%; fail rate 28,57%. Se calcula por ID único y no incorpora las 8 pruebas unitarias de frontend porque no están enlazadas a IDs del catálogo en el publicador. |
| Cobertura de ejecución del catálogo | 14/49 = 28,57% | Solo IDs con resultado automatizado en este build local; no es cobertura de código ni automatización del catálogo. |

## Métricas estáticas y de código

- **JaCoCo backend:** líneas 45,26% (210/464), ramas 21,79% (78/358), instrucciones 32,47% (1394/4293), métodos 48,15% (52/108).
- **Angular/Karma:** líneas 73,40% (69/94), statements 74,22% (72/97), ramas 56,00% (14/25), funciones 58,53% (24/41).
- **SpotBugs:** 9 hallazgos de prioridad P2: 8 `EI_EXPOSE_REP2` y 1 `CT_CONSTRUCTOR_THROW`. P2 es prioridad asignada por el analizador; son hallazgos que requieren triage, no nueve defectos confirmados.
- El análisis estático cubre bytecode Java del backend. No se integró un analizador estático específico para TypeScript/Angular.

## Defectos y severidad

El registro contiene cuatro defectos únicos confirmados, abiertos y enlazados a fallos del resumen actual: uno de cantidad cero en carrito y tres de accesibilidad. Sobre 14 IDs únicos ejecutados, la tasa descriptiva es **28,57 defectos por cada 100 casos ejecutados**. Distribución: 1 alta y 3 media. No interpretar esta tasa como probabilidad de fallo; un defecto puede ser detectado por más de un caso y el conteo deduplica por ID de defecto.

El triage de accesibilidad se basa en fallos reproducidos tres veces y corroborados en el DOM/plantillas vigentes. La falla de cantidad cero se confirmó en la repetición limpia de Maven el 12-11-2026. No se modificó código de backend ni frontend para obtener aprobaciones.

## Flakiness, automatización y fuga a producción

- **Flaky rate:** 0/8 = 0,00% en tres repeticiones secuenciales de Playwright con el mismo fingerprint del código y runner. Esto solo describe esos ocho casos y ese ambiente; no prueba estabilidad de todas las suites ni de Jenkins.
- **Automatización del catálogo:** 36/47 = **76,60%** de los casos aplicables tienen una fuente automatizada enlazada. Hay 11 brechas y 2 casos manuales puros. Los dos manuales se excluyen del denominador; las brechas se mantienen dentro.
- **Defect leakage:** **No medible**, no cero. No se dispone de incidencias confirmadas posliberación enlazadas a una versión y a un periodo de observación. Los fallos de QA no permiten inferir fuga.

## Acciones sustentadas por evidencia

1. Priorizar la validación de `cantidad > 0` antes de cualquier lectura/escritura de carrito; mantener la prueba fallida hasta que el comportamiento real cambie y repetir Maven.
2. Corregir etiquetas programáticas de filtros de catálogo y checkout, y anunciar cambios de cantidad con una región de estado accesible; volver a correr los tres casos Playwright fallidos.
3. Triar individualmente los nueve hallazgos SpotBugs y registrar decisión/riesgo; no contarlos como defectos de producto sin confirmación.
4. Reducir las brechas de automatización, empezando por los once casos clasificados `automation_gap`; mantener Narrador y recorridos manuales como manuales.
5. Crear historial de liberación e incidencias por versión para medir defect leakage.
6. Repetir una ejecución integral en Jenkins y GitHub Actions y archivar ambos artefactos. La corrida local no sustituye ni confirma esos builds remotos.

## Archivos de evidencia

- JSON: `qa/artifacts/metrics-local-2026-11-12/metrics/quality-summary.json`
- HTML: `qa/artifacts/metrics-local-2026-11-12/metrics/quality-report.html`
- Resumen trazable local: `qa/artifacts/metrics-local-2026-11-12/current-run.json` (generado para análisis; no publicado a TestLink).
- JUnit backend: `backend/target/surefire-reports/`
- JaCoCo: `backend/target/site/jacoco/jacoco.xml`
- SpotBugs: `backend/target/spotbugsXml.xml`
- Cobertura frontend: `frontend/coverage/ihc-frontend/index.html`
- Repeticiones Playwright y capturas: `qa/artifacts/pending-playwright-integration-final/`, `qa/artifacts/pending-playwright-flaky-2/`, `qa/artifacts/pending-playwright-flaky-3/`
- Clasificación de catálogo: `qa/metrics/automation-classification.json`
- Registro de defectos: `qa/metrics/defect-register.json`
- Línea base de estabilidad: `qa/metrics/stability-baseline.json`

La publicación a TestLink quedó omitida en esta medición local. Solo se debe publicar desde el pipeline cuando el resumen corresponda al build actual.
