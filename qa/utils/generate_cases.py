"""Extrae la Tabla C2 del informe y produce el catálogo trazable del criterio 5."""
import csv
from pathlib import Path

from docx import Document


QA_ROOT = Path(__file__).resolve().parents[1]
REPORT = QA_ROOT.parents[2] / "Informe" / "2026-2_ISC-Informe_Proyecto Final_Calidad y Prueba de Software.docx"
OUT = QA_ROOT / "cases.csv"

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
    10: "Newman parcial", 11: "Newman", 12: "Newman parcial", 13: "Behave parcial; Newman parcial",
    14: "Newman parcial", 15: "Newman parcial", 16: "Newman parcial; actualización bloqueada", 17: "Behave parcial; Newman",
    18: "Newman parcial", 19: "Newman parcial",
    20: "revisión manual pendiente", 21: "axe parcial", 22: "axe parcial", 23: "revisión manual pendiente",
    24: "revisión manual pendiente", 32: "revisión manual pendiente; Playwright aporta ancho de viewport", 34: "axe parcial",
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
    10: "producto del carrito; cantidad 0, 1 y eliminación",
    11: "Miel QA; stock 5; carrito con 4; añadir 2",
    12: "carrito válido; nombre, teléfono, dirección y distrito sintéticos",
    13: "carrito vacío o teléfono abc; pedido no persistido",
    17: "cliente QA intenta POST /api/productos",
    19: "estado no permitido y pedido inexistente",
    32: "zoom 200 % y ancho 390/1365 píxeles",
    33: "contraste WCAG AA de controles críticos",
}

FIELDNAMES = ["id", "version", "tipo", "hu", "ca", "rf_rnf", "dominio", "prioridad", "tecnica", "precondiciones", "perfil", "navegador", "datos", "pasos", "esperado", "obtenido", "estado", "evidencia", "defecto", "severidad", "automatizacion"]

