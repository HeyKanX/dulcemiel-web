# Guía manual para continuar Jenkins y TestLink

**Proyecto:** Dulce Miel  
**Estado de referencia:** 10 de noviembre de 2026  
**Commit vigente en `main`:** `4d5c4e3`

## Qué ya está hecho

- El `Jenkinsfile` para Linux está en `main` y ejecuta las suites automatizadas de backend, frontend, Newman, Behave/Selenium, Playwright, axe-core y K6.
- Las fallas de una suite quedan visibles y no detienen las suites siguientes.
- Las pruebas de QA usan una pila efímera de Docker Compose, dentro de la red privada; el pipeline limpia solo esa pila al finalizar.
- Jenkins se reinició con la imagen de QA y conserva sus trabajos e historial en el volumen persistente.
- Cada ejecución genera un resumen nuevo para TestLink. El resumen incluye solo casos automatizados con evidencia de esa ejecución; no convierte casos manuales ni resultados históricos en resultados actuales.
- Azure no se despliega al ejecutar este job de Jenkins.
- El build #5 confirmó que la publicación a TestLink funciona: se enviaron seis resultados generados por esa corrida (cinco aprobados y uno no aprobado).
- En el build #6, Jenkins ya reutilizó correctamente Chromium, Firefox y WebKit. La preparación del stack falló porque Maven se ejecutó desde la raíz del repositorio en vez de hacerlo desde `backend`; el preparador ya quedó corregido para entrar a esa carpeta.
- La corrección del preparador quedó subida a `main` en `4d5c4e3`. El siguiente paso es iniciar una nueva corrida para confirmar que el stack arranque y que se ejecuten las suites dependientes.

## 1. Iniciar sesión en Jenkins

1. Abre `http://localhost:8080` e inicia sesión con tu usuario habitual.
2. En el inicio, abre el trabajo **DulceMiel-QA**.
3. Comprueba que el trabajo use el repositorio `https://github.com/HeyKanX/dulcemiel-web.git`, la rama `*/main` y la ruta del script `Jenkinsfile`. Ya quedaron configurados así; no hace falta volver a crearlo.

## 2. Agregar la credencial de TestLink a Jenkins

La publicación real requiere una credencial disponible para el pipeline. La clave de TestLink no debe pegarse en el Jenkinsfile, en el repositorio, en la consola ni en el chat.

1. En Jenkins, abre **Manage Jenkins → Credentials → System → Global credentials (unrestricted)**. Según la versión puede aparecer como **Administrar Jenkins → Credenciales → Sistema → Credenciales globales**.
2. Selecciona **Add Credentials**.
3. En **Kind**, elige **Secret text**.
4. En **Secret**, pega la clave de desarrollador generada en la misma instancia de TestLink a la que apunta el proyecto.
5. En **ID**, escribe exactamente `testlink-devkey`.
6. Guarda. No compartas el valor de la clave.

La URL XML-RPC ya está configurada en el Jenkinsfile como `http://testlink-app-1/lib/api/xmlrpc/v1/xmlrpc.php`. El proyecto y el plan que produce el resumen son **Dulce Miel** y **Plan de pruebas - Dulce Miel**. Si la instancia local fue reemplazada o cambió de nombre, detente y verifica primero su URL y conectividad; no sustituyas la dirección por la URL del frontend.

## 3. Ejecutar las pruebas automatizadas y publicar sus resultados

1. Regresa a **DulceMiel-QA**.
2. Elige **Build with Parameters / Construir con parámetros**.
3. Marca `PUBLICAR_RESULTADOS_TESTLINK` para enviar a TestLink los resultados automatizados que genere esta corrida. Deja el parámetro desmarcado si solo deseas ejecutar y revisar el resumen sin publicarlo.
4. Inicia la ejecución y abre **Console Output / Salida de consola** o la vista **Stage View**.
5. Espera a que finalicen también los perfiles K6, incluido el de carga sostenida. No inicies una segunda corrida mientras esta siga activa.

La etapa **Validar resumen TestLink** hace primero una validación local sin publicar. Después, si el parámetro está marcado y la credencial existe, la etapa **Publicar resultados en TestLink** envía el resumen de esa misma corrida. Así no necesitas lanzar una corrida adicional solo para simular el envío.

## 4. Revisar la corrida en Jenkins

