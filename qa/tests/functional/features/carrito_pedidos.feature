Feature: Compra y permisos del cliente

  @TC-F-009 @CA09 @HU05 @writes
  Scenario: TC-F-009 / CA09 - agregar producto desde el catálogo
    Given que un cliente sintético inicia sesión
    When agrega Miel QA desde el catálogo
    Then el carrito muestra una unidad y total correcto

  @TC-F-014 @CA13 @HU06 @writes
  Scenario: TC-F-014 / CA13 - impedir pedido con carrito vacío
    Given que un cliente sintético inicia sesión
    When abre el checkout sin productos
    Then no puede confirmar un pedido

  @TC-F-018 @CA17 @HU08 @writes
  Scenario: TC-F-018 / CA17 - cliente no accede al panel administrativo
    Given que un cliente sintético inicia sesión
    When solicita directamente la administración
    Then es redirigido fuera del panel

  @TC-NF-INT-002 @CNF-INT-02 @RNF06 @writes
  Scenario: TC-NF-INT-002 / CNF-INT-02 - conservar catálogo al recargar sesión activa
    Given que un cliente sintético inicia sesión
    When recarga el catálogo con la sesión activa
    Then el catálogo continúa mostrando Miel QA
