# Esquema propuesto de métricas de calidad — Dulce Miel

**Estado:** generador y etapas de análisis/cobertura integrados en Jenkins y GitHub Actions; línea base local medida el 12-11-2026. La publicación real de cada build debe verificarse en el artefacto de la plataforma.
**Alcance:** pruebas automatizadas ejecutadas por Jenkins o GitHub Actions. Los recorridos manuales quedan separados y no se mezclan en los porcentajes del pipeline.

## 1. Formatos de salida

Cada build debe conservar un resumen legible y uno procesable:

- `quality-summary.json`: fuente consolidada con identificador del build, commit, rama, fecha, ambiente y resultados de las suites.
- `quality-report.html`: resumen y tendencias para revisión del equipo.
- Ambos archivos se generan en `qa/metrics/reports/<runId>/` y se adjuntan al build como artefactos. En GitHub Actions se descargan desde el artefacto `dulce-miel-quality-<run>-<intento>`; en Jenkins aparecen en los artefactos del build.
- Informes originales JUnit, cobertura, análisis estático, K6 y TestLink: evidencia adjunta al mismo build, sin sobrescribir la de otras corridas.
- Exportación Excel/PDF: evidencia de entrega bajo demanda; no sustituye los reportes originales ni TestLink.

El reporte presenta datos en cinco vistas:

1. **Resumen por build:** estado general, pass rate, fail rate, cobertura por componente, métricas disponibles, datos N/A explicados y enlace al build/TestLink.
2. **Detalle por suite:** backend, frontend, Newman, Behave/Selenium, Playwright, axe-core y cada perfil K6.
3. **Cobertura:** componente, tipo de cobertura, elementos cubiertos, total y porcentaje.
4. **Análisis estático y defectos:** herramienta, regla/categoría, severidad, hallazgos nuevos y existentes; incidencias confirmadas en una tabla aparte.
5. **Rendimiento K6:** perfil, usuarios virtuales, duración, iteraciones, solicitudes, p95, p99, tasa de error, checks y umbrales.

## 2. Metadatos obligatorios por ejecución

- Proyecto y versión/build de Jenkins.
- Commit y rama probados.
- Fecha y hora, zona horaria y ambiente (QA aislado; nunca producción).
- Suite, herramienta y versión de la herramienta.
- IDs de casos de TestLink incluidos, cuando exista trazabilidad.
- Rutas a reportes originales y estado de publicación a TestLink.

Una métrica sin build, commit o ambiente identificable se muestra como **sin trazabilidad** y no entra en tendencias comparativas.

## 3. Fórmulas y reglas

### Pass rate y fail rate

- `ejecutadas = aprobadas + no_aprobadas`.
- `pass_rate (%) = aprobadas / ejecutadas × 100`.
- `fail_rate (%) = no_aprobadas / ejecutadas × 100`.
- `bloqueadas`, `omitidas` y `no ejecutadas` se informan por separado; no entran en el denominador.
- Si `ejecutadas = 0`, el porcentaje es **N/A**, nunca 0 % ni 100 %.

Se calcula por suite y para el conjunto automatizado del build. El conjunto solo incluye resultados producidos por ese build.

### Cobertura

- `cobertura (%) = elementos cubiertos / elementos instrumentados × 100`.
- Mostrar por separado líneas, ramas, funciones e instrucciones, siempre que la herramienta los produzca.
- Mostrar backend Java y frontend Angular en filas separadas. No promediar porcentajes de componentes con denominadores distintos.
- Los umbrales de aceptación se fijarán por componente después de obtener una línea base estable; hasta entonces se informa la medida sin convertirla en aprobación automática.
- Cobertura no equivale a corrección ni reemplaza pruebas de comportamiento.

### Análisis estático

- Conteo de hallazgos por herramienta, regla/categoría y severidad; separar nuevos de existentes mediante comparación con la línea base del branch.
- `densidad de hallazgos (por KLOC) = hallazgos / miles de líneas de código analizadas`, solo si se conserva el mismo alcance de archivos entre builds.
- Complejidad: registrar funciones que superan la regla acordada y su valor; no sumar métricas de herramientas distintas en un solo número.
- Los hallazgos de análisis estático no se cuentan automáticamente como defectos confirmados. Se mantienen como hallazgos hasta ser triados.

### Tasa de defectos y severidad

Una prueba fallida no es automáticamente un defecto del producto. Cada hallazgo debe clasificarse como `producto`, `prueba`, `entorno` o `datos`; solo los defectos confirmados del producto entran en la métrica.

- `tasa de defectos detectados = defectos únicos confirmados durante el ciclo / casos ejecutados × 100`.
- Reportar como **defectos únicos por cada 100 casos ejecutados**, junto con el conteo absoluto y el periodo/build. Un defecto repetido por varias pruebas se cuenta una sola vez.
- Distribución por severidad: conteo y porcentaje de defectos únicos `Crítica`, `Alta`, `Media` y `Baja` sobre el total de defectos confirmados.
- Si no hay defectos confirmados, la distribución es **N/A**; se muestra conteo cero aparte.
- La severidad debe tener criterios escritos y consistentes; no inferirla solo del estado aprobado/no aprobado en TestLink.

### Defect leakage

Por versión liberada:

`defect_leakage (%) = defectos confirmados encontrados después de liberar / (defectos confirmados antes de liberar + defectos confirmados después de liberar) × 100`.

Se atribuye cada defecto a la versión que lo introdujo. Si la versión no ha tenido periodo de observación o el denominador es cero, el resultado es **N/A**. No se puede medir con solo resultados Jenkins/TestLink; requiere registrar incidencias posliberación.

