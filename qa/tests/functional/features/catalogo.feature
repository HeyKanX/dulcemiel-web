# Fuente: Anexo C, Tabla C2 del informe. Producto de prueba con stock 5.
Feature: Consulta pública del catálogo

  @TC-F-005 @CA05 @HU03
  Scenario: TC-F-005 / CA05 - mostrar datos esenciales del producto publicado
    Given que el visitante abre el catálogo
    Then encuentra el producto sintético con nombre precio y disponibilidad

  @TC-F-007 @CA07 @HU04
  Scenario: TC-F-007 / CA07 - mostrar detalle de un producto existente
    Given que el visitante abre el catálogo
    When abre el detalle del producto sintético
    Then ve su descripción precio stock y categoría

  @TC-F-008 @CA08 @HU04
  Scenario: TC-F-008 / CA08 - informar producto inexistente
    Given que el visitante abre un detalle inexistente
    Then encuentra un mensaje comprensible y un enlace de regreso
