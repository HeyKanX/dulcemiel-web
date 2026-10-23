# Flujo de automatización de pruebas

Este flujo adapta al proyecto Dulce Miel los patrones de las prácticas disponibles de las semanas 1, 2, 4, 5, 8 y 9, los ejemplos de clase y los entregables T1/Campus360. Separa el diseño del caso, su implementación automatizada y el resultado de cada corrida.

## Secuencia de trabajo

1. **Partir de una necesidad verificable.** Identificar la historia o requisito (`HU`, `RF` o `RNF`) y el criterio de aceptación (`CA`) que se comprobará. Los criterios describen condiciones esperadas; no son casos ni resultados de ejecución.
2. **Diseñar el caso antes de automatizarlo.** Registrar en `test-design/cases.csv` el identificador `TC`, tipo y nivel de prueba, precondiciones, datos, pasos y resultado esperado. Incluir flujos válidos, negativos y límites cuando el criterio lo requiera. Revisar que los datos y pasos se puedan reproducir.
3. **Preparar el entorno y los datos.** Iniciar backend, frontend y servicios requeridos. Usar datos sintéticos; cualquier escenario que modifique datos debe llevar `@writes` y validar que la conexión apunta a la base aislada de QA. El API puede preparar una cuenta sintética cuando el objetivo del caso es verificar el comportamiento de la interfaz después de iniciar sesión; las acciones y resultados bajo prueba siguen ocurriendo en la interfaz.
4. **Escribir el escenario BDD.** Usar la sintaxis de Gherkin reconocida por Behave (`Feature`, `Scenario`, `Given`, `When`, `Then`, `And`) y redactar el comportamiento del negocio en español. Etiquetar cada escenario con su `TC` y las referencias `HU`/`CA` aplicables. Un `TC` puede tener una automatización, varias capas o ejecución manual; no inferir cobertura solo por tener una etiqueta.
5. **Conectar el escenario con sus pasos.** Mantener las definiciones de pasos agrupadas por funcionalidad. Los pasos expresan intención y resultado; delegan las interacciones del navegador a Page Objects. Los Page Objects encapsulan localizadores, navegación e interacción, y usan esperas explícitas para estados observables. La configuración y ciclo de vida de Selenium se mantiene en `testsupport` y los hooks de Behave.
6. **Ejecutar y observar.** Para cada escenario, crear un navegador independiente, ejecutar las acciones, comprobar el resultado esperado y registrar el estado real. La corrida completa usa un identificador `QA_RUN_ID`; los escenarios que escriben en la base verifican previamente `QA_ISOLATED_DB=1`.
7. **Conservar evidencia y cerrar recursos.** Los hooks guardan captura y texto visible de la página por escenario, incluso cuando falla, y cierran el navegador. Si no se inicia el navegador, no se genera evidencia de interfaz. La salida de Behave y los reportes JUnit complementan estas evidencias.
8. **Registrar el resultado.** Añadir una fila por caso y corrida en `test-runs/executions.csv`, vinculando `TC`, corrida, commit, ambiente, resultado observado, evidencia y defecto confirmado. Mantener la fila de intentos anteriores; después de una corrección se registra una nueva ejecución. Diseños y ejecuciones se contabilizan por separado.
9. **Interpretar y corregir.** Confirmar los fallos contra el resultado esperado, registrar defectos reproducibles y volver a ejecutar el caso afectado tras el cambio. Reportar cobertura de criterios y resultados con base en ejecuciones, distinguiendo aprobados, fallidos, bloqueados, parciales y no ejecutados.

## Aplicación a Dulce Miel

La suite funcional de navegador se encuentra en `tests/functional/features/`, con pasos en `steps/`, Page Objects en `pages/` y configuración del navegador en `testsupport/`. La preparación de cuentas mediante API sirve como apoyo de datos para escenarios de UI; no convierte esas comprobaciones en pruebas exclusivamente de API. Las comprobaciones directas de API se mantienen en la colección Newman. Pruebas unitarias, integración, compatibilidad, accesibilidad y rendimiento conservan sus herramientas y niveles propios.

El tag `@writes` es una protección del entorno, no un resultado de prueba: `environment.py` exige la marca de base aislada antes de abrir Chrome para escenarios con escritura. La base de QA debe inicializarse según `infra/bootstrap.ps1`; no se debe cambiar esa protección para apuntar a la base de trabajo.

Las prácticas orientan la estructura, pero sus cantidades y particularidades pertenecen a cada ejercicio. Semana 1 fija el alcance, los perfiles, el ambiente académico y la necesidad de trazabilidad; Semana 2 establece las historias y criterios de aceptación que originan los casos; Semana 4 aporta priorización por riesgo, niveles y tipos de prueba, datos controlados y regresión. Semana 5 desarrolla BDD y la separación entre historia, criterios y casos. T1/Campus360 muestra la combinación de pruebas unitarias con patrón Arrange-Act-Assert y escenarios BDD con pasos, casos válidos, errores y límites, además de resultados ejecutados con xUnit/SpecFlow. Semana 8 organiza casos por identificadores y usa Page Objects con Selenium/Playwright. AulaNova muestra escenarios Behave, pasos separados, esperas explícitas, creación y liberación de recursos por escenario y registro de evidencia. Sus conteos, tecnologías .NET y arquitectura de servidor no se trasladan literalmente a Dulce Miel.

En los materiales disponibles no hay carpetas de prácticas independientes para cada semana del curso; se revisaron los documentos encontrados en `Practicas de campo`, las semanas 5, 8 y 9, el material de clase y las entregas T1/Campus360. La práctica de T1 usa palabras clave Gherkin en español con SpecFlow; esta suite usa `--lang en` porque Behave selecciona esas palabras clave, y mantiene en español la descripción del negocio.

## Comandos de la corrida funcional

Desde `qa/`, con backend y frontend locales disponibles:

```powershell
$env:QA_ISOLATED_DB = '1'
$env:QA_RUN_ID = (Get-Date -Format 'yyyyMMdd-HHmmss')
$env:QA_ARTIFACTS = '..\..\evidencias-criterio5'
py -m behave tests/functional/features --lang en --junit --junit-directory '..\..\evidencias-criterio5' -f progress
```

La opción `--lang en` selecciona las palabras clave inglesas de Gherkin; el texto descriptivo de funcionalidades, escenarios y pasos permanece en español.