# Un CA con comprobación solo de API mantiene estado parcial; no equivale a aprobar
# su recorrido de interfaz o su accesibilidad. Fuente: XML/log finales de C5.
RESULTS = {
    "CA01": ("parcial aprobado", "Registro y respuesta API correctos; recorrido web aprobado", "behave.log; api-newman.xml", "", ""),
    "CA02": ("parcial aprobado", "Correo duplicado rechazado en API y web", "behave.log; api-newman.xml", "", ""),
    "CA03": ("parcial aprobado", "Login API correcto; rol cliente observado", "api-newman.xml", "", ""),
    "CA04": ("parcial aprobado", "Credenciales incorrectas rechazadas en web; cuenta inactiva pendiente", "behave.log", "", ""),
    "CA05": ("parcial aprobado", "Catálogo y producto sintético visibles", "behave.log; api-newman.xml", "", ""),
    "CA07": ("parcial aprobado", "Detalle del producto visible en web", "behave.log", "", ""),
    "CA08": ("parcial aprobado", "API devuelve 404; mensaje web no comprobado íntegramente", "behave.log; api-newman.xml", "", ""),
    "CA09": ("parcial aprobado", "API agregó cuatro unidades; falta recorrido completo de interfaz", "api-newman.xml", "", ""),
    "CA10": ("parcial fallido", "Cantidad cero respondió 201; modificación/eliminación completa pendiente", "api-newman.xml", "D-C5-02", "media"),
    "CA11": ("fallido", "Con stock cinco, 4+2 respondió 201 y dejó seis; se esperaba rechazo y conservar cuatro", "api-newman.xml", "D-C5-01", "alta"),
    "CA12": ("parcial aprobado", "API generó pedido, vació carrito y descontó stock; interfaz pendiente", "api-newman.xml", "", ""),
    "CA13": ("parcial aprobado", "API rechazó carrito vacío; otros campos y mensajes web pendientes", "behave.log; api-newman.xml", "", ""),
    "CA14": ("parcial aprobado", "API devolvió el pedido del cliente QA; vista de seguimiento pendiente", "api-newman.xml", "", ""),
    "CA15": ("parcial aprobado", "API mostró detalle y subtotal propio; vista de seguimiento pendiente", "api-newman.xml", "", ""),
    "CA16": ("parcial fallido", "POST de producto sin imagen respondió 500; actualización dependiente bloqueada", "api-newman.xml; api-newman.log", "D-C5-06", "alta"),
    "CA17": ("parcial aprobado", "Cliente recibió 403 y el producto no apareció en catálogo", "behave.log; api-newman.xml", "", ""),
    "CA18": ("parcial aprobado", "API aceptó estado permitido y lo devolvió; UI pendiente", "api-newman.xml", "", ""),
    "CA19": ("parcial aprobado", "API rechazó estado inválido y pedido inexistente sin cambiar estado", "api-newman.xml", "", ""),
    "CA21": ("parcial fallido", "Cuatro campos de registro sin nombre accesible; revisión de lector pendiente", "axe-results.json", "D-C5-04", "alta"),
    "CA22": ("parcial fallido", "Dos campos de login sin nombre accesible; revisión de lector pendiente", "axe-results.json", "D-C5-04", "alta"),
    "CA34": ("parcial fallido", "Selector de categoría sin nombre accesible; consistencia global pendiente", "axe-results.json", "D-C5-05", "media"),
    "CNF-REN-01": ("aprobado en entorno local", "Tres perfiles bajo p95 de página HTTP 3000 ms y 0 % de errores", "k6-smoke.json; k6-baseline.json; k6-moderate.json", "", ""),
    "CNF-REN-02": ("aprobado en entorno local", "Tres perfiles bajo p95 de API 2000 ms y 0 % de errores", "k6-smoke.json; k6-baseline.json; k6-moderate.json", "", ""),
    "CNF-COM-01": ("parcial aprobado", "Seis combinaciones motor/ancho sin desbordamiento en dos vistas", "playwright.log", "", ""),
    "CNF-SEG-01": ("parcial aprobado", "Cliente obtuvo 403 y producto no apareció", "api-newman.xml", "", ""),
    "CNF-INT-01": ("parcial aprobado", "Pedido con carrito vacío rechazado; dato inválido completo pendiente", "api-newman.xml", "", ""),
    "CNF-INT-02": ("fallido", "Tras login y recarga del catálogo se mostró error de carga", "behave.log; CNF-INT-02_*.png", "D-C5-03", "media"),
}


