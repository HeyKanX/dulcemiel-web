IF DB_ID(N'DulceMielBD') IS NULL
BEGIN
  CREATE DATABASE [DulceMielBD];
END
GO

USE [DulceMielBD];
GO

IF OBJECT_ID(N'dbo.sp_dashboard_resumen', N'P') IS NOT NULL DROP PROCEDURE dbo.sp_dashboard_resumen;
IF OBJECT_ID(N'dbo.sp_actualizar_estado_pedido', N'P') IS NOT NULL DROP PROCEDURE dbo.sp_actualizar_estado_pedido;
IF OBJECT_ID(N'dbo.sp_crear_pedido', N'P') IS NOT NULL DROP PROCEDURE dbo.sp_crear_pedido;
IF OBJECT_ID(N'dbo.sp_guardar_producto', N'P') IS NOT NULL DROP PROCEDURE dbo.sp_guardar_producto;
IF OBJECT_ID(N'dbo.sp_guardar_promocion', N'P') IS NOT NULL DROP PROCEDURE dbo.sp_guardar_promocion;
GO

IF OBJECT_ID(N'dbo.detalles_pedido', N'U') IS NOT NULL DROP TABLE dbo.detalles_pedido;
IF OBJECT_ID(N'dbo.pedidos', N'U') IS NOT NULL DROP TABLE dbo.pedidos;
IF OBJECT_ID(N'dbo.carrito', N'U') IS NOT NULL DROP TABLE dbo.carrito;
IF OBJECT_ID(N'dbo.promociones', N'U') IS NOT NULL DROP TABLE dbo.promociones;
IF OBJECT_ID(N'dbo.carrusel_inicio', N'U') IS NOT NULL DROP TABLE dbo.carrusel_inicio;
IF OBJECT_ID(N'dbo.productos', N'U') IS NOT NULL DROP TABLE dbo.productos;
IF OBJECT_ID(N'dbo.configuracion_sitio', N'U') IS NOT NULL DROP TABLE dbo.configuracion_sitio;
IF OBJECT_ID(N'dbo.usuarios', N'U') IS NOT NULL DROP TABLE dbo.usuarios;
GO

CREATE TABLE dbo.usuarios (
  id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
  nombre NVARCHAR(100) NOT NULL,
  email NVARCHAR(120) NOT NULL UNIQUE,
  password NVARCHAR(255) NOT NULL,
  rol NVARCHAR(20) NOT NULL CONSTRAINT DF_usuarios_rol DEFAULT N'usuario',
  estado NVARCHAR(20) NOT NULL CONSTRAINT DF_usuarios_estado DEFAULT N'activo',
  fecha_creacion DATETIME2(0) NOT NULL CONSTRAINT DF_usuarios_fecha_creacion DEFAULT SYSUTCDATETIME(),
  fecha_actualizacion DATETIME2(0) NOT NULL CONSTRAINT DF_usuarios_fecha_actualizacion DEFAULT SYSUTCDATETIME(),
  CONSTRAINT CK_usuarios_rol CHECK (rol IN (N'admin', N'empleado', N'usuario')),
  CONSTRAINT CK_usuarios_estado CHECK (estado IN (N'activo', N'inactivo'))
);
GO

CREATE TABLE dbo.configuracion_sitio (
  id INT NOT NULL PRIMARY KEY CONSTRAINT DF_configuracion_sitio_id DEFAULT 1,
  nombre_empresa NVARCHAR(120) NOT NULL,
  descripcion_inicio NVARCHAR(MAX) NOT NULL,
  mision NVARCHAR(MAX) NOT NULL,
  vision NVARCHAR(MAX) NOT NULL,
  logo_data VARBINARY(MAX) NULL,
  logo_mime NVARCHAR(80) NULL,
  logo_nombre NVARCHAR(255) NULL,
  fecha_actualizacion DATETIME2(0) NOT NULL CONSTRAINT DF_configuracion_fecha DEFAULT SYSUTCDATETIME(),
  CONSTRAINT CK_configuracion_unica CHECK (id = 1)
);
GO

