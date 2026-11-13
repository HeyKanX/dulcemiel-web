# Fase 3 — Métricas de calidad trazadas a OE1–OE7

**Corte:** 13 de noviembre de 2026  
**Proyecto:** Dulce Miel  
**Fuente del mapa de objetivos:** rúbrica compartida por el equipo.  
**Política de lectura:** cada cifra conserva su fuente, ejecución y denominador. Los datos locales de la fase 2 no se combinan con el build remoto #8 para fabricar un único pass rate.

**Integración CI:** el mapa OE1–OE7 está conectado al generador de JSON/HTML usado por Jenkins y GitHub Actions. Cada nueva corrida publicará la relación entre objetivo, indicadores, meta de rúbrica y límites de medición en sus artefactos. El generador no asigna porcentajes globales de cumplimiento por objetivo.

## 1. Mapa oficial de objetivos

Se usa la asignación de siete objetivos de la rúbrica del proyecto:

| OE | Objetivo | Indicadores/evidencia de fase 3 |
|---|---|---|
| OE1 | Historias de Usuario y Criterios de Aceptación | Trazabilidad HU/CA ↔ caso; requisitos y criterios cubiertos / total identificado. |
| OE2 | Diseño de Casos de Prueba | Casos únicos; integridad de campos; cobertura de escenarios positivos, negativos y límites; reproducibilidad. |
| OE3 | Pruebas Unitarias, de Integración y TDD | Conteo pass/fail/omitidas por suite, cobertura JaCoCo y evidencia de integración con SQL real/TDD. |
| OE4 | Pruebas Funcionales y de Aceptación | Pass/fail por suite y por caso trazado; fallos clasificados; estados manuales separados de automatizados. |
| OE5 | Pruebas No Funcionales | Resultados K6 por perfil, accesibilidad ejecutada frente a bloqueada, seguridad y compatibilidad. |
| OE6 | Herramientas de Automatización y CI/CD | Casos automatizables enlazados, ejecución en Jenkins/GitHub Actions, Docker y publicación de resultados. Umbral de rúbrica: ≥75%. |
| OE7 | Métricas de Calidad de Software | Cobertura, análisis estático, defectos/severidad, pass/fail, defect leakage, flaky rate y automatización. Umbral de rúbrica: ≥50%. |

**Inconsistencia documental:** un borrador del informe extraído localmente enumera OE6 como métricas, OE7 como automatización y añade un OE8. Esto no coincide con la rúbrica de siete objetivos citada arriba. Para esta matriz y la evaluación solicitada, prevalece la rúbrica compartida: OE6=automatización/CI-CD y OE7=métricas. Antes de entregar el informe académico final, alinear el capítulo de objetivos con esa numeración.

## 2. Inventario del registro de pruebas

Fuente: `Informe/Registro_Casos_Prueba_Dulce_Miel_ACTUAL.xlsx`, hoja `Casos de prueba`, leído sin modificar.

- 49 filas de casos con identificador único (49/49); IDs duplicados: 0.
- Los 10 campos del formato están diligenciados en 49/49 filas: identificador, tipo/prioridad, origen HU/criterio/requisito, herramienta, caso, precondición, pasos, esperado, estado y detalle/evidencia. Esto mide integridad de celdas, no valida por sí solo la calidad semántica de cada paso.
- Estado registrado: 8 “Aprobado” y 41 “No aprobado”. Estos valores describen la versión del Excel consultada y **no** son el resultado del build #8 ni una tasa global de defectos. No se reinterpretan como pendientes.
- La hoja registra el campo de trazabilidad de origen para 49/49 casos. El porcentaje de cobertura de requisitos/CA aún requiere un inventario canónico con el total de HU y CA y una relación unívoca entre cada elemento y los IDs de caso.

## 3. Métricas disponibles y cálculos

### Ejecución integral comparable — GitHub Actions build #8

Fuente: `INFORME-METRICAS-CALIDAD-BUILD-8-2026-11-13.md`, ejecución `43366002658`, commit `885fe83e069724d622733f8d2668fee957d7a486`, QA en Docker.

