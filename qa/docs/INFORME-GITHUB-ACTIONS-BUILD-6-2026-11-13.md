# Revisión de calidad — GitHub Actions build 6

**Ejecución:** [Dulce Miel - Calidad automatizada #6](https://github.com/HeyKanX/dulcemiel-web/actions/runs/43360758317)

**Commit:** `d6c15201d034a6098b5fee455f0a6c30e2030092`

**Ambiente:** Docker Compose QA efímero; no se desplegó a producción.

**Resultado:** el job ejecutó las suites, generó el reporte y adjuntó el artefacto, pero el Quality Gate terminó fallido por pruebas no aprobadas.

## Resultados del build

| Suite / métrica | Resultado | Interpretación |
|---|---:|---|
| Backend JUnit | 20/21 aprobadas; 1 no aprobada | La prueba de cantidad cero esperaba HTTP 400 y recibió HTTP 201. Las 5 pruebas Testcontainers/SQL Server pasaron. El resumen automático de este build mostró backend como bloqueado por un error del parser de reportes, aunque los XML JUnit sí están en el artefacto; el código ya quedó corregido para corridas siguientes. |
| Frontend unitario | 8/8 aprobadas | Sin fallos en esta corrida. |
| Newman | 29/31 aserciones aprobadas; 2 fallidas en 30 solicitudes | Cantidad cero recibió 201 en vez de 400. La creación administrativa de producto recibió 500 en vez de 201; la causa no está identificada y no se clasificó aún como defecto confirmado. |
| Behave/Selenium | 0/10 aprobadas | Los 10 casos terminaron en `Invalid Host header`; la página Angular no se sirvió al contenedor del navegador. Se clasifica como problema de configuración del entorno QA, no como 10 defectos de aplicación. |
| Compatibilidad Playwright | 0/6 aprobadas | Las comprobaciones no encontraron el título porque recibieron la página de error de host. Mismo bloqueo ambiental que Selenium. |
| axe-core | 0/8 rutas evaluadas correctamente | Las 8 rutas agotaron el tiempo de espera esperando el contenido Angular; el host inválido impidió evaluar accesibilidad. Estos resultados no demuestran ocho fallos de accesibilidad de la aplicación. |
| Casos automatizados trazables | 28/49 casos con resultado; 14 aprobados y 14 no aprobados | Pass rate 50%; cobertura de ejecución del catálogo 57,14%. Los fallos de entorno influyen en el fail rate; por eso no equivale a la tasa de defectos. |

## Rendimiento K6

Los seis perfiles cumplieron sus umbrales, con 0% de solicitudes fallidas: humo (30 s), línea base (3 VUs, 2 min), moderada (8 VUs, 3 min), estrés progresivo (hasta 600 VUs, 4 min), pico (hasta 1000 VUs, 50 s) y sostenida (100 VUs, 10 min). En pico, API p95 fue 4,21 ms y página p95 16,36 ms. En sostenida, API p95 fue 3,86 ms y página p95 7,06 ms. Las cifras describen el ambiente efímero del build, no producción.

## Métricas de código y calidad

- **Cobertura JaCoCo backend:** líneas 45,04%; ramas 21,51%; instrucciones 32,08%; métodos 48,15%.
- **Cobertura Angular:** líneas 73,40%; statements 74,23%; ramas 56,00%; funciones 58,54%.
- **SpotBugs:** 9 hallazgos P2 (8 `EI_EXPOSE_REP2`, 1 `CT_CONSTRUCTOR_THROW`); requieren triage y no son automáticamente defectos confirmados.
- **Defectos enlazados a fallos de este build:** 1 confirmado, severidad media (cantidad cero); 3,57 defectos únicos por 100 casos trazables ejecutados (1/28). El 500 del alta administrativa queda pendiente de diagnóstico.
- **Flaky rate:** la línea base de repetición local de ocho casos continúa en 0/8 = 0,00% en tres corridas con el mismo fingerprint; el build 6 no repitió sus suites y por sí solo no mide flakiness.
- **Automatización del catálogo:** 36/47 = 76,60%; 11 casos con brecha y 2 solo manuales. El 57,14% de ejecución en el build es otra medida.
- **Defect leakage:** no medible; no hay registro posliberación vinculado a versiones y periodo de observación.

## Correcciones aplicadas para la siguiente corrida

1. Se añadió `--allowed-hosts frontend` únicamente al servidor de desarrollo del contenedor QA. Esto no cambia el código ni el despliegue de la aplicación. La opción se comprobó localmente: el servidor aceptó `Host: frontend` y `Host: frontend:4200`.
2. Se corrigió el generador para que no descarte reportes JUnit de backend que se generaron antes de crear la carpeta de artefactos QA. Jenkins y GitHub Actions usan espacios de trabajo limpios; el filtro de antigüedad se limita al análisis local.
3. Se añadió a GitHub Actions la suite automatizada de ocho casos Playwright seleccionados que ya corría en Jenkins.

Las correcciones mantienen visibles los fallos reales; no se modificaron las reglas de negocio para forzar aprobaciones. La siguiente corrida de GitHub Actions verificará el host QA y mostrará el conteo JUnit corregido. La publicación a TestLink quedó omitida en el build 6; el paso de validación de IDs sí terminó correctamente.

## Evidencia

- Artefacto remoto: `dulce-miel-quality-6-1` del build 6.
- Reporte JSON descargado: `qa/artifacts/github-actions-build-6/dulce-miel-quality-6-1/qa/metrics/reports/43360758317/quality-summary.json`.
- JUnit backend: `qa/artifacts/github-actions-build-6/dulce-miel-quality-6-1/backend/target/surefire-reports/`.
- Newman, Behave, axe, compatibilidad y K6: `qa/artifacts/github-actions-build-6/dulce-miel-quality-6-1/qa/artifacts/build-6-53500816/`.
