"""Redacta el informe técnico a partir de los resultados finales y la revisión humana."""
import json
from pathlib import Path


QA = Path(__file__).resolve().parents[1]
AUDIT = QA.parents[1]
EVIDENCE = AUDIT / "evidencias-criterio5"
SUMMARY = json.loads((EVIDENCE / "summary.json").read_text(encoding="utf-8"))


def total(name):
    return sum(item.get(name, 0) for item in SUMMARY["behave"].values())


def fmt(value):
    return f"{value:.2f}".replace(".", ",")


def profile_row(name, vus, duration):
    data = SUMMARY["k6"][f"k6-{name}"]
    api = data["api_latency"]
    page = data["page_latency"]
    return f"| {name} | {vus} | {duration} | {data['http_reqs']['count']} | {fmt(api['med'])} / {fmt(api['p(90)'])} / {fmt(api['p(95)'])} / {fmt(api['p(99)'])} | {fmt(page['med'])} / {fmt(page['p(90)'])} / {fmt(page['p(95)'])} / {fmt(page['p(99)'])} | {data['request_errors']['rate']:.1%} |"


api = SUMMARY["newman"]
web_total = total("tests")
web_failed = total("failures")
web_errors = total("errors")
web_passed = web_total - web_failed - web_errors - total("skipped")
api_passed = api["tests"] - api["failures"] - api["errors"] - api["skipped"]
req_total = sum(int(x["http_reqs"]["count"]) for x in SUMMARY["k6"].values())
report = f"""# Criterio 5: resultados y reproducción de la auditoría de Dulce Miel

Fecha: 20 de octubre de 2026. Versión del producto: commit `9e46844840322566bb0eaa7f028fda2eea3b895f`. Las pruebas están en la única copia activa `codigo-auditado/qa/`. El sistema original en `Desarrollo/dulcemiel-web` sigue en su commit sin cambios de producción.

## Alcance y trazabilidad

El catálogo `codigo-auditado/qa/cases.csv` contiene **44 casos diseñados**: CA01–CA34, extraídos de la Tabla C2 del Anexo C, más diez casos no funcionales. La cobertura de diseño de CA es 34/34 = 100 %. Diseñar no equivale a ejecutar: se comprobaron por API subcasos de HU07 y HU09, mientras sus recorridos de interfaz y las revisiones manuales de accesibilidad siguen pendientes. Cada fila conserva precondiciones, perfil, datos, pasos, esperado y obtenido, prioridad, técnica, estado y evidencia. `manual_review.csv` identifica las verificaciones humanas pendientes.

| Recorrido o atributo | Historias y criterios comprobados en esta corrida | Evidencia |
|---|---|---|
| Registro y sesión | HU01 CA01–CA02; HU02 CA03–CA04 | Behave y Newman |
| Catálogo y detalle | HU03 CA05; HU04 CA07–CA08 | Behave y Newman |
| Carrito | HU05 CA09 y CA11; cantidad cero como subcaso de CA10/RNF05 | Behave y Newman |
| Pedido, seguimiento y permisos | HU06 CA12–CA13; HU07 CA14–CA15; HU08 CA16–CA17; HU09 CA18–CA19 | Behave y Newman, varios subcasos solo API |
| Accesibilidad e integración | CA21, CA22, CA34; RNF06/CNF-INT-02 | axe y Behave |
| Compatibilidad y rendimiento | RNF04/CNF-COM-01; RNF03/CNF-REN-01–02 | Playwright y k6 |

La aprobación de una comprobación parcial de API o de un escaneo no certifica por sí sola todo el criterio de aceptación. Los casos no ejecutados no entran en el numerador de aprobación.

## Ejecuciones finales

| Suite | Ejecutado | Aprobado | Fallido | Error de prueba/ambiente | Evidencia |
|---|---:|---:|---:|---:|---|
| Behave/Selenium, escenarios Gherkin | {web_total} | {web_passed} | {web_failed} | {web_errors} | `evidencias-criterio5/behave.log`, `TESTS-*.xml` y captura del fallo |
| Newman, aserciones en {SUMMARY['newman_requests']} solicitudes API | {api['tests']} | {api_passed} | {api['failures']} | {api['errors']} | `api-newman.log`, `api-newman.xml` |
| Playwright, combinaciones motor/ancho | 6 | 6 | 0 | 0 | `playwright.log` |

La colección contiene 32 solicitudes diseñadas; se ejecutaron {SUMMARY['newman_requests']} y dos quedaron bloqueadas al faltar el identificador del producto que no pudo crearse. Las aserciones de Newman suman pruebas, no criterios de aceptación completos.

De las cuatro aserciones fallidas de Newman, CA11 produjo dos fallos (respuesta y cantidad conservada), la cantidad cero produjo uno y crear producto sin imagen produjo una respuesta 500. Las dos comprobaciones dependientes de esa creación se omitieron por bloqueo; no se contaron como aprobadas ni como defectos adicionales. La corrida Behave falló en CNF-INT-02 al recargar una sesión activa. Las primeras corridas con errores de selector, un identificador de Postman sin preparar y una espera insuficiente de Angular están archivadas bajo `preparacion-*` y se excluyeron de los números finales. `api-newman-ampliada-antes-bloqueo.*` conserva la corrida que reveló la cascada de fallos por identificador ausente.

## Hallazgos revisados

| ID | Caso | Observado frente a esperado | Interpretación y ajuste recomendado |
|---|---|---|---|
| D-C5-01 | CA11 | Con stock 5 y cuatro unidades en carrito, añadir dos respondió 201 y dejó 6; se esperaba 400 y mantener 4. | Defecto del producto confirmado también por el criterio 4. Revisar validación de cantidad acumulada y operación atómica de stock. |
| D-C5-02 | CA10/RNF05 | Añadir cantidad cero respondió 201; se esperaba rechazo 400. | Falta validación de cantidad positiva en la entrada API; revisar consistencia con restricción SQL. |
| D-C5-03 | CNF-INT-02/RNF06 | Tras login correcto, recargar `/productos` mostró “No se pudieron cargar los productos”; la consulta API con token respondió 200 fuera del navegador. | Defecto observable de integración del frontend al restaurar sesión. Revisar la inicialización de AuthService y el interceptor; confirmar causa antes de reparar. |
| D-C5-04 | CA21/CA22 | axe detectó cuatro campos de registro y dos de login sin nombre accesible. Las etiquetas visibles carecen de asociación `for`/`id` o envoltura del control. | Barrera confirmada en el marcado para tecnologías de asistencia. Asociar etiquetas y errores a campos; verificar posteriormente con lector. |
| D-C5-05 | CA34 | El selector de categorías del catálogo carece de nombre accesible. | Añadir etiqueta programática y comprobar su anuncio con lector. |
| D-C5-06 | CA16 | El administrador inició sesión, pero `POST /api/productos` con datos válidos y sin imagen respondió 500; se esperaba 201. El log backend identifica conversión implícita de `nvarchar` a `varbinary(max)` al insertar `imagen_data` nulo. | Defecto de persistencia en el caso sin imagen, que el controlador declara opcional. Revisar enlace del parámetro SQL y probar con y sin imagen; actualización y lectura quedan bloqueadas en esta corrida. |

La severidad preliminar es alta para D-C5-01, D-C5-04 y D-C5-06; media para los demás. No se cambió código productivo para obtener aprobaciones. Los fallos son resultados válidos de la auditoría. La revisión de código de los componentes y los controles visibles corroboró las etiquetas sin asociación; las dificultades de selector en pruebas fueron corregidas y no se atribuyeron al producto.

## Pruebas no funcionales

Playwright evaluó Chromium, Firefox y WebKit a 390 y 1365 px. Verificó la presencia de catálogo y registro y ausencia de desbordamiento horizontal en esas vistas. Esta comprobación no equivale al recorrido completo de compra en cada motor.

axe-core analizó registro, login y catálogo: detectó una regla `label` en cada formulario (4 y 2 nodos) y `select-name` en el catálogo (1 nodo). El contraste produjo 11 nodos de evaluación incompleta en el catálogo y requiere medición humana. No se declaró conformidad WCAG 2.2 AA.

La medición k6 utilizó exclusivamente lectura (`GET /api/productos` y `GET /productos`) sobre el SQL aislado. Metas previas del informe: p95 API ≤ 2000 ms y p95 de página HTTP ≤ 3000 ms. Valores en milisegundos con orden **p50 / p90 / p95 / p99**:

| Perfil | VU | Duración | Solicitudes | API ms | Página HTTP ms | Errores |
|---|---:|---:|---:|---:|---:|---:|
{profile_row('smoke', 1, '30 s')}
{profile_row('baseline', 3, '2 min')}
{profile_row('moderate', 8, '3 min')}

Total: {req_total} solicitudes. Los tres perfiles cumplieron los umbrales declarados bajo esta carga local. La medición de página corresponde a la respuesta HTTP inicial de Angular, no al tiempo de renderizado o interacción. El dataset contiene seis productos, incluido Miel QA; la caché y el servidor de desarrollo local influyen en los tiempos. Estos datos no representan Azure ni producción.

## Ambiente y reproducción

- Windows 11 Pro (compilación 26200), 16 procesadores lógicos y 34,1 GB de RAM física; Java 25.0.3, Node 24.14.1, Chrome 155, Docker Engine 29.8.1, Python 3.14, Behave 1.3.3, Selenium 4.51.0, Playwright 1.58.0, Newman 6.2.x y k6 2.2.0. Java y Node difieren de las versiones preferidas (21 y 20); las ejecuciones descritas funcionaron en este equipo, sin afirmar compatibilidad general.
- Contenedor exclusivo `dulce-miel-qa-c5` publicado solo en `127.0.0.1:14333`; base `DulceMielBD` reconstruida con `backend/database/schema.sql` y `qa/infra/seed.sql`. El contenedor habitual `sql_servidor` del puerto 1433 no fue usado.
- Backend local en puerto 5000 y Angular local en 4200. Las cuentas de cada corrida usan correos `example.test` únicos. No se emplearon datos personales ni servicios publicados. El secreto SQL queda en `qa/.local/connection.json`, ignorado por Git.
- Instrucciones de instalación, arranque, comandos y perfiles: `codigo-auditado/qa/README.md`. La salida cruda, XML, capturas, análisis axe y resumen k6 se conservan en `evidencias-criterio5/`. `summary.json` consolida las métricas sin sustituir los archivos fuente.

## Trabajo pendiente antes de afirmar cobertura completa

Completar las rutas visuales de HU07 y HU09, y el recorrido administrativo de HU08; la actualización administrativa quedó bloqueada por D-C5-06. Revisar los CA no ejecutados y los subcasos parciales. Registrar la lista manual de teclado, foco, zoom 200 %, contraste y NVDA, con revisor y evidencia. Repetir cualquier caso con dato o ambiente inválido solo después de identificar la causa. Esta auditoría puede presentarse con fallos abiertos; el estado actual no autoriza declarar conformidad integral del sistema.
"""

output = AUDIT / "CRITERIO_5_RESULTADOS_Y_REPRODUCCION.md"
output.write_text(report, encoding="utf-8")
print(output)