def main():
    doc = Document(REPORT)
    table = next(t for t in doc.tables if len(t.columns) == 5 and t.rows[0].cells[0].text.strip() == "ID" and t.rows[0].cells[1].text.strip() == "HU" and any(row.cells[0].text.strip() == "CA01" for row in t.rows))
    rows = []
    for cells in table.rows[1:]:
        case_id, hu, given, when, then = [c.text.strip() for c in cells.cells]
        n = int(case_id[2:])
        rf, domain = DOMAIN.get(n, ("RF08/RF09" if n == 31 else "RF01-RF09", "transversal"))
        is_accessibility = n >= 20
        rnf = "RNF01" if is_accessibility else ("RNF02" if n in (3, 4, 17, 19) else "RNF05" if n in (9, 10, 11, 12, 13, 18) else "")
        rows.append({
            "id": case_id, "version": "9e46844", "tipo": "no funcional; aceptación" if is_accessibility else "funcional; aceptación",
            "hu": hu, "ca": case_id, "rf_rnf": ";".join(x for x in (rf, rnf) if x), "dominio": domain,
            "prioridad": "alta" if n in (1, 2, 3, 4, 9, 10, 11, 12, 13, 17, 18, 19, 20, 21, 22, 26, 28, 29, 32) else "media",
            "tecnica": "teclado; semántica; inspección" if is_accessibility else "caja negra; partición/límite o transición según datos",
            "precondiciones": given, "perfil": "visitante" if n in (1, 2, 5, 6, 7, 8, 20, 21, 23, 24, 25) else "cliente" if n in (3, 4, 9, 10, 11, 12, 13, 14, 15, 22, 26, 27, 28, 29, 30) else "administrador" if n in (16, 18, 19, 31) else "sin permiso" if n == 17 else "todos",
            "navegador": "No aplica para API; Chrome para Behave" if AUTOMATION.get(n, "").startswith("Newman") else "Chrome; Chromium/Firefox/WebKit si aplica", "datos": DATA.get(n, "datos sintéticos del escenario; completar identificadores en la corrida"),
            "pasos": when, "esperado": then, "obtenido": "", "estado": "no ejecutado", "evidencia": "", "defecto": "", "severidad": "",
            "automatizacion": AUTOMATION.get(n, "manual o pendiente de automatización"),
        })
    extra = [
        ("CNF-REN-01", "RNF03", "rendimiento", "GET /productos; 1 VU 30 s, luego 3 VU 2 min", "p95 <= 3000 ms; registrar p50/p90/p95/p99 y errores", "k6"),
        ("CNF-REN-02", "RNF03", "rendimiento", "GET /api/productos; mismos perfiles", "p95 <= 2000 ms; registrar p50/p90/p95/p99 y errores", "k6"),
        ("CNF-COM-01", "RNF04", "compatibilidad", "abrir catálogo y registro en 390/1365 px con tres motores", "tareas visibles y sin desbordamiento horizontal", "Playwright"),
        ("CNF-ACC-01", "RNF01", "accesibilidad", "registro por teclado; revisar foco y orden", "todos los controles operables, foco visible y orden lógico", "manual; axe parcial"),
        ("CNF-ACC-02", "RNF01", "accesibilidad", "revisar errores de registro con lector de pantalla", "campo y corrección identificables", "manual; axe parcial"),
        ("CNF-ACC-03", "RNF01", "accesibilidad", "completar compra al 200 % de zoom", "sin pérdida de información o función", "manual"),
        ("CNF-ACC-04", "RNF01", "accesibilidad", "medir contraste de controles esenciales", "umbral WCAG 2.2 AA aplicable", "manual; axe parcial"),
        ("CNF-SEG-01", "RNF02", "seguridad", "cliente intenta crear producto", "HTTP 403; ningún cambio persistido", "Newman parcial"),
        ("CNF-INT-01", "RNF05/RNF06", "integridad", "rechazar pedido con dato inválido; consultar pedidos y carrito", "sin pedido creado ni cambio del carrito", "Newman parcial"),
        ("CNF-INT-02", "RNF06", "integracion", "iniciar sesión y recargar catálogo", "la sesión persiste y el catálogo sigue mostrando productos", "Behave/Selenium"),
    ]
    for case_id, rnf, domain, steps, expected, automation in extra:
        rows.append({"id": case_id, "version": "9e46844", "tipo": "no funcional", "hu": "transversal", "ca": "", "rf_rnf": rnf,
                     "dominio": domain, "prioridad": "alta", "tecnica": "medición/revisión dirigida", "precondiciones": "SQL local aislado y servicios QA activos",
                     "perfil": "visitante/cliente según caso", "navegador": "Chrome o matriz Playwright según caso", "datos": "dataset sintético QA; sin datos personales",
                     "pasos": steps, "esperado": expected, "obtenido": "", "estado": "no ejecutado", "evidencia": "", "defecto": "", "severidad": "", "automatizacion": automation})
    for row in rows:
        if row["id"] in RESULTS:
            row["estado"], row["obtenido"], row["evidencia"], row["defecto"], row["severidad"] = RESULTS[row["id"]]
    with OUT.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} casos guardados en {OUT}")


if __name__ == "__main__":
    main()
