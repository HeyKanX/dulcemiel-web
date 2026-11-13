# Índice de informes de calidad

Este índice organiza los documentos del expediente sin duplicar resultados. Los archivos originales de cada ejecución se conservan por separado bajo `qa/artifacts/` y `qa/metrics/reports/<runId>/`.

## Fase 1 — diseño y ejecución de casos

- Registro vigente: `../../../../Informe/Registro_Casos_Prueba_Dulce_Miel_ACTUAL.xlsx` (carpeta Informe, hermana de `Desarrollo`).
- Procedimiento de ejecución: `../../../../Informe/GUIA_EJECUCION_PENDIENTES_FASE1.md`.
- Cierre y criterios de la fase: `../../../../Informe/CIERRE_FASE_1_CASOS_DE_PRUEBA.md`.
- Las versiones anteriores del Excel se conservan bajo `../../../../Informe/Historicos/Casos-de-prueba/`.

## Fase 2 — diagnóstico de fallos

- `CIERRE-FASE-2-DIAGNOSTICO-FALLOS-2026-11-13.md`: diferencia fallos de producto, prueba, datos y entorno, y enlaza evidencia reproducible.

## Fase 3 — métricas de calidad

- `FASE-3-METRICAS-OE1-OE7-2026-11-13.md`: estado por OE, fórmulas, valores, fuentes y límites de interpretación.
- `ESQUEMA-METRICAS-CALIDAD.md`: definiciones, denominadores, reglas de clasificación y evidencia exigida.
- `fase-3/CI-BUILD-15-METRICAS-2026-11-13.md`: lectura detallada y trazada a OE del build 15; se conserva como evidencia histórica del candidato con correcciones.
- `INFORME-LINEA-BASE-METRICAS-2026-11-12.md` y los informes de builds anteriores: antecedentes históricos; no reemplazan un build actual.
- Los registros fuente están en `qa/metrics/` y sus copias por corrida en `qa/metrics/reports/<runId>/`.

## Fase 4 — informe final y matriz OE1–OE7

- El informe académico editable y sus versiones se conservan en `../../../../Informe/`.
- La matriz de objetivos se vincula con `qa/metrics/objective-map.json`; no se calcula un porcentaje global de OE si la rúbrica no define ponderaciones.
- El HTML y el JSON de cada build se generan juntos a partir del mismo resumen; ambos deben referir al mismo build, commit y entorno.

## Regla para interpretar resultados

Cada porcentaje debe mostrar numerador, denominador, unidad y corrida fuente. Toda cifra debe explicar qué representa, qué permite concluir y qué no demuestra. Un `N/A` explica la falta de base de medición; nunca equivale a cero. Un caso no aprobado no se convierte en defecto confirmado hasta que se clasifique y se deduplique con evidencia.
