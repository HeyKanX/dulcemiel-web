USE [DulceMielBD];
GO
-- Datos exclusivamente sintéticos para el criterio 5.
INSERT INTO dbo.productos (nombre, descripcion, precio, stock, categoria)
VALUES (N'Miel QA', N'Miel de prueba para la auditoría', 12.50, 5, N'Alimentos');
GO
-- La cuenta administrativa es sintética y existe únicamente en el SQL de auditoría.
INSERT INTO dbo.usuarios (nombre, email, password, rol)
VALUES (N'Administrador QA', N'qa_admin@example.test', N'$2b$10$FNN4VY1QA1oKUhazZDJDMOY8KfCXfErE9VNx.NETGZf53k87RG2Me', N'admin');
GO
