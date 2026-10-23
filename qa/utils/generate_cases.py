"""Exporta diseño de casos y ejecuciones por separado desde la Tabla C2."""
import csv
from pathlib import Path

from docx import Document


QA_ROOT = Path(__file__).resolve().parents[1]
REPORT = QA_ROOT.parents[2] / "Informe" / "2026-2_ISC-Informe_Proyecto Final_Calidad y Prueba de Software.docx"
CASES_OUT = QA_ROOT / "test-design" / "cases.csv"
RUNS_OUT = QA_ROOT / "test-runs" / "executions.csv"

DOMAIN = {
    **{n: ("RF01", "registro") for n in (1, 2, 20, 21)},
    **{n: ("RF02", "sesion") for n in (3, 4, 22)},
    **{n: ("RF03", "catalogo") for n in (5, 6, 23, 24)},
    **{n: ("RF04", "detalle") for n in (7, 8, 25)},
    **{n: ("RF05", "carrito") for n in (9, 10, 11, 26, 27)},
    **{n: ("RF06", "pedido") for n in (12, 13, 28, 29)},
    **{n: ("RF07", "seguimiento") for n in (14, 15, 30)},
    **{n: ("RF08", "administracion_productos") for n in (16, 17)},
    **{n: ("RF09", "administracion_pedidos") for n in (18, 19)},
}

AUTOMATION = {
    1: "Behave; Newman", 2: "Behave; Newman", 3: "Newman", 4: "Behave",
    5: "Behave; Newman", 7: "Behave", 8: "Behave; Newman", 9: "Behave; Newman",
    10: "Newman", 11: "Newman", 12: "Newman parcial", 13: "Behave parcial; Newman parcial",
    14: "Newman parcial", 15: "Newman parcial", 16: "Newman parcial; actualización bloqueada",
    17: "Behave parcial; Newman", 18: "Newman parcial", 19: "Newman parcial",
    20: "axe DevTools Extension; revisión manual", 21: "axe DevTools Extension; revisión manual",
    22: "axe DevTools Extension; revisión manual", 23: "axe DevTools Extension; revisión manual",
    24: "axe DevTools Extension; revisión manual", 25: "axe DevTools Extension; revisión manual",
    26: "axe DevTools Extension; revisión manual", 27: "axe DevTools Extension; revisión manual",
    28: "axe DevTools Extension; revisión manual", 29: "axe DevTools Extension; revisión manual",
    30: "axe DevTools Extension; revisión manual", 31: "axe DevTools Extension; revisión manual",
    32: "axe DevTools Extension; revisión manual", 33: "axe DevTools Extension; revisión manual",
    34: "axe DevTools Extension; revisión manual",
}

DATA = {
    1: "correo qa-<corrida>@example.test; contraseña sintética; nombre Caso QA",
    2: "mismo correo sintético registrado previamente",
    3: "cliente QA activo; credenciales sintéticas",
    4: "correo inexistente y contraseña sintética incorrecta; cuenta inactiva en subcaso manual",
    5: "Miel QA; precio 12.50; stock 5",
    7: "identificador de Miel QA",
    8: "identificador 2147483647",
    9: "Miel QA; añadir 4 con stock 5",
    10: "Miel QA; stock 5; carrito con 4; intentar añadir cantidad 0",
    11: "Miel QA; stock 5; carrito con 4; añadir 2",
    12: "carrito válido; nombre, teléfono, dirección y distrito sintéticos",
    13: "carrito vacío o teléfono abc; pedido no persistido",
    17: "cliente QA intenta POST /api/productos",
    19: "estado no permitido y pedido inexistente",
    32: "zoom 200 % y ancho 390/1365 píxeles",
    33: "contraste WCAG AA de controles críticos",
}

