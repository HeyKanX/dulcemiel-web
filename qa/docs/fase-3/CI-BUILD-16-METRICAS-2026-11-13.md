# Informe de métricas del build 16

**Proyecto:** Dulce Miel  
**Plataforma:** GitHub Actions  
**Ejecución:** [Build 16, ID 43414310448](https://github.com/HeyKanX/dulcemiel-web/actions/runs/43414310448)  
**Commit de la cabeza de PR:** `846582cd991d51d0aa08f79f7085d4b36546ed34`  
**Commit de integración probado por GitHub:** `2569f4358502fc0725a318b002f50798a823d0c0`  
**Ambiente:** QA efímero en Docker; no producción.  
**Corte:** 13 de noviembre de 2026.

## Resultado general y lectura de los porcentajes

El catálogo contiene 49 identificadores de caso. Este build produjo estados automáticos vigentes para 36 IDs únicos: 31 aprobaron y 5 no aprobaron. Por eso el pass rate es `31 / (31 + 5) × 100 = 86,11%` y el fail rate es `5 / (31 + 5) × 100 = 13,89%`. Cada numerador cuenta IDs únicos de TestLink, no métodos JUnit ni aserciones HTTP. Los 13 IDs sin resultado actual quedan fuera de ambos porcentajes; la cobertura de ejecución del catálogo es `36 / 49 × 100 = 73,47%`. La cobertura de ejecución no indica cuántos casos están automatizados ni cuánto código ejecutaron las pruebas.

El Quality Gate quedó en **FAILURE** porque Behave, axe-core y Playwright reportaron fallos. Sus etapas terminaron, se generó el resumen y se guardaron los artefactos; por lo tanto, el gate detectó los resultados sin detener las etapas posteriores. No se modificó el código de la aplicación durante esta continuación. El build validó el mapeo de TestLink, pero no publicó estados porque se originó en un pull request y la opción de publicación real estaba desactivada.

## Resultados por suite y qué cuenta cada número

| Suite | Resultado | Unidad y significado |
|---|---:|---|
| Backend Maven/Surefire | 26/26 aprobadas | 26 métodos de prueba JUnit distribuidos en 6 reportes XML: 7 métodos de integración SQL Server, 1 prueba identificada como TDD, 8 de carrito, 5 de pedidos, 4 de JWT y 1 de inicio de aplicación. El 100% solo describe las aserciones ejecutadas en esos métodos; no equivale al 100% de cobertura de código. |
| Frontend Angular/Karma | 8/8 aprobadas | 8 especificaciones Karma/Jasmine. Statements: 72/97; líneas: 69/94; ramas: 14/25; funciones: 24/41. Las cuatro fracciones describen unidades instrumentadas distintas. |
| API Newman | 33/33 aprobadas | 33 aserciones en 32 solicitudes HTTP. El pass rate de Newman usa aserciones como denominador; solicitudes y aserciones no se suman ni representan el mismo número de casos. |
| Interfaz Behave/Selenium | 9/10 aprobadas | 10 escenarios Gherkin con reporte JUnit. El caso que falla es `TC-NF-INT-002`; los otros nueve cumplieron sus pasos esperados. |
| Casos seleccionados Playwright | 5/8 aprobados | 8 casos automatizados; fallaron `TC-NF-ACC-004`, `TC-NF-ACC-008` y `TC-NF-ACC-009`. El pass rate de esa suite es 62,50%. |
| Compatibilidad Playwright | 1/1 aprobada | 1 prueba compuesta de compatibilidad. El valor 1 cuenta el método de auditoría; sus combinaciones internas no se deben presentar como una sola combinación de navegador/dispositivo. |
| Accesibilidad axe-core | 1/9 rutas sin violación; 8/9 con violaciones | 9 rutas/páginas recibieron resultado. Una ruta sin violaciones reportadas y ocho rutas con al menos una violación. Se detectaron verificaciones incompletas en `/` y `/productos`; esas comprobaciones necesitan revisión humana y no cuentan como violaciones confirmadas. |
| K6 | 6/6 perfiles aprobados | Cada perfil aprobó sus 5 umbrales configurados; en conjunto son 30 de 30 evaluaciones de umbral cumplidas. Un perfil aprobado significa que produjo un resumen válido y cumplió los umbrales de ese escenario, no que el sistema tenga capacidad ilimitada. |

Los conteos de suites no se suman: JUnit cuenta métodos de prueba, Karma especificaciones, Newman aserciones, Behave escenarios, axe rutas y K6 perfiles. El total comparable con el catálogo es 36 IDs únicos con resultado. Una fila de suite da su pass rate como aprobados dividido entre aprobados más fallidos; omitidos y bloqueados se informan aparte y quedan fuera del denominador.

## Casos no aprobados y clasificación

| Caso | Resultado observado | Clasificación al cierre |
|---|---|---|
| `TC-NF-ACC-004` | 2 controles o imágenes sin nombre accesible. | Fallo de accesibilidad asociado a `DEF-ACC-001` (severidad Media). |
| `TC-NF-ACC-008` | Después de cambiar la cantidad, el DOM tiene 0 regiones de anuncio (`aria-live`, `role=status` o `role=alert`). | Fallo de accesibilidad asociado a `DEF-ACC-002` (severidad Media). |
| `TC-NF-ACC-009` | 7/7 controles del checkout sin etiqueta programática; el envío del formulario vacío sí mostró validación. | Fallo de accesibilidad asociado a `DEF-ACC-003` (severidad Alta). La validación visual no sustituye el nombre accesible. |
| `TC-NF-ACC-014` | axe detectó contraste insuficiente en `/productos/1` y `/carrito/checkout`. | Fallo de accesibilidad asociado a `DEF-ACC-006` (severidad Media). |
| `TC-NF-INT-002` | Tras recargar `/productos`, Selenium no vio “Miel QA” y sí vio el mensaje de error. Una sonda del runner obtuvo HTTP 200 y encontró el nombre; no se capturaron eventos API del navegador ni errores JavaScript. | Fallo reproducible de interfaz/integración, `DEF-INT-006`, causa raíz pendiente de confirmar. No se atribuye al backend sin evidencia suficiente. |

En axe-core las violaciones quedaron por ruta: `select-name` (impacto del analizador critical) en `/` y `/productos`; `label` (critical) en registro, inicio de sesión y checkout; `color-contrast` (serious) en detalle de producto y checkout; `link-name` (serious) en detalle, carrito, checkout y seguimiento. Estas etiquetas de impacto son las que reporta axe; no son la severidad del registro de defectos. Los 8 resultados de página con violaciones no son 8 casos TestLink ni 8 defectos raíz.

La tasa de defectos confirmados vinculados a casos fallidos es `4 / 36 × 100 = 11,11 defectos confirmados por cada 100 IDs ejecutados`. El numerador es cuatro registros únicos de accesibilidad asociados a cuatro casos fallidos; el denominador es 36 IDs con resultado. El quinto caso fallido, `TC-NF-INT-002`, se mantiene como candidato reproducible con causa raíz sin confirmar y por eso no se suma a los cuatro defectos confirmados. La distribución del numerador confirmado es 3 de severidad Media y 1 Alta. El registro completo tiene 9 IDs únicos (8 confirmados abiertos y 1 caso reproducible pendiente de causa); no se cuentan hallazgos repetidos de una misma causa como defectos adicionales.

## Cobertura de código y meta de mejora

| Componente y herramienta | Unidad | Resultado | Interpretación |
|---|---|---:|---|
| Backend Java — JaCoCo | Líneas | 235/469 = 50,11% | La instrumentación observó ejecución en 235 de 469 líneas; 234 no quedaron cubiertas en esta corrida. |
| Backend Java — JaCoCo | Ramas | 104/362 = 28,73% | 104 de 362 alternativas de decisión fueron ejecutadas. Esta cifra señala rutas lógicas no recorridas; no mide si las cubiertas son correctas. |
| Backend Java — JaCoCo | Instrucciones | 1.613/4.328 = 37,27% | 1.613 instrucciones de bytecode reportadas fueron cubiertas. El total y el numerador no son líneas fuente. |
| Backend Java — JaCoCo | Métodos | 58/108 = 53,70% | 58 de 108 métodos instrumentados se ejecutaron. |
| Frontend Angular — Karma/Istanbul | Líneas | 69/94 = 73,40% | 69 de 94 líneas instrumentadas del frontend se ejecutaron. |
| Frontend Angular — Karma/Istanbul | Ramas | 14/25 = 56,00% | 14 de 25 alternativas instrumentadas del frontend se ejecutaron. |
| Frontend Angular — Karma/Istanbul | Statements | 72/97 = 74,23% | 72 de 97 sentencias instrumentadas se ejecutaron. |
| Frontend Angular — Karma/Istanbul | Funciones | 24/41 = 58,54% | 24 de 41 funciones instrumentadas se ejecutaron. |

Los denominadores de Java y Angular provienen de instrumentaciones distintas, así que sus porcentajes no se promedian. Una instrucción, línea, rama o función cubierta demuestra que se ejecutó, no que su resultado sea correcto. La línea base de CI queda fijada con el run `43414310448` y el commit probado `2569f4358502fc0725a318b002f50798a823d0c0`. Para el siguiente incremento de revisión, +5 puntos porcentuales equivalen a backend Java: líneas 55,11% y ramas 33,73%; frontend Angular: líneas 78,40% y ramas 61,00%. Son metas de revisión por componente; el gate actual no rechaza por esos umbrales.

## Análisis estático y líneas base

SpotBugs reportó 9 observaciones: 8 de la regla `EI_EXPOSE_REP2` y 1 de `CT_CONSTRUCTOR_THROW`, todas con prioridad P2 y clasificadas como existentes frente al baseline del build 15. Por tanto, este build tiene 0 observaciones nuevas de SpotBugs. P2 es una prioridad que asigna el analizador; no significa severidad Media del producto ni confirma 9 defectos. El baseline identifica cada observación por regla y clase primaria, ignorando el número de línea para no duplicarla si el código se desplaza.

El compilador TypeScript 5.2.2 terminó con código 0 y registró 0 diagnósticos, 0 nuevos frente a su baseline vacío. `TS####` sería el identificador de regla/diagnóstico y “error” la severidad técnica del compilador; aquí no hubo códigos TS que clasificar. SpotBugs aporta prioridad y regla para Java; TypeScript aporta código y nivel del compilador para el frontend. Ambos hallazgos deben triagearse antes de sumarlos al registro de defectos.

## Métricas restantes

- **Defect leakage:** N/A. La fórmula es defectos confirmados posliberación ÷ (defectos confirmados preliberación + posliberación) × 100. Falta una versión liberada y un periodo de observación con incidencias vinculadas; N/A significa que no hay denominador válido, no que haya cero defectos.
- **Flaky rate del commit probado:** N/A porque su fingerprint no coincide con la muestra controlada disponible. La muestra histórica sí tiene 3 ejecuciones del mismo commit `39bbd975c3bd9781d01a8754402373d0e90ee981`, mismo runner Chromium/Playwright y semilla SQL QA; 8 IDs repetidos, 0 cambiaron de estado, sin retries. `0/8 = 0%` describe solo esos ocho casos en esa versión y ambiente. No se extrapola al commit de build 16.
- **Tasa de automatización del catálogo:** `36 / (36 + 11) × 100 = 76,60%`. Los 36 casos automatizados/enlazados forman el numerador; los 47 casos aplicables son 36 automatizados más 11 brechas. Se excluyen 2 casos exclusivamente manuales. Supera el umbral de OE6 de 75%, pero no quiere decir que los 47 se ejecutaron en este build.
- **Cobertura de ejecución del catálogo:** `36 / 49 × 100 = 73,47%`. Cuenta IDs con resultado actual sobre todos los IDs del catálogo. No es la tasa de automatización ni la cobertura de código.

## Relación con los objetivos específicos OE1–OE7

| Objetivo y meta | Evidencia de build 16 | Interpretación y límite |
|---|---|---|
| OE1 — Historias de Usuario y Criterios de Aceptación (100%) | 49 IDs del catálogo enlazados al mapa de casos y 36 con ejecución actual. | La relación requisito/caso se conserva; no se calcula cobertura porcentual de HU/CA porque falta un inventario canónico versionado de todas las historias y criterios como denominador. |
| OE2 — Diseño de Casos de Prueba (100%) | Catálogo de 49 IDs; los casos usados por automatización incluyen identificador, origen y evidencias en los artefactos. | 49 mide tamaño del catálogo, no validez semántica. La revisión de pasos, datos, precondiciones y clases positivas/negativas/límite debe contrastarse con cada criterio; no se infiere 100% de la cantidad. |
| OE3 — Pruebas Unitarias, de Integración y TDD (100%) | 26/26 métodos Maven pasan; entre ellos 7 pruebas con SQL Server y una `CarritoCa11TddTest`. Karma: 8/8. JaCoCo/Karma aportan los denominadores de cobertura arriba. | Los resultados prueban ejecución de esos métodos, no cumplimiento porcentual completo del objetivo. Las ramas Java con 104/362 (28,73%) son la brecha de cobertura más visible para priorizar. |
| OE4 — Pruebas Funcionales y de Aceptación (100%) | 31/36 IDs automatizados aprobados, 5/36 no aprobados; 13/49 sin resultado actual. El mapa TestLink valida los IDs; publicación real se omitió en evento PR. | El fail rate visible se mantiene en 13,89%; esos cinco casos no se convierten automáticamente en cinco defectos confirmados. La cobertura del build es 73,47% del catálogo. |
| OE5 — Pruebas No Funcionales (100%) | 6/6 perfiles K6 cumplen 5/5 umbrales cada uno; Newman ejecuta 32 solicitudes y 33 aserciones; axe procesa 9 rutas; compatibilidad 1/1 prueba compuesta. | El rendimiento medido pasó sus umbrales; la accesibilidad tiene fallos concretos en 8 rutas y dos comprobaciones incompletas. Los resultados se limitan a escenarios/rutas ejecutados en QA. |
| OE6 — Herramientas de Automatización y CI/CD (≥75%) | Automatización `36/47 = 76,60%`; build GitHub Actions ejecuta Maven, Karma, SpotBugs, TypeScript, Docker Compose, Newman, Behave, Playwright, axe y seis perfiles K6; conserva evidencia. | La tasa del catálogo supera 75%. El denominador es 47 casos automatizables; 2 manuales no cuentan. Esta corrida verifica GitHub Actions, no agrega una nueva ejecución de Jenkins. |
| OE7 — Métricas de Calidad de Software (≥50%) | Se presentan métricas estáticas, cobertura Java/Angular, pass/fail, registro/severidad/tasa de defectos, K6, automatización y estabilidad histórica. Leakage y flaky rate del commit actual tienen fórmula y estado N/A justificado. | Hay resultado verificable para las familias pedidas y límites explícitos; no se asigna porcentaje global de OE7 porque la rúbrica no define pesos ni una fórmula para convertirlas en cumplimiento. Se informa 8/8 familias cubiertas por el esquema, no un supuesto 100% del objetivo. |

Los objetivos y sus resultados deben leerse con esta diferencia: un número de evidencia no es un porcentaje de cumplimiento del objetivo. OE6 sí tiene una fórmula de tasa de automatización y su resultado supera la meta de 75%. Para OE1–OE5 la evidencia está relacionada con los objetivos, pero la rúbrica no ofrece ponderación para calcular un porcentaje. OE7 expone todas las familias solicitadas y marca explícitamente las métricas sin base empírica suficiente como N/A.

## Conclusión de la medición

El build 16 cierra la medición de la fase con cifras reproducibles y fallos visibles. El análisis estático diferencia los hallazgos existentes de los nuevos; el registro relaciona los fallos confirmados con casos y severidad; la cobertura deja una base por componente; la tasa de automatización se compara con OE6; y el HTML y JSON se generan del mismo run. Los defectos de accesibilidad permanecen no aprobados y el caso de recarga permanece reproducible con causa sin confirmar. El gate rojo es el resultado esperado ante esas pruebas fallidas; no bloquea el cierre de la fase de métricas ni equivale a corregir la aplicación. Leakage no se calcula sin una liberación observada y el flaky rate de la muestra histórica no se atribuye a esta versión.