| Métrica | Cálculo | Resultado y lectura |
|---|---|---|
| Cobertura de ejecución del catálogo | 36 IDs con resultado / 49 IDs | **73,47%**; 13 IDs sin resultado automatizado en ese build. No es cobertura de código. |
| Pass rate de IDs trazados | 29 aprobados / 36 ejecutados | **80,56%**. |
| Fail rate de IDs trazados | 7 no aprobados / 36 ejecutados | **19,44%**. Son casos que fallaron, no necesariamente siete defectos únicos. |
| Automatización del catálogo aplicable | 36 automatizados y enlazados / 47 aplicables | **76,60%**; satisface el umbral OE6 ≥75% para esta clasificación. Dos casos son exclusivamente manuales; 11 brechas de automatización permanecen. |
| Tasa de defectos del build | 4 defectos únicos confirmados / 36 casos ejecutados × 100 | **11,11 defectos por cada 100 casos** en ese build, con 3 de severidad media y 1 alta. No es la tasa de fallos. |
| Cobertura backend | JaCoCo del build | **45,04% líneas; 21,51% ramas; 32,08% instrucciones.** |
| Cobertura frontend | Karma/Istanbul del build | **73,40% líneas; 56,00% ramas; 58,54% funciones.** |
| Hallazgos estáticos | SpotBugs | **9 hallazgos P2** (8 clasificados como falsos positivos contextuales y 1 informativo/no confirmado tras triage). No contar como 9 defectos del producto. Solo analiza bytecode Java. |
| Flaky rate | casos con resultados diferentes / 8 repetidos | **0/8=0%** en tres repeticiones comparables de una muestra Playwright. No permite afirmar estabilidad de todas las suites. |
| Defect leakage | defectos posliberación / defectos confirmados pre+posliberación | **No medible**: no se encontró conjunto de incidencias posliberación asociado a release y periodo. N/A no equivale a cero. |
| No funcional K6 | perfiles que cumplieron umbrales / perfiles ejecutados | **6/6** en el build #8: humo, línea base, carga moderada, estrés, pico y sostenida. Conclusión válida para ese entorno QA y esos umbrales. |
| Accesibilidad automatizada | rutas escaneadas / rutas configuradas | **4/9 escaneadas; 4/4 con hallazgos entre las escaneadas.** Las otras 5 están bloqueadas/sin análisis válido, no aprobadas ni defectos confirmados. |

### Verificación local de fase 2 — evidencia distinta, no un build remoto

Fuente: `CIERRE-FASE-2-DIAGNOSTICO-FALLOS-2026-11-13.md` y `qa/artifacts/phase2-47311c38/`.

- Backend Maven: **28/28** aprobadas; incluye 7 verificaciones de integración con SQL Server real en Testcontainers y prueba identificada como TDD. Se reconciliaron los siete XML Surefire actuales; esto corrige el total de 26 que aparecía en una versión previa del cierre de fase 2.
- JaCoCo se regeneró el 13-11-2026 a partir del `backend/target/jacoco.exec` de esa ejecución local: **50,32% líneas (236/469), 29,56% ramas (107/362), 37,85% instrucciones (1.638/4.328), 53,70% métodos (58/108), 100% clases (17/17)**. El XML está en `backend/target/site/jacoco/jacoco.xml`. El comando generó el reporte sin volver a ejecutar pruebas.
- SpotBugs se volvió a invocar con la versión **4.10.5.0** definida en el pipeline. El XML presenta **9 hallazgos P2**: ocho `EI_EXPOSE_REP2` y uno `CT_CONSTRUCTOR_THROW`, con la misma clasificación contextual ya triada. El alcance sigue limitado a Java; no existe herramienta estática conectada al frontend TypeScript.
- Newman: **32 solicitudes, 33 aserciones, 0 fallidas**. Son métricas de solicitudes/aserciones de la colección en esa corrida; no deben equipararse 1:1 con IDs de TestLink.
- Behave/Selenium: **3/4 aprobadas; 1/4 no aprobada**, `TC-NF-INT-002`, reproducida al recargar el catálogo con sesión activa. Continúa abierta y sin causa raíz cerrada.
- axe: **4/9 rutas** analizadas; se encontraron nueve nodos con violaciones, agrupados en cinco grupos de regla/página. Las rutas protegidas que redirigieron al login permanecen sin conclusión.
- Registro acumulado de defectos actual: seis hallazgos de accesibilidad confirmados y abiertos (2 altos, 4 medios); dos defectos funcionales confirmados corregidos solo en la copia local, aún pendientes de build remoto; un fallo de integración reproducible pendiente de causa raíz. Este inventario cruza corridas, así que no se divide por 36 ni se presenta como tasa del build #8.

## 4. Estado de cierre por objetivo

