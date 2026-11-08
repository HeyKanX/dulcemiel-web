# Publicación de resultados a TestLink

El publicador envía resultados por XML-RPC únicamente cuando se ejecuta con `--publish`. Sin esa opción valida el resumen y el mapa de casos sin contactar al servidor.

## Entrada de una corrida

`results/current-run.json` debe ser generado por la misma ejecución de Jenkins. Tiene este formato:

```json
{
  "project": "Dulce Miel",
  "plan": "Plan de pruebas - Dulce Miel",
  "build": "Jenkins",
  "results": [
    {
      "case_id": "TC-F-001",
      "status": "p",
      "tool": "JUnit",
      "detail": "Resultado observado en esta ejecución",
      "evidence": "backend/target/surefire-reports/TEST-example.xml"
    }
  ]
}
```

Estados TestLink: `p` aprobado, `f` no aprobado, `b` bloqueado. No se deben copiar resultados históricos a `current-run.json`.

El mapa `results/case-id-map.json` enlaza los IDs funcionales con los casos ya registrados en TestLink. Los IDs deben verificarse contra la instancia del proyecto antes de publicar.

## Credenciales Jenkins

- Secreto de texto con ID `testlink-devkey` para la clave de desarrollador.
- Variable de entorno `TESTLINK_URL` con el endpoint XML-RPC de la instancia.

El resumen de corrida y el reporte de publicación son artefactos locales del build y no se deben confirmar al repositorio.
