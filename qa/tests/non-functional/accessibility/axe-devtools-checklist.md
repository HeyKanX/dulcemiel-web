# Revisión de accesibilidad con axe DevTools Extension

Realizar la revisión en el entorno local de QA, con datos sintéticos y una corrida identificada. Configurar axe DevTools Extension para WCAG 2.2 nivel AA y registrar el navegador y la versión de la aplicación.

La alternativa automatizada con axe-core para pantallas públicas está en `axe_core_scan.py`. Sus resultados se documentan por corrida en `qa/test-runs/`; mantienen aparte las tareas manuales de teclado, foco, zoom y lector de pantalla.

## Escaneo por página

1. Abrir una ruta cubierta por los casos de accesibilidad: registro, inicio de sesión, catálogo, detalle, carrito, checkout, seguimiento o panel administrativo.
2. Abrir las herramientas de desarrollo del navegador, seleccionar la pestaña **axe DevTools** y ejecutar **Full Page Scan**.
3. Registrar las reglas detectadas, impacto, cantidad y selectores indicados. Guardar una captura del resumen y de cada hallazgo que se relacione con un criterio CA.
4. Revisar cada hallazgo en el DOM y confirmar si corresponde a un defecto. Los elementos que la herramienta marque para revisión se verifican manualmente.
5. Relacionar la evidencia con `id_caso` (`TC-NF-ACC-*`) y `CAxx` en `manual_review.csv` y en la hoja de ejecución.

La edición gratuita permite revisar una página por vez y no ofrece todas las funciones de exportación y seguimiento. Para este proyecto, las capturas y el registro manual forman la evidencia de la corrida.

## Comprobaciones manuales complementarias

Registrar cada tarea con resultado observado, estado, evidencia, revisor y fecha:

- Completar recorridos principales únicamente con teclado; verificar orden lógico y foco visible.
- Provocar errores de validación y comprobar que se anuncie el campo y una indicación útil para corregirlo.
- Revisar nombres accesibles, etiquetas, roles, títulos y estados dinámicos con tecnología de asistencia.
- Ampliar la interfaz al 200 % y verificar que no se pierdan contenido ni funciones esenciales.
- Comprobar contraste de texto y controles con los umbrales que correspondan a WCAG 2.2 AA.
- Recorrer las tareas principales con NVDA u otro lector de pantalla disponible.

Un escaneo automatizado cubre solo las reglas que puede evaluar con el DOM disponible; un resultado sin hallazgos no equivale a conformidad integral ni sustituye las pruebas manuales.