Comprueba que aparezcan las etapas de backend, frontend, Newman, Behave/Selenium, Playwright, axe-core y los perfiles K6. Si una prueba falla, Jenkins debe continuar y terminar la compilación como **FAILURE**; ese estado es correcto cuando hubo una falla real.

Abre el log de la etapa fallida para distinguir entre:

- **Falla de producto:** una aserción muestra un comportamiento distinto al esperado. Registra el caso como no aprobado; no cambies el resultado ni la lógica para hacer pasar la prueba.
- **Falla de infraestructura:** faltan Docker, dependencias, navegador o conectividad, o una suite no pudo arrancar. Registra el mensaje y revisa la etapa de preparación antes de interpretar el resultado como defecto funcional.

El build #4 anterior falló por problemas del agente Linux (wrapper Maven sin permiso de ejecución, ChromeHeadless sin ruta configurada y uso del paso `bat` de Windows). La configuración subida en `dcda046` atiende esas causas; falta confirmar el resultado ejecutando un build nuevo.

En el build #5, Maven sí ejecutó 21 pruebas: 20 pasaron y falló `CarritoControllerAuditTest.cantidadCeroDebeRechazarseAntesDeEscribir`; esperaba `400 BAD_REQUEST` y recibió `201 CREATED`. El build también falló al instalar las dependencias QA porque Playwright quiso crear un directorio de bloqueo en `/opt/ms-playwright`, que es de solo lectura para `jenkins`. Los navegadores ya están incluidos en la imagen del controlador; el instalador se ajustó para comprobarlos y reutilizarlos, sin intentar descargarlos de nuevo. Como la preparación de QA no pasó, Newman, Behave/Selenium, Playwright, axe-core y K6 quedaron omitidas en ese build.

El build #6 confirmó que el cambio anterior resolvió la instalación de Playwright, pero el paso de preparación volvió a fallar en el empaquetado Maven: se llamó al wrapper desde la raíz y Maven no encontró el `pom.xml`. El script ahora cambia a `backend` antes de empaquetar. En ese build tampoco se ejecutaron las suites de QA; TestLink recibió nuevamente solo los seis resultados automatizados de Maven.

El aviso `No test report files were found` correspondía a los reportes JUnit de las suites QA omitidas, no a los reportes Maven, que sí fueron archivados. Se ajustó el post-proceso para que avise con claridad y no muestre ese mensaje genérico cuando no hubo XML de QA. El aviso `[Checks API] No suitable checks publisher found` es informativo: Jenkins no tiene un publicador de checks conectado; no es la causa del fallo de Maven ni de preparación.

Como antecedente separado, el build #3 reportó 20 de 21 pruebas Maven aprobadas y un fallo funcional: al intentar agregar cantidad cero, el sistema respondió `201` cuando se esperaba `400`. Si vuelve a aparecer, déjalo visible como defecto del backend; no se modifica código de aplicación como parte de esta ejecución de QA.

## 5. Confirmar los resultados en TestLink

1. Abre el proyecto **Dulce Miel** y el plan **Plan de pruebas - Dulce Miel**.
2. En **Test Execution / Ejecución de pruebas**, selecciona el build con el número de la corrida nueva de Jenkins.
3. Confirma que aparezcan los casos automatizados publicados y sus estados. Los casos manuales de teclado o lector de pantalla no se ejecutan ni se actualizan desde Jenkins.
4. Compara los resultados con el `current-run.json` de esa ejecución, disponible entre los artefactos del build. Revisa también los reportes JUnit, Newman, Behave, Playwright, axe-core y K6 que correspondan.
5. Si Jenkins muestra un error de publicación, conserva los resultados de pruebas y el log de TestLink; no repitas el envío a ciegas. Revisa la etapa de publicación y que el ID `testlink-devkey` pertenezca a la misma instancia.

## 6. Qué hacer al terminar

Guarda el número del build, su estado final, los casos automatizados publicados y los artefactos relevantes para el informe. El estado general de Jenkins puede ser fallido y aun así contener resultados válidos de las otras suites: no marques el conjunto como aprobado si alguna prueba automatizada quedó fallida.

Si no aparece **Build with Parameters**, verifica que Jenkins haya cargado la definición del `Jenkinsfile` de `main`; no vuelvas a crear el trabajo ni a copiar manualmente los casos de TestLink.