RESULTS = {
    "TC-F-001": ("parcial aprobado", "Registro y respuesta API correctos; recorrido web aprobado", "behave.log; api-newman.xml", "", "", "Behave; Newman"),
    "TC-F-002": ("parcial aprobado", "Correo duplicado rechazado en API y web", "behave.log; api-newman.xml", "", "", "Behave; Newman"),
    "TC-F-003": ("parcial aprobado", "Login API correcto; rol cliente observado", "api-newman.xml", "", "", "Newman"),
    "TC-F-004": ("parcial aprobado", "Credenciales incorrectas rechazadas en web; cuenta inactiva pendiente", "behave.log", "", "", "Behave"),
    "TC-F-005": ("parcial aprobado", "Catálogo y producto sintético visibles", "behave.log; api-newman.xml", "", "", "Behave; Newman"),
    "TC-F-007": ("parcial aprobado", "Detalle del producto visible en web", "behave.log", "", "", "Behave"),
    "TC-F-008": ("parcial aprobado", "API devuelve 404; mensaje web no comprobado íntegramente", "behave.log; api-newman.xml", "", "", "Behave; Newman"),
    "TC-F-009": ("parcial aprobado", "API agregó cuatro unidades; falta recorrido completo de interfaz", "api-newman.xml", "", "", "Newman parcial"),
    "TC-F-010": ("fallido", "La API aceptó cantidad cero con HTTP 201; se esperaba HTTP 400 y conservar carrito y stock.", "api-newman.xml", "D-C5-02", "media", "Newman"),
    "TC-F-012": ("fallido", "Con stock cinco, 4+2 respondió 201 y dejó seis; se esperaba rechazo y conservar cuatro", "api-newman.xml", "D-C5-01", "alta", "Newman"),
    "TC-F-013": ("parcial aprobado", "API generó pedido, vació carrito y descontó stock; interfaz pendiente", "api-newman.xml", "", "", "Newman parcial"),
    "TC-F-014": ("parcial aprobado", "API rechazó carrito vacío; otros campos y mensajes web pendientes", "behave.log; api-newman.xml", "", "", "Behave parcial; Newman parcial"),
    "TC-F-015": ("parcial aprobado", "API devolvió el pedido del cliente QA; vista de seguimiento pendiente", "api-newman.xml", "", "", "Newman parcial"),
    "TC-F-016": ("parcial aprobado", "API mostró detalle y subtotal propio; vista de seguimiento pendiente", "api-newman.xml", "", "", "Newman parcial"),
    "TC-F-017": ("parcial fallido", "POST de producto sin imagen respondió 500; actualización dependiente bloqueada", "api-newman.xml; api-newman.log", "D-C5-06", "alta", "Newman parcial"),
    "TC-F-018": ("parcial aprobado", "Cliente recibió 403 y el producto no apareció en catálogo", "behave.log; api-newman.xml", "", "", "Behave parcial; Newman"),
    "TC-F-019": ("parcial aprobado", "API aceptó estado permitido y lo devolvió; UI pendiente", "api-newman.xml", "", "", "Newman parcial"),
    "TC-F-020": ("parcial aprobado", "API rechazó estado inválido y pedido inexistente sin cambiar estado", "api-newman.xml", "", "", "Newman parcial"),
    "TC-NF-ACC-002": ("parcial fallido", "Cuatro campos de registro sin nombre accesible; revisión de lector pendiente", "axe-results.json", "D-C5-04", "alta", "axe-core exploratorio"),
    "TC-NF-ACC-003": ("parcial fallido", "Dos campos de login sin nombre accesible; revisión de lector pendiente", "axe-results.json", "D-C5-04", "alta", "axe-core exploratorio"),
    "TC-NF-ACC-015": ("parcial fallido", "Selector de categoría sin nombre accesible; consistencia global pendiente", "axe-results.json", "D-C5-05", "media", "axe-core exploratorio"),
    "TC-NF-REN-001": ("aprobado en entorno local", "Tres perfiles bajo p95 de página HTTP 3000 ms y 0 % de errores", "k6-smoke.json; k6-baseline.json; k6-moderate.json", "", "", "k6"),
    "TC-NF-REN-002": ("aprobado en entorno local", "Tres perfiles bajo p95 de API 2000 ms y 0 % de errores", "k6-smoke.json; k6-baseline.json; k6-moderate.json", "", "", "k6"),
    "TC-NF-COM-001": ("parcial aprobado", "Seis combinaciones motor/ancho sin desbordamiento en dos vistas", "playwright.log", "", "", "Playwright"),
    "TC-NF-SEG-001": ("parcial aprobado", "Cliente obtuvo 403 y producto no apareció", "api-newman.xml", "", "", "Newman parcial"),
    "TC-NF-INT-001": ("parcial aprobado", "Pedido con carrito vacío rechazado; dato inválido completo pendiente", "api-newman.xml", "", "", "Newman parcial"),
    "TC-NF-INT-002": ("fallido", "Tras login y recarga del catálogo se mostró error de carga", "behave.log; CNF-INT-02_*.png", "D-C5-03", "media", "Behave/Selenium"),
}