CREATE TABLE dbo.productos (
  id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
  nombre NVARCHAR(150) NOT NULL,
  descripcion NVARCHAR(MAX) NULL,
  precio DECIMAL(10, 2) NOT NULL,
  stock INT NOT NULL CONSTRAINT DF_productos_stock DEFAULT 0,
  imagen_data VARBINARY(MAX) NULL,
  imagen_mime NVARCHAR(80) NULL,
  imagen_nombre NVARCHAR(255) NULL,
  categoria NVARCHAR(100) NULL,
  estado NVARCHAR(20) NOT NULL CONSTRAINT DF_productos_estado DEFAULT N'disponible',
  fecha_creacion DATETIME2(0) NOT NULL CONSTRAINT DF_productos_fecha_creacion DEFAULT SYSUTCDATETIME(),
  fecha_actualizacion DATETIME2(0) NOT NULL CONSTRAINT DF_productos_fecha_actualizacion DEFAULT SYSUTCDATETIME(),
  CONSTRAINT CK_productos_precio CHECK (precio >= 0),
  CONSTRAINT CK_productos_stock CHECK (stock >= 0),
  CONSTRAINT CK_productos_estado CHECK (estado IN (N'disponible', N'agotado', N'discontinuado'))
);
GO

CREATE TABLE dbo.carrusel_inicio (
  id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
  titulo NVARCHAR(140) NOT NULL,
  descripcion NVARCHAR(500) NULL,
  imagen_data VARBINARY(MAX) NOT NULL,
  imagen_mime NVARCHAR(80) NOT NULL,
  imagen_nombre NVARCHAR(255) NULL,
  orden INT NOT NULL CONSTRAINT DF_carrusel_orden DEFAULT 0,
  activo BIT NOT NULL CONSTRAINT DF_carrusel_activo DEFAULT 1,
  fecha_creacion DATETIME2(0) NOT NULL CONSTRAINT DF_carrusel_fecha DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE dbo.promociones (
  id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
  titulo NVARCHAR(140) NOT NULL,
  descripcion NVARCHAR(500) NULL,
  descuento_porcentaje DECIMAL(5, 2) NOT NULL,
  fecha_inicio DATE NOT NULL,
  fecha_fin DATE NULL,
  activo BIT NOT NULL CONSTRAINT DF_promociones_activo DEFAULT 1,
  fecha_creacion DATETIME2(0) NOT NULL CONSTRAINT DF_promociones_fecha DEFAULT SYSUTCDATETIME(),
  CONSTRAINT CK_promociones_descuento CHECK (descuento_porcentaje >= 0 AND descuento_porcentaje <= 100)
);
GO

CREATE TABLE dbo.carrito (
  id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
  usuario_id INT NOT NULL,
  producto_id INT NOT NULL,
  cantidad INT NOT NULL CONSTRAINT DF_carrito_cantidad DEFAULT 1,
  precio_unitario DECIMAL(10, 2) NULL,
  fecha_agregado DATETIME2(0) NOT NULL CONSTRAINT DF_carrito_fecha_agregado DEFAULT SYSUTCDATETIME(),
  CONSTRAINT CK_carrito_cantidad CHECK (cantidad > 0),
  CONSTRAINT FK_carrito_usuarios FOREIGN KEY (usuario_id) REFERENCES dbo.usuarios(id) ON DELETE CASCADE,
  CONSTRAINT FK_carrito_productos FOREIGN KEY (producto_id) REFERENCES dbo.productos(id) ON DELETE CASCADE,
  CONSTRAINT UQ_carrito_usuario_producto UNIQUE (usuario_id, producto_id)
);
GO

CREATE TABLE dbo.pedidos (
  id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
  usuario_id INT NOT NULL,
  numero_pedido NVARCHAR(50) NOT NULL UNIQUE,
  total DECIMAL(10, 2) NOT NULL,
  estado NVARCHAR(20) NOT NULL CONSTRAINT DF_pedidos_estado DEFAULT N'pendiente',
  contacto_nombre NVARCHAR(120) NOT NULL,
  contacto_telefono NVARCHAR(30) NOT NULL,
  contacto_email NVARCHAR(120) NULL,
  direccion_entrega NVARCHAR(250) NOT NULL,
  distrito NVARCHAR(100) NOT NULL,
  referencia NVARCHAR(300) NULL,
  notas NVARCHAR(500) NULL,
  fecha_pedido DATETIME2(0) NOT NULL CONSTRAINT DF_pedidos_fecha_pedido DEFAULT SYSUTCDATETIME(),
  fecha_entrega DATETIME2(0) NULL,
  CONSTRAINT CK_pedidos_total CHECK (total >= 0),
  CONSTRAINT CK_pedidos_estado CHECK (estado IN (N'pendiente', N'procesando', N'enviado', N'entregado', N'cancelado')),
  CONSTRAINT FK_pedidos_usuarios FOREIGN KEY (usuario_id) REFERENCES dbo.usuarios(id) ON DELETE CASCADE
);
GO

CREATE TABLE dbo.detalles_pedido (
  id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
  pedido_id INT NOT NULL,
  producto_id INT NOT NULL,
  cantidad INT NOT NULL,
  precio_unitario DECIMAL(10, 2) NOT NULL,
  subtotal DECIMAL(10, 2) NOT NULL,
  CONSTRAINT CK_detalles_pedido_cantidad CHECK (cantidad > 0),
  CONSTRAINT CK_detalles_pedido_precio CHECK (precio_unitario >= 0),
  CONSTRAINT CK_detalles_pedido_subtotal CHECK (subtotal >= 0),
  CONSTRAINT FK_detalles_pedido_pedidos FOREIGN KEY (pedido_id) REFERENCES dbo.pedidos(id) ON DELETE CASCADE,
  CONSTRAINT FK_detalles_pedido_productos FOREIGN KEY (producto_id) REFERENCES dbo.productos(id)
);
GO

CREATE TRIGGER dbo.trg_usuarios_fecha_actualizacion ON dbo.usuarios AFTER UPDATE AS
BEGIN
  SET NOCOUNT ON;
  UPDATE u SET fecha_actualizacion = SYSUTCDATETIME()
  FROM dbo.usuarios u INNER JOIN inserted i ON u.id = i.id;
END;
GO

CREATE TRIGGER dbo.trg_productos_fecha_actualizacion ON dbo.productos AFTER UPDATE AS
BEGIN
  SET NOCOUNT ON;
  UPDATE p SET fecha_actualizacion = SYSUTCDATETIME()
  FROM dbo.productos p INNER JOIN inserted i ON p.id = i.id;
END;
GO

CREATE TRIGGER dbo.trg_configuracion_fecha_actualizacion ON dbo.configuracion_sitio AFTER UPDATE AS
BEGIN
  SET NOCOUNT ON;
  UPDATE c SET fecha_actualizacion = SYSUTCDATETIME()
  FROM dbo.configuracion_sitio c INNER JOIN inserted i ON c.id = i.id;
END;
GO

INSERT INTO dbo.usuarios (nombre, email, password, rol) VALUES
(N'Administrador DulceMiel', N'admin@dulcemiel.local', N'$2b$10$yxQo2iUzSCbFRaPYkf7z.uDGpYa4dZt/ynNF4PdLAYSLFuZ3i1Xcq', N'admin'),
(N'Empleado DulceMiel', N'empleado@dulcemiel.local', N'$2b$10$yxQo2iUzSCbFRaPYkf7z.uDGpYa4dZt/ynNF4PdLAYSLFuZ3i1Xcq', N'empleado'),
(N'Cliente de prueba', N'cliente@dulcemiel.local', N'$2b$10$yxQo2iUzSCbFRaPYkf7z.uDGpYa4dZt/ynNF4PdLAYSLFuZ3i1Xcq', N'usuario');

INSERT INTO dbo.configuracion_sitio (id, nombre_empresa, descripcion_inicio, mision, vision) VALUES
(1, N'DulceMiel', N'Miel pura, derivados apicolas y productos naturales trabajados con cuidado local.', N'Producir y comercializar miel y derivados apicolas de alta calidad, cuidando las colmenas, el entorno y la confianza de cada cliente.', N'Ser una apicola referente por trazabilidad, sabor natural y una experiencia digital clara para clientes y administradores.');

INSERT INTO dbo.productos (nombre, descripcion, precio, stock, categoria) VALUES
(N'Miel multifloral 500g', N'Miel natural de cosecha local, ideal para desayunos, infusiones y reposteria.', 28.00, 35, N'Miel'),
(N'Miel con panal', N'Frasco artesanal con trozos de panal comestible.', 42.00, 16, N'Especiales'),
(N'Propoleo natural', N'Extracto de propoleo para bienestar diario.', 24.50, 25, N'Derivados'),
(N'Polen granulado', N'Polen seleccionado para batidos, yogures y recetas naturales.', 31.90, 18, N'Derivados'),
(N'Pack regalo DulceMiel', N'Seleccion de mieles y derivados en presentacion para regalo.', 79.00, 10, N'Kits');

INSERT INTO dbo.promociones (titulo, descripcion, descuento_porcentaje, fecha_inicio, fecha_fin, activo) VALUES
(N'Pack natural', N'Promocion para packs regalo y productos de temporada.', 12.00, CONVERT(date, GETDATE()), NULL, 1);
GO

CREATE INDEX idx_carrito_usuario ON dbo.carrito(usuario_id);
CREATE INDEX idx_pedidos_usuario ON dbo.pedidos(usuario_id);
CREATE INDEX idx_detalles_pedido ON dbo.detalles_pedido(pedido_id);
CREATE INDEX idx_productos_estado ON dbo.productos(estado);
GO

CREATE PROCEDURE dbo.sp_guardar_producto
  @id INT = NULL,
  @nombre NVARCHAR(150),
  @descripcion NVARCHAR(MAX) = NULL,
  @precio DECIMAL(10,2),
  @stock INT,
  @categoria NVARCHAR(100) = NULL,
  @estado NVARCHAR(20) = N'disponible',
  @imagen_data VARBINARY(MAX) = NULL,
  @imagen_mime NVARCHAR(80) = NULL,
  @imagen_nombre NVARCHAR(255) = NULL
AS
BEGIN
  SET NOCOUNT ON;

  IF @id IS NULL
  BEGIN
    INSERT INTO dbo.productos (nombre, descripcion, precio, stock, categoria, estado, imagen_data, imagen_mime, imagen_nombre)
    VALUES (@nombre, @descripcion, @precio, @stock, @categoria, @estado, @imagen_data, @imagen_mime, @imagen_nombre);
    SELECT CAST(SCOPE_IDENTITY() AS INT) AS insertId;
    RETURN;
  END

  UPDATE dbo.productos
  SET nombre = @nombre,
      descripcion = @descripcion,
      precio = @precio,
      stock = @stock,
      categoria = @categoria,
      estado = @estado,
      imagen_data = COALESCE(@imagen_data, imagen_data),
      imagen_mime = COALESCE(@imagen_mime, imagen_mime),
      imagen_nombre = COALESCE(@imagen_nombre, imagen_nombre)
  WHERE id = @id;
END;
GO

CREATE PROCEDURE dbo.sp_crear_pedido
  @usuario_id INT,
  @contacto_nombre NVARCHAR(120),
  @contacto_telefono NVARCHAR(30),
  @contacto_email NVARCHAR(120) = NULL,
  @direccion_entrega NVARCHAR(250),
  @distrito NVARCHAR(100),
  @referencia NVARCHAR(300) = NULL,
  @notas NVARCHAR(500) = NULL
AS
BEGIN
  SET NOCOUNT ON;
  SET XACT_ABORT ON;

  DECLARE @pedido_id INT;
  DECLARE @total DECIMAL(10,2);
  DECLARE @numero NVARCHAR(50) = CONCAT(N'PED-', FORMAT(SYSDATETIME(), 'yyyyMMddHHmmssfff'));

  IF NOT EXISTS (SELECT 1 FROM dbo.carrito WHERE usuario_id = @usuario_id)
    THROW 50001, 'El carrito esta vacio', 1;

  IF EXISTS (
    SELECT 1
    FROM dbo.carrito c
    JOIN dbo.productos p ON p.id = c.producto_id
    WHERE c.usuario_id = @usuario_id AND p.stock < c.cantidad
  )
    THROW 50002, 'Stock insuficiente para uno o mas productos', 1;

  BEGIN TRANSACTION;

  SELECT @total = SUM(c.cantidad * ISNULL(c.precio_unitario, p.precio))
  FROM dbo.carrito c
  JOIN dbo.productos p ON p.id = c.producto_id
  WHERE c.usuario_id = @usuario_id;

  INSERT INTO dbo.pedidos (
    usuario_id, numero_pedido, total, contacto_nombre, contacto_telefono,
    contacto_email, direccion_entrega, distrito, referencia, notas
  )
  VALUES (
    @usuario_id, @numero, @total, @contacto_nombre, @contacto_telefono,
    @contacto_email, @direccion_entrega, @distrito, @referencia, @notas
  );

  SET @pedido_id = SCOPE_IDENTITY();

  INSERT INTO dbo.detalles_pedido (pedido_id, producto_id, cantidad, precio_unitario, subtotal)
  SELECT @pedido_id, c.producto_id, c.cantidad, ISNULL(c.precio_unitario, p.precio), c.cantidad * ISNULL(c.precio_unitario, p.precio)
  FROM dbo.carrito c
  JOIN dbo.productos p ON p.id = c.producto_id
  WHERE c.usuario_id = @usuario_id;

  UPDATE p
  SET p.stock = p.stock - c.cantidad,
      p.estado = CASE WHEN p.stock - c.cantidad <= 0 THEN N'agotado' ELSE p.estado END
  FROM dbo.productos p
  JOIN dbo.carrito c ON c.producto_id = p.id
  WHERE c.usuario_id = @usuario_id;

  DELETE FROM dbo.carrito WHERE usuario_id = @usuario_id;

  COMMIT TRANSACTION;

  SELECT @pedido_id AS id, @numero AS numero_pedido, @total AS total;
END;
GO

CREATE PROCEDURE dbo.sp_actualizar_estado_pedido
  @pedido_id INT,
  @estado NVARCHAR(20)
AS
BEGIN
  SET NOCOUNT ON;
  UPDATE dbo.pedidos
  SET estado = @estado,
      fecha_entrega = CASE WHEN @estado = N'entregado' THEN SYSUTCDATETIME() ELSE fecha_entrega END
  WHERE id = @pedido_id;
END;
GO

CREATE PROCEDURE dbo.sp_guardar_promocion
  @id INT = NULL,
  @titulo NVARCHAR(140),
  @descripcion NVARCHAR(500) = NULL,
  @descuento_porcentaje DECIMAL(5,2),
  @fecha_inicio DATE,
  @fecha_fin DATE = NULL,
  @activo BIT = 1
AS
BEGIN
  SET NOCOUNT ON;

  IF @id IS NULL
  BEGIN
    INSERT INTO dbo.promociones (titulo, descripcion, descuento_porcentaje, fecha_inicio, fecha_fin, activo)
    VALUES (@titulo, @descripcion, @descuento_porcentaje, @fecha_inicio, @fecha_fin, @activo);
    SELECT CAST(SCOPE_IDENTITY() AS INT) AS insertId;
    RETURN;
  END

  UPDATE dbo.promociones
  SET titulo = @titulo,
      descripcion = @descripcion,
      descuento_porcentaje = @descuento_porcentaje,
      fecha_inicio = @fecha_inicio,
      fecha_fin = @fecha_fin,
      activo = @activo
  WHERE id = @id;
END;
GO

CREATE PROCEDURE dbo.sp_dashboard_resumen
AS
BEGIN
  SET NOCOUNT ON;
  SELECT
    (SELECT COUNT(*) FROM dbo.productos) AS productos,
    (SELECT COUNT(*) FROM dbo.pedidos) AS pedidos,
    (SELECT COUNT(*) FROM dbo.usuarios WHERE rol = N'usuario') AS clientes,
    (SELECT ISNULL(SUM(total), 0) FROM dbo.pedidos WHERE estado = N'entregado') AS ventas,
    (SELECT COUNT(*) FROM dbo.pedidos WHERE estado = N'pendiente') AS pedidos_pendientes,
    (SELECT COUNT(*) FROM dbo.productos WHERE stock <= 5) AS stock_bajo;
END;
GO
