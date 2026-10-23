# language: es
Característica: Compra y permisos del cliente

  @TC-F-009 @CA09 @HU05 @writes
  Escenario: TC-F-009 / CA09 - agregar producto desde el catálogo
    Dado que un cliente sintético inicia sesión
    Cuando agrega Miel QA desde el catálogo
    Entonces el carrito muestra una unidad y total correcto

  @TC-F-014 @CA13 @HU06 @writes
  Escenario: TC-F-014 / CA13 - impedir pedido con carrito vacío
    Dado que un cliente sintético inicia sesión
    Cuando abre el checkout sin productos
    Entonces no puede confirmar un pedido

  @TC-F-018 @CA17 @HU08 @writes
  Escenario: TC-F-018 / CA17 - cliente no accede al panel administrativo
    Dado que un cliente sintético inicia sesión
    Cuando solicita directamente la administración
    Entonces es redirigido fuera del panel

  @TC-NF-INT-002 @CNF-INT-02 @RNF06 @writes
  Escenario: TC-NF-INT-002 / CNF-INT-02 - conservar catálogo al recargar sesión activa
    Dado que un cliente sintético inicia sesión
    Cuando recarga el catálogo con la sesión activa
    Entonces el catálogo continúa mostrando Miel QA