EXTRA = [
    ("TC-NF-REN-001", "RNF03", "rendimiento", "GET /productos; 1 VU 30 s, luego 3 VU 2 min", "p95 <= 3000 ms; registrar p50/p90/p95/p99 y errores", "k6"),
    ("TC-NF-REN-002", "RNF03", "rendimiento", "GET /api/productos; mismos perfiles", "p95 <= 2000 ms; registrar p50/p90/p95/p99 y errores", "k6"),
    ("TC-NF-COM-001", "RNF04", "compatibilidad", "abrir catálogo y registro en 390/1365 px con tres motores", "tareas visibles y sin desbordamiento horizontal", "Playwright"),
    ("TC-NF-SEG-001", "RNF02", "seguridad", "cliente intenta crear producto", "HTTP 403; ningún cambio persistido", "Newman"),
    ("TC-NF-INT-001", "RNF05/RNF06", "integridad", "rechazar pedido con dato inválido; consultar pedidos y carrito", "sin pedido creado ni cambio del carrito", "Newman"),
    ("TC-NF-INT-002", "RNF06", "integridad", "iniciar sesión y recargar catálogo", "la sesión persiste y el catálogo sigue mostrando productos", "Behave/Selenium"),
]

DESIGN_FIELDS = ["id_caso", "commit_base", "tipo_prueba", "nivel_prueba", "historia", "criterio_aceptacion", "requisito", "dominio", "prioridad", "tecnica", "precondiciones", "perfil", "navegador", "datos", "pasos", "resultado_esperado", "herramienta_planificada"]
RUN_FIELDS = ["id_corrida", "fecha", "id_caso", "commit_base", "ambiente", "resultado", "resultado_observado", "evidencia", "defecto", "severidad", "herramienta_ejecutada"]


def case_id(number):
    if number <= 10:
        return f"TC-F-{number:03d}"
    if number <= 19:
        return f"TC-F-{number + 1:03d}"
    return f"TC-NF-ACC-{number - 19:03d}"