| OE | Estado de medición | Conclusión con evidencia actual | Pendiente para declarar cumplimiento académico |
|---|---|---|---|
| OE1 | Parcial | 49/49 casos incluyen referencia de origen; no hay denominador canónico de HU/CA validado aquí. | Importar la lista definitiva de HU y CA y calcular cobertura por IDs. |
| OE2 | Parcialmente medido | 49 casos únicos; todos tienen las 10 columnas no vacías. | Revisar semántica de datos y pasos, reproducibilidad y positivo/negativo/límite contra cada HU/CA. |
| OE3 | Medido en local; CI pendiente | Maven 28/28; 7 integraciones SQL; TDD incluido. JaCoCo local actualizado: 50,32% líneas y 29,56% ramas. El build #8 anterior fue 20/21 y no debe confundirse con la corrección local. Las correcciones se trasladaron al PR #8 para la validación remota. | Confirmar el build del PR y que los reportes se generen juntos en esa corrida. |
| OE4 | Medido con fallos visibles | Build #8: 29/36 aprobados. En local, Newman 0/33 aserciones fallidas y Behave 3/4. | Diagnosticar `TC-NF-INT-002` y reconciliar resultados con IDs/TestLink de la misma corrida. |
| OE5 | Parcial | K6 6/6 en build #8; accesibilidad automática 4 rutas con hallazgos, 5 sin análisis; manuales de teclado/Narrador separados. | Acceder a rutas protegidas con sesión QA en el runner y volver a escanear; mantener resultados manuales con evidencia propia. |
| OE6 | Supera el umbral de clasificación actual | 36/47=76,60%, sobre el 75% solicitado. CI con Jenkins/GitHub Actions y Docker está documentado. | Confirmar artefactos del build más reciente y que publicación TestLink use resultados frescos. Las correcciones de fase 2 están en PR y aún esperan validación CI. |
| OE7 | Métricas calculadas, cierre parcial | Se calculan cobertura, tasa/severidad, pass/fail, flaky y automatización. | Defect leakage sigue N/A; no asignar porcentaje global de OE7 hasta que la rúbrica defina ponderación y criterio de aceptación por submétrica. Actualizar métricas tras el nuevo build integrado. |

## 5. Interpretación y acciones para culminar la fase 3

1. Mantener el build #8 como línea base integral comparable y la corrida local de fase 2 como evidencia de diagnóstico/corrección separada.
2. Validar en el PR #8 las correcciones de `TC-F-010` y `TC-F-017` con un build completo. El build debe conservar su estado fallido si Behave, accesibilidad u otra prueba reproduce un problema.
3. Generar JaCoCo y todos los reportes de suites dentro de ese mismo build; publicar un `quality-summary.json`/HTML nuevo, JUnit y los perfiles K6 bajo el ID de ejecución correspondiente.
4. Reconciliar IDs y resultados del `quality-summary.json` con TestLink después del build; verificar que el número de ejecuciones por ID y los estados coincidan. No volver a publicar datos históricos como si fueran nuevos.
5. Mantener `TC-NF-INT-002` abierto hasta aislar si el origen es la aplicación, el arranque SPA, el proxy o el fixture. No cambiar el criterio de prueba para convertirlo en aprobado.
6. Definir con el equipo fuente, periodo y vínculo de incidencias posliberación para defect leakage. Hasta entonces, reportar N/A con motivo.
7. La rúbrica no especifica ponderación de las submétricas de OE7. El informe puede demostrar qué métricas están implementadas y cuáles tienen datos; no puede afirmar “OE7=50%” mediante una ponderación inventada.

## 6. Fuentes y límites

- `qa/docs/INFORME-METRICAS-CALIDAD-BUILD-8-2026-11-13.md` — ejecución CI integral comparable.
- `qa/docs/CIERRE-FASE-2-DIAGNOSTICO-FALLOS-2026-11-13.md` — verificación local posterior y límites de publicación.
- `qa/docs/ESQUEMA-METRICAS-CALIDAD.md` — fórmulas, denominadores y reglas de interpretación.
- `qa/metrics/automation-classification.json` — conteos 36/11/2 y mapeo por caso.
- `qa/metrics/defect-register.json` — defectos abiertos/corregidos localmente y estado de causa raíz.
- `qa/metrics/stability-baseline.json` — tres repeticiones idénticas de los mismos ocho casos Playwright.
- `qa/metrics/objective-map.json` y `qa/metrics/generate_quality_report.py` — mapa OE versionado y su salida en el reporte de cada build Jenkins/GitHub Actions.
- `Informe/Registro_Casos_Prueba_Dulce_Miel_ACTUAL.xlsx`, hoja `Casos de prueba` — 49 filas y 10 columnas, consultado en modo lectura.

