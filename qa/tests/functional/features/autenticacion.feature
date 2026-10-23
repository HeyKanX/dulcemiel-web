# language: es
# Fuente: Anexo C, Tabla C2 del informe. Datos solo en SQL aislado.
Característica: Registro e inicio de sesión de Dulce Miel

  @TC-F-001 @CA01 @HU01 @writes
  Escenario: TC-F-001 / CA01 - registrar una cuenta nueva
    Dado que el visitante abre el registro
    Cuando registra una cuenta sintética nueva
    Entonces ve la confirmación de registro

  @TC-F-002 @CA02 @HU01 @writes
  Escenario: TC-F-002 / CA02 - rechazar un correo duplicado
    Dado que existe una cuenta sintética para la prueba
    Cuando intenta registrar de nuevo el mismo correo
    Entonces ve un error de correo duplicado y conserva el nombre ingresado

  @TC-F-004 @CA04 @HU02
  Escenario: TC-F-004 / CA04 - rechazar credenciales incorrectas
    Dado que el visitante abre el inicio de sesión
    Cuando introduce credenciales sintéticas incorrectas
    Entonces el acceso se rechaza sin mostrar datos sensibles