def main():
    doc = Document(REPORT)
    table = next(t for t in doc.tables if len(t.columns) == 5 and t.rows[0].cells[0].text.strip() == "ID" and t.rows[0].cells[1].text.strip() == "HU" and any(row.cells[0].text.strip() == "CA01" for row in t.rows))
    cases, runs = [], []
    for cells in table.rows[1:]:
        ca, hu, given, when, then = [c.text.strip() for c in cells.cells]
        n = int(ca[2:])
        rf, domain = DOMAIN.get(n, ("RF08/RF09" if n == 31 else "RF01-RF09", "transversal"))
        is_accessibility = n >= 20
        kind = "accesibilidad" if is_accessibility else "funcional"
        rnf = "RNF01" if is_accessibility else ("RNF02" if n in (3, 4, 17, 19) else "RNF05" if n in (9, 10, 11, 12, 13, 18) else "")
        cid = case_id(n)
        data = DATA.get(n, "datos sintéticos del escenario; completar identificadores en la corrida")
        steps, expected = when, then
        if n == 10:
            data = "Miel QA; stock 5; carrito con 4; intentar añadir cantidad 0"
            steps = "Cuando intenta añadir cero unidades al carrito"
            expected = "Entonces la API rechaza la cantidad con HTTP 400 y conserva sin cambios el carrito y el stock."
        cases.append({
            "id_caso": cid, "commit_base": "9e46844", "tipo_prueba": kind, "nivel_prueba": "aceptación",
            "historia": hu, "criterio_aceptacion": ca, "requisito": ";".join(x for x in (rf, rnf) if x),
            "dominio": domain, "prioridad": "alta" if n in (1, 2, 3, 4, 9, 10, 11, 12, 13, 17, 18, 19, 20, 21, 22, 26, 28, 29, 32) else "media",
            "tecnica": "teclado; semántica; inspección" if is_accessibility else "caja negra; partición/límite o transición según datos",
            "precondiciones": given, "perfil": "visitante" if n in (1, 2, 5, 6, 7, 8, 20, 21, 23, 24, 25) else "cliente" if n in (3, 4, 9, 10, 11, 12, 13, 14, 15, 22, 26, 27, 28, 29, 30) else "administrador" if n in (16, 18, 19, 31) else "sin permiso" if n == 17 else "todos",
            "navegador": "No aplica para API; Chrome para Behave" if AUTOMATION.get(n, "").startswith("Newman") else "Chrome; Chromium/Firefox/WebKit si aplica",
            "datos": data, "pasos": steps, "resultado_esperado": expected,
            "herramienta_planificada": AUTOMATION.get(n, "Behave/Selenium" if not is_accessibility else "axe DevTools Extension; revisión manual"),
        })
        if n == 10:
            cases.append({
                "id_caso": "TC-F-011", "commit_base": "9e46844", "tipo_prueba": "funcional", "nivel_prueba": "aceptación",
                "historia": hu, "criterio_aceptacion": ca, "requisito": "RF05;RNF05", "dominio": "carrito",
                "prioridad": "alta", "tecnica": "caja negra; partición válida y transición de estado",
                "precondiciones": "Dado que el cliente tiene Miel QA en el carrito y puede modificarlo", "perfil": "cliente",
                "navegador": "Chrome; API según la ejecución", "datos": "Miel QA; cantidad válida 1; eliminación del producto",
                "pasos": "Cuando modifica la cantidad a un valor válido y luego elimina el producto del carrito",
                "resultado_esperado": "Entonces el subtotal se actualiza según la cantidad y, al eliminar, el producto deja de aparecer y el total se recalcula.",
                "herramienta_planificada": "Newman; Behave/Selenium",
            })

    for cid, requirement, kind, steps, expected, tool in EXTRA:
        cases.append({
            "id_caso": cid, "commit_base": "9e46844", "tipo_prueba": kind, "nivel_prueba": "sistema",
            "historia": "transversal", "criterio_aceptacion": "", "requisito": requirement,
            "dominio": kind, "prioridad": "alta", "tecnica": "medición/revisión dirigida",
            "precondiciones": "SQL local aislado y servicios QA activos", "perfil": "visitante/cliente según caso",
            "navegador": "Chrome o matriz Playwright según caso", "datos": "dataset sintético QA; sin datos personales",
            "pasos": steps, "resultado_esperado": expected, "herramienta_planificada": tool,
        })

    for case in cases:
        result = RESULTS.get(case["id_caso"])
        if not result:
            continue
        status, observed, evidence, defect, severity, tool = result
        runs.append({
            "id_corrida": "AUD-C5-20261020", "fecha": "2026-10-20", "id_caso": case["id_caso"],
            "commit_base": case["commit_base"], "ambiente": "QA local aislado",
            "resultado": status, "resultado_observado": observed, "evidencia": evidence,
            "defecto": defect, "severidad": severity, "herramienta_ejecutada": tool,
        })

    for path, rows, fields in ((CASES_OUT, cases, DESIGN_FIELDS), (RUNS_OUT, runs, RUN_FIELDS)):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    print(f"{len(cases)} casos diseñados; {len(runs)} registros de ejecución guardados.")
    print(f"Diseño: {CASES_OUT}\nEjecuciones: {RUNS_OUT}")


if __name__ == "__main__":
    main()