### Pruebas inestables (flaky)

Para una ventana controlada, repetir el mismo conjunto con commit, datos y ambiente constantes, idealmente tres ejecuciones.

- `flaky_rate (%) = casos con resultados distintos entre repeticiones / casos repetidos × 100`.
- Un caso que falla y pasa con reintento también se marca `flaky`, aunque el resultado final del retry sea aprobado.
- Informar `casos repetidos`, `casos flaky`, repeticiones por caso y si hubo retry. Los cambios de ambiente invalidan la comparación y se reportan como bloqueos de entorno.
- `stability_score` no será una métrica independiente en la primera versión: el pass rate y el flaky rate se muestran por separado para evitar esconder una falla tras un reintento.

### Métricas K6

Por perfil y por build, registrar al menos:

- Latencia p95 y p99 en milisegundos.
- Tasa de solicitudes fallidas: `solicitudes fallidas / solicitudes totales × 100`.
- Tasa de checks exitosos: `checks aprobados / checks ejecutados × 100`.
- Throughput: solicitudes por segundo reportadas por K6.
- Duración, VUs y nombre del perfil (humo, línea base, moderada, estrés, pico o sostenida).

El perfil pasa únicamente si se ejecutó, generó resumen válido y cumplió todos sus umbrales definidos para ese perfil. Una conexión rechazada al iniciar el entorno es **bloqueada/infraestructura**, no una aprobación ni un fallo de rendimiento. Los umbrales se revisan y versionan explícitamente; no se cambian para hacer pasar una ejecución.

### Automatización

- `automatización (%) = casos aplicables automatizados y enlazados a TestLink / total de casos aplicables del alcance × 100`.
- Publicar también el conteo de casos manuales, automatizados, bloqueados y sin clasificar.
- La publicación a TestLink refleja solo evidencia del build actual. Los casos manuales no se incluyen en el pass/fail de Jenkins.

## 4. Modelo mínimo de datos

Cada fila de detalle de suite debe conservar: `build_id`, `commit`, `fecha`, `ambiente`, `suite`, `herramienta`, `testlink_case_id` (opcional), `total`, `passed`, `failed`, `blocked`, `skipped`, `duration`, `report_path` y `classification` de fallos.

Las métricas de cobertura, análisis estático, defectos y K6 tienen tablas/datasets propios con sus denominadores y unidades; no se mezclan en una fila ambigua ni se promedian entre sí.

## 5. Reglas para interpretar los resultados de Dulce Miel

- Mantener visible `FAILURE` del build si alguna suite reporta una falla real; permitir que las siguientes suites se ejecuten para obtener cobertura diagnóstica completa.
- Separar defectos de producto de fallos de script, datos, infraestructura y publicación a TestLink.
- No convertir un caso no ejecutado en aprobado ni en no aprobado sin evidencia.
- Guardar reportes originales y resumen consolidado bajo el mismo número de build.
- Comparar tendencias solo entre ejecuciones con alcance, commit/versión y ambiente identificables.

## 6. Integración actual y límites de interpretación

`qa/metrics/generate_quality_report.py` crea el JSON y el HTML en cada ejecución. Jenkins lo invoca en `post { always }`; GitHub Actions lo genera antes de Quality Gate para que un fallo de métricas también quede visible y archiva después los reportes. Ambos flujos mantienen visibles los fallos y ejecutan las etapas posteriores según su configuración.

El resumen lee JUnit/Surefire y Behave, log de Karma, datos Newman, Playwright, axe-core, los seis resúmenes K6, cobertura HTML de Angular, XML JaCoCo y el resumen actual de TestLink. El paso backend ejecuta `mvn test` y luego solicita `jacoco:report` incluso si las pruebas fallan; el código de salida original de Maven se conserva para que el build no oculte un fallo.

El pass/fail trazable de TestLink se calcula por ID único, una vez por corrida. La cobertura de ejecución del catálogo indica cuántos IDs tuvieron estado automatizado en ese build; no es cobertura de código ni tasa de automatización. K6 se informa por perfil y solo aprueba si existe resumen y pasan todos los umbrales. Si una etapa falla sin resumen, aparece bloqueada/incompleta, no aprobada.

La línea base local del 12-11-2026 mide cobertura de JaCoCo y Angular, cuenta hallazgos SpotBugs por prioridad (sin tratarlos como defectos confirmados), calcula defectos únicos del registro de triage enlazados a fallos, mide tres repeticiones estables de ocho casos Playwright y clasifica los casos del catálogo por automatización enlazada o ejecución exclusivamente manual. Defect leakage queda como **No medible**, no como cero, porque aún no existe una fuente de incidencias posliberación asociada a versión y periodo. Para medirlo, registrar por cada versión fecha de liberación, periodo observado, defectos confirmados preliberación y postliberación y vínculo al ID del defecto.

Los recorridos manuales de teclado y Narrador no entran al resultado de los pipelines; se conservan en TestLink como evidencia manual. La tasa de automatización se calcula como casos automatizados y enlazados / casos aplicables (casos manuales puros excluidos; brechas incluidas). La cobertura de ejecución del build es un indicador distinto: IDs del catálogo con resultado actual / total del catálogo.

La línea base local no sustituye una corrida de Jenkins o GitHub Actions: el reporte la etiqueta como local y no publica resultados a TestLink. Revisar los artefactos del primer build de cada plataforma antes de comparar tendencias; no reutilizar cifras históricas de otros commits.
