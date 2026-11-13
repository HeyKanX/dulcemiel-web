# Registro y reportes de métricas

## Fuentes estructuradas versionadas

- `objective-map.json`: definición de OE1–OE7, indicadores, metas y límites.
- `automation-classification.json`: clasificación por caso; la tasa de automatización excluye casos exclusivamente manuales del denominador e incluye brechas automatizables.
- `defect-register.json`: un registro por defecto raíz, con casos asociados, módulo, versión, severidad, estado y fecha registrada. `first_observed_on` queda vacío cuando la fuente no aporta la fecha real de detección.
- `stability-baseline.json`: repeticiones controladas; solo se calcula flaky rate cuando código, conjunto y entorno coinciden.
- `coverage-targets.json`: línea base CI por congelar y aumentos por etapas. Un umbral `null` indica que el valor estable todavía no se ha medido.
- `typescript-baseline.json`: reglas TypeScript existentes frente a las cuales se clasifican diagnósticos nuevos.

## Salidas por ejecución

`reports/<runId>/quality-summary.json` y `quality-report.html` se generan desde los mismos reportes de la corrida. Los XML JUnit, cobertura JaCoCo/Karma, XML SpotBugs, diagnósticos TypeScript, resultados axe, Newman, Playwright y resúmenes K6 se archivan como evidencia del build que los generó.

El reporte HTML explica los conteos, unidades, fórmulas y denominadores. Resultados por suite con unidades distintas (pruebas JUnit, aserciones HTTP y casos de aceptación) no se suman entre sí. Cobertura de código, cobertura de ejecución del catálogo y tasa de automatización se presentan como métricas diferentes.

## Límites

- Defect leakage es `N/A` sin defectos posliberación vinculados a una versión y periodo observado.
- La severidad informada por un analizador no sustituye el triage de impacto del defecto.
- Los resultados manuales no se incluyen en el pass/fail automático del pipeline.
- El cumplimiento porcentual de cada OE solo se calcula si existe una fórmula y ponderación aprobada en la rúbrica.
