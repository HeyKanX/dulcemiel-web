# Trazabilidad de requisitos y pruebas

## Términos y relación

| Elemento | Qué representa | Identificador usado |
|---|---|---|
| Requerimiento | Necesidad verificable del sistema. RF expresa funciones; RNF expresa cualidades o restricciones. | `RFxx`, `RNFxx` |
| Historia de usuario | Necesidad expresada desde el rol de una persona usuaria. | `HUxx` |
| Criterio de aceptación | Condición observable para aceptar una historia o requisito. No es un caso de prueba ni una ejecución. | `CAxx` |
| Caso de prueba | Diseño reproducible con precondiciones, datos, pasos y resultado esperado. Un caso puede comprobar un criterio, y un criterio puede necesitar varios casos. | `TC-*` |
| Tipo de prueba | Propósito que comprueba el caso: funcional, accesibilidad, compatibilidad, rendimiento, seguridad o integridad. | Campo `tipo_prueba` |
| Nivel de prueba | Ámbito de evaluación, por ejemplo unitario, integración, sistema o aceptación. No es sinónimo del tipo. | Campo `nivel_prueba` |
| Técnica de prueba | Forma de seleccionar o evaluar datos y comportamientos, como particiones, valores límite o transiciones. | Campo `tecnica` |
| Escenario automatizado | Implementación ejecutable de un caso en Gherkin/Behave, Selenium, Newman, Playwright, k6 u otra herramienta. | Etiqueta `TC-*` y referencias `HUxx`/`CAxx` |
| Ejecución | Una corrida concreta de un caso en una versión y ambiente, con resultado obtenido y evidencia. El mismo caso puede ejecutarse muchas veces. | `id_corrida` + `id_caso` |
| Fallo y defecto | Un resultado fallido es una diferencia entre lo esperado y lo observado. Se registra como defecto cuando se confirma y se le asigna un identificador. | `D-C5-xx` |

La ruta de trazabilidad es `HU → RF/RNF y CA → TC → ejecución → evidencia → defecto o métrica`. Los identificadores `TC-*` distinguen casos de aceptación `CA-*`; no se deben reutilizar como si fueran lo mismo.

## Conteo actual del catálogo

`test-design/cases.csv` contiene 41 casos únicos:

- 20 casos funcionales de nivel aceptación. Los criterios funcionales CA01–CA19 se vinculan con casos, y CA10 se divide en dos: límite inválido de cantidad cero y modificación/eliminación con cantidad válida.
- 15 casos de accesibilidad asociados a CA20–CA34.
- 6 casos no funcionales adicionales: dos de rendimiento, uno de compatibilidad, uno de seguridad y dos de integridad.

Así, los 34 criterios CA tienen al menos un caso diseñado (34/34). Los cuatro registros `CNF-ACC-*` que antes repetían CA20, CA21, CA32 y CA33 se convirtieron en tareas manuales ligadas a esos casos existentes; ya no aumentan el conteo. Los casos diseñados no equivalen a escenarios automatizados o ejecutados. `test-runs/executions.csv` conserva resultados de la auditoría registrada; el estado parcial no significa que el criterio esté aprobado en su totalidad.

## Lectura de la rúbrica

**Criterio 2, análisis y objetivos.** Debe verse alineación entre problema, objetivos, historias, criterios de aceptación y diseño de casos. La matriz conserva los identificadores de esa cadena.

**Criterio 4, pruebas unitarias, integración y TDD.** Solicita pruebas unitarias y de integración, evidencia de TDD cuando corresponda, casos límite, evaluación de cobertura y resultados reproducibles. JaCoCo genera cobertura para el backend Java; Karma Coverage informa la del frontend Angular. Quitarlos debilitaría la evidencia explícita de cobertura de código. Mantenerlos no garantiza por sí solo el nivel destacado: hay que interpretar las líneas y ramas cubiertas y explicar áreas sin cobertura.

**Criterio 5, pruebas funcionales, aceptación y no funcionales.** Solicita un registro sistemático de precondiciones, pasos, datos, resultado esperado y obtenido y evidencia; pide ejecutar pruebas funcionales y de aceptación, además de no funcionales pertinentes; y requiere automatización e interpretación de métricas. Por eso diseño (`cases.csv`) y resultados (`executions.csv`) tienen archivos distintos.

La guía de Semana 9 de la práctica Aula Nova pide al menos 20 casos funcionales antes de las pruebas no funcionales y propone 10 de rendimiento, 10 de estrés y 10 de seguridad con k6. Ese conteo pertenece a esa práctica y a su aplicación de ejemplo; la rúbrica del proyecto Dulce Miel no fija esos números. Sirve como referencia de organización y categorías, pero cada escenario y umbral se debe adaptar al sistema y a sus requisitos. En la auditoría actual hay dos casos de rendimiento k6; no se debe afirmar que se ejecutaron 10 escenarios de estrés y 10 de seguridad.

Los 20 casos funcionales listados arriba satisfacen el mínimo usado en la práctica mediante la descomposición justificada de CA10. La suite Behave actual cubre un subconjunto de casos como navegador, Newman agrega verificaciones de API y la matriz conserva casos manuales y no ejecutados. Los conteos de casos, solicitudes API, aserciones, escenarios ejecutados y criterios cubiertos son medidas distintas y se informan por separado.

## Herramientas y alcance

JaCoCo se conserva porque aporta la métrica de cobertura del backend solicitada por el criterio 4. Karma Coverage cumple ese propósito en Angular. Las herramientas del proyecto incluyen axe DevTools Extension.

Las ejecuciones y evidencias históricas se conservan en `test-runs/executions.csv` para mantener la trazabilidad; se distinguen de los casos diseñados y de las corridas futuras.

## Registro de ejecución

Añadir una fila por cada caso ejecutado y por cada corrida. Conservar como mínimo: `id_corrida`, fecha, `id_caso`, commit probado, ambiente, resultado, resultado observado, evidencia, defecto/severidad y herramienta ejecutada. Usar estos estados para nuevas corridas:

- `aprobado`: todos los pasos y resultados esperados del caso se verificaron.
- `fallido`: el comportamiento observado contradice el esperado.
- `bloqueado`: no fue posible completar la prueba por ambiente, datos o dependencia.
- `no ejecutado`: el caso está diseñado, pero no tiene una corrida.
- `parcial`: se verificó solo una parte del caso o una de varias capas; no se cuenta como aprobación completa.

No sobrescribir registros de corridas anteriores. Si se corrige un defecto, conservar la ejecución fallida y crear otra fila con el nuevo resultado, commit y evidencia.
