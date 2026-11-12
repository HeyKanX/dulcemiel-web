# GitHub Actions para calidad de Dulce Miel

El workflow `../../.github/workflows/quality.yml` se ejecuta en `push` y pull request a `main`, o manualmente desde **Actions → Dulce Miel - Calidad automatizada → Run workflow**. Este flujo solo ejecuta pruebas; no llama a Azure ni publica el sitio.

## Qué ejecuta

- Pruebas backend Maven, incluida la integración con SQL Server mediante Testcontainers.
- Pruebas unitarias y compilación de Angular.
- Newman, Behave/Selenium, compatibilidad Playwright y axe-core.
- Los seis perfiles K6: humo, línea base, carga moderada, estrés progresivo, pico repentino y carga sostenida.
- Generación y validación local del resumen TestLink por ejecución.
- Archivo de resultados JUnit, cobertura, registros, resúmenes y evidencias como artifact del run.

El agente de pruebas se construye desde `Dockerfile.runner`. Los servicios de SQL Server, backend y frontend se levantan con Compose en una red privada única para el run. La limpieza elimina el proyecto Compose y la red de esa ejecución.

## Publicar en TestLink

La validación local del mapa se hace en cada run. La publicación real queda apagada para `push` y pull requests. Para enviarla manualmente:

1. En el repositorio de GitHub, abre **Settings → Secrets and variables → Actions**.
2. Crea los secretos `TESTLINK_URL` (endpoint XML-RPC) y `TESTLINK_DEVKEY` (clave de desarrollador). No los pongas en archivos versionados ni en logs.
3. Abre **Actions → Dulce Miel - Calidad automatizada → Run workflow**.
4. Activa `publish_testlink` solo si quieres enviar los resultados de ese run.

El publicador usa `qa/testlink/results/current-run.json` generado por ese mismo run, y valida los IDs contra `case-id-map.json`. Los casos manuales y los resultados históricos no se publican desde este workflow.

**Alcance de red:** un agente GitHub-hosted no puede resolver el TestLink que solo existe en la red Docker local (`testlink-app-1`). Para publicar desde Actions, el equipo debe usar un runner autoalojado conectado a esa red o una instancia TestLink con endpoint accesible y aprobado desde GitHub. No expongas la clave ni abras TestLink públicamente solo para habilitar el pipeline. Jenkins sigue siendo la vía de publicación mientras TestLink sea exclusivamente local.

## Interpretar el resultado

Cada suite automatizada se ejecuta aunque otra falle. El paso **Quality Gate** deja el workflow fallido si una prueba o la preparación del entorno falla; los artifacts se suben antes del cierre para conservar evidencia. Una falla de aserción debe revisarse como posible defecto de producto; una suite que no pudo iniciarse por una falla de dependencias o infraestructura no debe clasificarse como defecto funcional.

El workflow de producción `azure-static-web-apps-jolly-smoke-017f42010.yml` permanece separado: solo realiza despliegue cuando se inicia manualmente desde `main` y se confirma el parámetro de producción.
