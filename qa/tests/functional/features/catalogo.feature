# language: es
# Fuente: Anexo C, Tabla C2 del informe. Producto de prueba con stock 5.
Característica: Consulta pública del catálogo

  @TC-F-005 @CA05 @HU03
  Escenario: TC-F-005 / CA05 - mostrar datos esenciales del producto publicado
    Dado que el visitante abre el catálogo
    Entonces encuentra el producto sintético con nombre precio y disponibilidad

  @TC-F-007 @CA07 @HU04
  Escenario: TC-F-007 / CA07 - mostrar detalle de un producto existente
    Dado que el visitante abre el catálogo
    Cuando abre el detalle del producto sintético
    Entonces ve su descripción precio stock y categoría

  @TC-F-008 @CA08 @HU04
  Escenario: TC-F-008 / CA08 - informar producto inexistente
    Dado que el visitante abre un detalle inexistente
    Entonces encuentra un mensaje comprensible y un enlace de regreso
