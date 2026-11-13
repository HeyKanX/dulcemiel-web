# Cierre de fase 2: diagnóstico y evidencia

Fecha de corte: 13 de noviembre de 2026  
Base de diagnóstico: `885fe83e069724d622733f8d2668fee957d7a486`; las correcciones se reprodujeron y verificaron localmente. Actualización: se trasladaron a la rama `qa/phase3-metrics-ci` del PR #8 para validación remota; `main` sigue sin cambios hasta superar revisión y CI.  
Alcance de ejecución: stack QA desechable `dm-phase2-47311c38`, con SQL Server, backend y frontend propios. No se detuvieron ni modificaron los contenedores de Jenkins, TestLink ni los otros entornos QA.

## Resultado ejecutivo

- Se corrigió en backend el rechazo de cantidades cero, negativas y no enteras antes de consultar o escribir en SQL.
- Se corrigió el alta administrativa de producto sin imagen: el valor nulo de `imagen_data` ahora se envía como `VARBINARY`, que es el tipo de la columna SQL Server.
- Verificación posterior: Maven **28/28** pruebas, con **0 fallos**; incluye **7** integraciones contra SQL Server real en Testcontainers. El recuento se reconcilió con los siete XML Surefire presentes en `backend/target/surefire-reports/` durante fase 3. Newman: **32 solicitudes, 33 aserciones, 0 fallos**.
- Behave en la interfaz: **3/4 aprobados**. Se reproduce el fallo de `TC-NF-INT-002` al recargar catálogo con sesión activa. El endpoint del catálogo devuelve 200 y siete productos en consulta directa; en el navegador, después de la recarga, no se observa una solicitud a `/api/productos` y la vista muestra el mensaje de error. Se mantiene **No aprobado** y abierto; no se cambió la prueba para ocultarlo ni se atribuyó una causa de código sin evidencia suficiente.
- Accesibilidad automatizada: **4 de 9 rutas escaneadas**; las otras **5 quedaron sin análisis válido**, incluyendo rutas protegidas que redirigieron a login. En las rutas escaneadas se detectaron **9 nodos** con violaciones axe distribuidas en cinco grupos de regla/página. Los resultados sin escaneo no cuentan como defectos ni como aprobados.
- SpotBugs: **9 avisos P2** revisados. Ocho `EI_EXPOSE_REP2` se clasifican como falsos positivos de dependencias compartidas inyectadas por Spring en controladores singleton. El `CT_CONSTRUCTOR_THROW` de `JwtService` se clasifica como informativo/no confirmado: la excepción al construir una clave inválida aborta el arranque intencionalmente y no se observó escape del objeto parcialmente construido.

## Diagnóstico y correcciones funcionales

| Caso / hallazgo | Diagnóstico | Acción | Evidencia posterior |
|---|---|---|---|
| `TC-F-010`: cantidad cero aceptada | `CarritoController.add()` validaba ausencia, pero no que la cantidad fuera mayor que cero; la base tenía una restricción que no se usaba para devolver un 400 controlado. | Se rechazan `cantidad < 1` antes de SQL. El parseo ahora requiere entero exacto para no truncar valores como 1.5. La ruta de actualización aplica la misma regla. | Maven 28/28; Newman valida cantidad cero como HTTP 400 y 0 escrituras en carrito. |
| Cantidad negativa/fraccionaria y actualización a cero | El controlador podía aceptar negativos y truncar fracciones; actualizar cero podía alcanzar la restricción SQL y devolver error del servidor. | Se agregaron pruebas unitarias para negativo, fracción y actualización con cero. | `CarritoControllerAuditTest`: 8/8; integración SQL verifica cero sin persistencia. |
| `TC-F-017`: crear producto sin imagen | El NULL de `imagen_data` llegaba a SQL Server como NVARCHAR implícito, incompatible con VARBINARY; explicaba el HTTP 500 de Newman. | El parámetro se tipó explícitamente como `Types.VARBINARY`; no se hizo obligatoria la imagen. | Prueba de integración crea producto sin imagen y confirma persistencia con `imagen_data IS NULL`; Newman termina 0/33 aserciones fallidas. |
| `TC-NF-INT-002`: recargar catálogo con sesión | El flujo se reproduce en el stack aislado. La respuesta directa de `GET /api/productos` es 200 con siete productos; al refrescar la página el navegador carga Angular pero no inicia una solicitud a `/api/productos` y queda el mensaje “No se pudieron cargar los productos.” | Se deja abierto para diagnóstico adicional del ciclo de arranque/ruta de la SPA. No se cambió frontend ni el criterio para forzar aprobación. | Behave 3/4; artefactos en `qa/artifacts/phase2-47311c38/behave-full` y `qa/artifacts/phase2-47311c38/behave`. |

### Pruebas de backend ejecutadas

El build local completo de Maven ejecutó **28 pruebas**, con **28 aprobadas, 0 fallidas, 0 errores y 0 omitidas**. El conteo se obtuvo sumando los atributos `tests/failures/errors/skipped` de los siete XML Surefire actuales. Incluye:

- unitarias y de auditoría del carrito;
- prueba identificada como TDD `CarritoCa11TddTest`;
- pedidos y autenticación;
- siete pruebas de integración con SQL Server efímero real, incluida la validación de carrito y el alta de producto sin imagen.

Esto reemplaza, para el cambio local actual, el fallo del build #8: **no se debe interpretar como resultado de un nuevo build remoto**. Jenkins/GitHub todavía necesitan recibir estas correcciones y ejecutar su propio build para confirmarlas allí.

