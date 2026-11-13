# Informe de métricas del build 15

**Proyecto:** Dulce Miel  
**Plataforma:** GitHub Actions  
**Ejecución:** [Build 15, ID 43408870524](https://github.com/HeyKanX/dulcemiel-web/actions/runs/43408870524)  
**Commit probado:** `c658f57e687c7549992883801b0a3f607ed46a9f` (merge commit de la solicitud)  
**Ambiente:** QA aislado en Docker; no producción.  
**Corte:** 13 de noviembre de 2026.

## Resultado general

La corrida ejecutó 36 de los 49 IDs del catálogo automatizado enlazado a TestLink. De esos 36 IDs únicos, 35 aprobaron y uno no aprobó: `TC-NF-INT-002`, que verifica que el catálogo conserve el producto “Miel QA” después de recargar con una sesión activa. El pass rate es `35 / 36 × 100 = 97,22%`: significa que 35 casos automatizados con resultado vigente cumplieron el esperado en esta corrida. El fail rate es `1 / 36 × 100 = 2,78%`: significa que un caso no cumplió el criterio; no equivale a una tasa de defectos confirmados. Los 13 IDs restantes no tuvieron resultado automatizado en este build y quedan fuera de ambos denominadores.

El Quality Gate terminó en **FAILURE** porque Behave/Selenium reportó el caso fallido. Esto confirma que la automatización detecta y conserva el error; no significa que Jenkins o GitHub Actions haya dejado de funcionar. Se ejecutaron las etapas posteriores, se generaron métricas y se guardaron artefactos. La publicación de resultados en TestLink fue omitida porque el evento fue un pull request y no una ejecución manual con publicación autorizada.

## Conteos por suite y significado de cada unidad

| Suite | Resultado | Qué cuenta el número | Interpretación |
|---|---:|---|---|
| Backend Maven/Surefire | 26/26 aprobadas | Métodos de prueba JUnit en 6 reportes XML | Incluye 7 pruebas de integración SQL Server con Testcontainers y 1 prueba TDD de carrito. 26 es el total de métodos de esta corrida; no es el total de casos del catálogo ni el número 62 de ejecuciones anteriores. |
| Frontend Angular/Karma | 8/8 aprobadas | Pruebas unitarias reportadas por Karma | Las 8 comprobaciones pasan; su cobertura de código se interpreta aparte en la sección de cobertura. |
| API Newman | 33/33 aserciones aprobadas | Aserciones verificadas en 32 solicitudes HTTP | 33 es el denominador de aserciones; 32 cuenta solicitudes. No se suman entre sí ni se igualan a 33 casos TestLink. |
| Interfaz Behave/Selenium | 9/10 aprobadas | Escenarios Gherkin con estado JUnit | El caso restante es `TC-NF-INT-002`; produce el fallo que hace fallar el Quality Gate. |
| Playwright seleccionado | 8/8 aprobadas | Casos automatizados seleccionados del registro | Resultado automático de esta corrida, no reemplaza las ejecuciones manuales previas. |
| Compatibilidad Playwright | 1/1 aprobado | Un método compuesto de auditoría | El método ejecuta sus combinaciones de navegador y viewport; 1 es el caso contenedor, no una sola combinación de dispositivo. |
| axe-core | 9 rutas procesadas, 0 violaciones detectadas | Rutas entregadas al escáner; 9 respuestas registradas | En las rutas escaneadas no se encontraron violaciones de las reglas WCAG configuradas. Hubo 2 verificaciones incompletas; axe no sustituye una comprobación manual con teclado o Narrador. El escaneo de `/dashboard` encontró contenido, aunque no registró código HTTP. |

Los conteos de estas suites no se suman para producir un total porque cada herramienta cuenta unidades diferentes: métodos JUnit, aserciones HTTP, escenarios, casos de catálogo o rutas accesibles. El total comparable de aceptación del catálogo sigue siendo 36 IDs únicos, según `current-run.json`.

## Diagnóstico verificable de `TC-NF-INT-002`

Después de recargar la ruta `/productos`, Selenium observó el mensaje “No se pudieron cargar los productos” y no encontró la tarjeta de “Miel QA”. La sonda directa ejecutada desde el runner recibió HTTP 200 y encontró el nombre “Miel QA” en la respuesta de `/api/productos`; el navegador no reportó errores JavaScript y los eventos de solicitud API capturados durante la recarga quedaron vacíos. Por ello el caso **no aprueba**: el usuario automatizado no ve el producto esperado. La evidencia actual localiza la diferencia entre la respuesta de API disponible al runner y el resultado presentado por la interfaz, pero no determina por sí sola la causa raíz. Se clasifica como fallo reproducible de interfaz/integración con causa raíz pendiente, sin cambiar la aplicación ni relajar el criterio.

Evidencia: `qa/artifacts/build-15-087d8cf9/ui-behave/TESTS-carrito_pedidos.xml`, el archivo `build-15-087d8cf9_failed_TC-NF-INT-002...txt` y su captura PNG, incluidos en los artefactos de la ejecución.

## Cobertura de código

JaCoCo informa para Java backend: líneas `235/469 = 50,11%`, ramas `104/362 = 28,73%`, instrucciones `1613/4328 = 37,27%` y métodos `58/108 = 53,70%`. Por ejemplo, 50,11% de líneas significa que la instrumentación registró ejecución en 235 de las 469 líneas contabilizadas; las otras 234 no se ejercitaron en esa corrida. No demuestra corrección de las líneas recorridas.

Karma/Istanbul informa para Angular frontend: líneas `69/94 = 73,40%`, ramas `14/25 = 56,00%`, funciones `24/41 = 58,54%` e instrucciones `72/97 = 74,23%`. El 56,00% de ramas, por ejemplo, corresponde a 14 de 25 alternativas instrumentadas. Backend y frontend tienen bases distintas y no se promedian. Estos porcentajes aportan evidencia a OE3 y OE7; no son cobertura de criterios ni de casos de prueba.

## Pruebas de carga K6

Los seis perfiles cumplieron sus cinco umbrales definidos; “5/5” significa que cada umbral configurado en ese perfil se cumplió, no que el sistema sea ilimitado. `VUs` es el máximo de usuarios virtuales simultáneos del escenario, `p95` es la latencia de API bajo la cual quedó el 95% de las solicitudes medidas y `% error` es solicitudes fallidas dividido por solicitudes totales.

| Perfil | VUs máx. | Duración | Solicitudes | API p95 | Error | Lectura |
|---|---:|---:|---:|---:|---:|---|
| Humo | 1 | 30,18 s | 60 | 4,54 ms | 0% | Comprobación breve de conectividad y umbrales básicos. |
| Línea base | 3 | 120,69 s | 720 | 4,81 ms | 0% | Referencia de baja carga para comparar perfiles del mismo ambiente. |
| Carga moderada | 8 | 180,96 s | 2.880 | 4,90 ms | 0% | Comportamiento con ocho VUs durante tres minutos. |
| Estrés progresivo | 600 | 240,80 s | 120.220 | 1,61 ms | 0% | Máximo VUs configurado alcanzado; no se registraron solicitudes fallidas. |
| Pico repentino | 1.000 | 50,56 s | 80.726 | 2,08 ms | 0% | Escenario breve con incremento de tráfico; resultado limitado a esa ventana y entorno. |
| Carga sostenida | 100 | 600,75 s | 119.600 | 3,26 ms | 0% | Diez minutos aproximados con 100 VUs, sin errores de solicitud. |

Los 324.206 envíos suman el tráfico medido de los seis perfiles para describir volumen ejecutado; no son una carga simultánea ni se usan como denominador de un porcentaje agregado. Estos valores provienen de un backend/frontend efímero en Docker, por lo que no predicen por sí solos la latencia o capacidad de producción. Los resultados contribuyen a OE5 y OE7.

## Análisis estático, defectos y estabilidad

- **SpotBugs:** 9 hallazgos P2: 8 de regla `EI_EXPOSE_REP2` y 1 de `CT_CONSTRUCTOR_THROW`. P2 es prioridad técnica asignada por SpotBugs, no severidad confirmada del producto. Estos 9 deben triasearse por regla; no se cuentan como 9 defectos. Build 15 todavía no ejecutó el analizador TypeScript añadido después de esta corrida.
- **Tasa de defectos confirmados ligados a esta corrida:** `0/36 = 0,00 por cada 100 casos` significa que ningún defecto confirmado del registro se pudo vincular como defecto raíz a los casos fallidos de esta corrida. Hay 1 fallo pendiente de causa raíz, por lo que cero no significa que no hubiera un resultado fallido. El registro acumulado conserva 6 defectos abiertos de accesibilidad.
- **Defect leakage:** N/A, porque falta registrar una liberación y un periodo con incidencias posliberación asociadas. N/A no significa 0%.
- **Flaky rate del commit actual:** N/A, porque el fingerprint de esta corrida no coincide con la muestra histórica. La muestra controlada separada contiene 3 repeticiones del commit `39bbd975c3bd9781d01a8754402373d0e90ee981`, con 8 casos por corrida y 0 reintentos; `0/8 = 0%` significa que esos ocho casos conservaron su estado en esas tres repeticiones. No se extrapola al commit del build 15.

## Tasas del catálogo y relación con objetivos

- **Tasa de automatización OE6/OE7:** `36/47 = 76,60%`. El numerador son los 36 casos automatizados y enlazados; el denominador son 47 casos aplicables. Los 2 casos exclusivamente manuales se excluyen; las 11 brechas automatizables sí permanecen en el denominador. La proporción supera el umbral de OE6 (75%) para esta clasificación del catálogo, pero no implica que esos 47 se ejecutaran en este build.
- **Cobertura de ejecución OE4/OE6:** `36/49 = 73,47%`. Cuenta IDs con resultado actual frente a todos los IDs del catálogo; quedan 13 sin resultado en build 15. No es cobertura de código ni automatización.
- **OE1:** hay 49 casos con IDs y trazabilidad de origen en el registro, pero la cobertura de HU/criterios no puede expresarse como porcentaje sin un inventario canónico total de HU/CA asociado.
- **OE2:** el catálogo contiene 49 IDs únicos. El número solo mide el tamaño del catálogo; la suficiencia y validez semántica del diseño se evalúan contra criterios positivos, negativos y límite.
- **OE3:** 26 pruebas Maven (7 integraciones SQL y 1 TDD) y 8 pruebas unitarias de frontend aprobaron; las coberturas anteriores muestran el código ejecutado, no el porcentaje de cumplimiento del objetivo.
- **OE4:** 35/36 IDs automatizados aprobaron y 1/36 no aprobó. El Quality Gate conserva ese fallo visible.
- **OE5:** los perfiles K6 aprobaron en el ambiente aislado. axe procesó nueve rutas sin violaciones detectadas, con dos comprobaciones incompletas; Narrador/teclado manual no forma parte del escaneo automático.
- **OE6:** la clasificación de automatización es 76,60%; build 15 verifica GitHub Actions. Jenkins queda como evidencia separada y no se infiere su validación a partir de esta corrida.
- **OE7:** se calcularon cobertura, pass/fail, tasa de defectos confirmados, análisis SpotBugs, K6, automatización y estabilidad histórica. Leakage permanece N/A; no se asigna porcentaje global de OE7 porque la rúbrica no especifica ponderaciones.

## Relevancia de esta corrida para el cierre de Fase 3

Build 15 deja evidencia de que el CI ejecuta todas las suites automatizadas, incluido K6 de estrés, pico y sostenida, genera artefactos y falla el Quality Gate frente a un caso que no cumple. Es la referencia integral del candidato con las correcciones anteriores. Según la instrucción del equipo, el frontend se restituyó luego al estado previo a aquellas correcciones antes de la siguiente validación; por tanto, este build 15 queda como evidencia histórica del candidato, no como resultado del código restituido.

La siguiente corrida debe incorporar el analizador TypeScript, validar el baseline y producir el HTML/JSON explicativo con el mismo build/commit. La tabla de metas de cobertura se basará en esa corrida posterior comparable; no se derivan umbrales del build 15 para un código diferente.
