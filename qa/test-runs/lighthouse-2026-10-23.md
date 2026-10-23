# Resultado de Lighthouse en el catálogo desplegado

La evidencia entregada corresponde a `https://jolly-smoke-017f42010.5.azurestaticapps.net/productos`, capturada el **23 de octubre de 2026 a las 5:10 a. m. (GMT-5)**. El PDF indica Lighthouse **13.4.1**, Chromium **155**, escritorio emulado, una carga inicial y limitación de red personalizada. Es una medición puntual; las puntuaciones estimadas pueden variar entre corridas.

| Categoría | Puntuación |
|---|---:|
| Rendimiento | 88/100 |
| Accesibilidad | 94/100 |
| Buenas prácticas | 100/100 |
| SEO | 83/100 |

Lighthouse registró FCP **1,2 s**, LCP **1,7 s**, TBT **0 ms**, CLS **0,03** e índice de velocidad **1,6 s**. Señaló un ahorro estimado de **1.330 KiB** en entrega de imágenes y de **310 ms** al usar protocolos HTTP modernos en las respuestas indicadas. Estas recomendaciones son oportunidades de optimización, no fallos de una meta de rendimiento acordada. La corrida mide la página desplegada y no se combina con las mediciones k6 del entorno local, que usan otros perfiles y una métrica HTTP distinta.

En accesibilidad, la auditoría puntuó **94/100** y detectó que el selector de categoría no tiene etiqueta asociada. El hallazgo coincide con `select-name` de la corrida axe-core pública del mismo día y aporta evidencia adicional para `TC-NF-ACC-015` / `CA34`. Como recomendaciones sin peso en la puntuación, Lighthouse señaló cuatro imágenes cuyo texto alternativo parece redundante con texto cercano y cuatro enlaces de igual destino cuya descripción debería revisarse. Esos elementos se relacionan con `TC-NF-ACC-004` / `CA23`, pero requieren lectura del contexto y validación humana antes de clasificarse como defectos. La comprobación automática tampoco ejecuta los recorridos de teclado o lector de pantalla.

En SEO, el PDF señala falta de metadescripción y **13 errores de sintaxis en `robots.txt`**; la respuesta mostrada contiene HTML en vez de directivas para rastreadores. La puntuación de buenas prácticas no certifica seguridad: el propio PDF enumera observaciones sin puntuación sobre CSP, HSTS, COOP y control de incrustación que requieren una evaluación aparte.

El PDF original se conservó sin cambios en `Auditoria/evidencias-criterio5/lighthouse/20261023-publico/catalogo-lighthouse.pdf`. El resumen de esta corrida se mantiene separado del registro axe-core para conservar herramienta, página, fecha y alcance de cada resultado.