## Clasificación de accesibilidad

Fuente: `axe-results.json` del build #8 y pruebas previas del conjunto Playwright. Impacto de axe describe la regla automatizada; severidad del registro se asigna según el impacto en la tarea y la política de `defect-register.json`.

| Ruta / control | Regla / impacto axe | Severidad del registro | Caso asociado | Clasificación |
|---|---|---|---|---|
| Registro, cuatro campos | `label` / critical | Alta | `TC-NF-ACC-002` | Confirmado: controles de autenticación no tienen nombre accesible programático. |
| Inicio de sesión, dos campos | `label` / critical | Alta | `TC-NF-ACC-003` | Confirmado por axe; Narrador/lector de pantalla debe seguir validándose manualmente para el anuncio hablado. |
| Catálogo, selector de categoría | `select-name` / critical | Media | `TC-NF-ACC-004` | Confirmado y agrupado con el defecto existente de filtros sin etiqueta; no se duplica como un defecto distinto. |
| Detalle del producto, campo de cantidad | `label` / critical | Media | `TC-NF-ACC-006` | Confirmado: campo no tiene etiqueta programática, aunque su propósito se identifica visualmente. |
| Detalle, enlace “Volver a productos” | `color-contrast` / serious | Media | `TC-NF-ACC-014` | Confirmado: 4.32:1 frente a 4.5:1 para texto normal. |
| Carrito, checkout, seguimiento, dashboard y ruta raíz | No hubo resultado axe válido en ese build | — | Casos correspondientes | **Sin conclusión**: bloqueo/redirect o ruta no escaneada; no equivale a aprobado ni a defecto. |

El registro conserva abiertos los hallazgos confirmados del catálogo, carrito y checkout anteriores. El caso `TC-NF-ACC-008` sobre anuncios de cambio y `TC-NF-ACC-009` sobre etiquetas del checkout siguen respaldados por las verificaciones Playwright previas y no se corrigieron en este trabajo. La ejecución manual reportada por la persona usuaria dejó el recorrido de registro solo con teclado y la compra solo con teclado aprobados; el seguimiento con lector de pantalla quedó no aprobado por estructura/anuncio y bloqueo al abrir detalle. Esos recorridos manuales no se convierten en resultados axe.

## Clasificación SpotBugs del build #8

| Hallazgo | Cantidad | Clasificación | Decisión |
|---|---:|---|---|
| `EI_EXPOSE_REP2` en 8 controladores (`JdbcTemplate` inyectado) | 8 | Falso positivo contextual | Los controladores son beans singleton de Spring y reciben un colaborador compartido mediante constructor; no exponen un objeto mutable de dominio al consumidor ni devuelven el campo. No se agrega como defecto confirmado. |
| `CT_CONSTRUCTOR_THROW` en `JwtService` | 1 | Informativo / no confirmado | La construcción de una clave JWT inválida debe impedir iniciar el servicio. No se detectó objeto publicado ni finalizador/subclase que haga explotable el estado parcial. Se conserva como aviso estático y se puede revisar si la política exige reducir avisos. |

El reporte bruto está en `qa/artifacts/github-actions-build-8/dulce-miel-quality-8-1/backend/target/spotbugsXml.xml`. La prioridad P2 del analizador no sustituye la evaluación de explotabilidad/impacto.

## Estado de defectos

- **Corregidos localmente y verificados:** `DEF-F-004` (cantidad cero) y `DEF-F-005` (producto sin imagen). No cuentan aún como corregidos en rama remota hasta ejecutar Jenkins/GitHub con los cambios integrados.
- **Abiertos de accesibilidad:** `DEF-ACC-001` a `DEF-ACC-006`, con el selector ya agrupado dentro de `DEF-ACC-001`.
- **Abierto para diagnóstico de interfaz:** `TC-NF-INT-002`; falta rastrear por qué la recarga de la SPA no lanza la consulta de catálogo en el entorno automatizado y repetir el caso después del ajuste.
- **No confirmado como defecto:** nueve avisos P2 de SpotBugs, clasificados arriba.

El registro estructurado actualizado está en `qa/metrics/defect-register.json`.

## Evidencias de esta ejecución

- Maven completo: `backend/target/surefire-reports/`. La cobertura JaCoCo no se recalculó en esta fase.
- Newman: `qa/artifacts/phase2-47311c38/api-fixed/newman.xml` (32 solicitudes, 33 aserciones, cero fallos).
- Behave: `qa/artifacts/phase2-47311c38/behave-full/` (3 aprobados, 1 no aprobado).
- Stack efímero usado: contenedores prefijo `dm-phase2-47311c38-`; frontend/API en puertos 54200/55001.
- Axe / SpotBugs build #8: artefactos históricos indicados en las secciones anteriores.

## Criterio de paso a fase 3

La fase 2 queda **cerrada como diagnóstico y corrección verificable de los fallos identificados**, con un fallo de integración documentado que no debe ocultarse. Se puede iniciar la fase 3 usando resultados reproducibles y separando lo verificado de lo pendiente. Antes de dar la calidad de interfaz como conforme, falta resolver y volver a ejecutar `TC-NF-INT-002`, corregir los hallazgos abiertos de accesibilidad según prioridad, e integrar/repetir en Jenkins las correcciones locales para que el resultado remoto y TestLink correspondan a la misma corrida.

No se publica a TestLink desde este entorno local porque no se generó aquí un resultado completo con el mapeo de todos los IDs del pipeline; el informe y los JUnit quedan disponibles para una corrida Jenkins posterior.
