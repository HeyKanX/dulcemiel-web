# Fuente: Anexo C, Tabla C2 del informe. Datos solo en SQL aislado.
Feature: Registro e inicio de sesión de Dulce Miel

  @TC-F-001 @CA01 @HU01 @writes
  Scenario: TC-F-001 / CA01 - registrar una cuenta nueva
    Given que el visitante abre el registro
    When registra una cuenta sintética nueva
    Then ve la confirmación de registro

  @TC-F-002 @CA02 @HU01 @writes
  Scenario: TC-F-002 / CA02 - rechazar un correo duplicado
    Given que existe una cuenta sintética para la prueba
    When intenta registrar de nuevo el mismo correo
    Then ve un error de correo duplicado y conserva el nombre ingresado

  @TC-F-004 @CA04 @HU02
  Scenario: TC-F-004 / CA04 - rechazar credenciales incorrectas
    Given que el visitante abre el inicio de sesión
    When introduce credenciales sintéticas incorrectas
    Then el acceso se rechaza sin mostrar datos sensibles
