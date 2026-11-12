package com.dulcemiel.backend.controller;

import com.dulcemiel.backend.service.JwtService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.web.servlet.MockMvc;
import org.testcontainers.mssqlserver.MSSQLServerContainer;
import org.testcontainers.utility.DockerImageName;
import org.testcontainers.utility.MountableFile;

import java.nio.file.Path;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/** Recorridos de integración vinculados parcialmente a TC-F-001, TC-F-003, TC-F-009, TC-F-012, TC-F-013, TC-F-014 y TC-F-018. */
@SpringBootTest
@AutoConfigureMockMvc
class ApiSqlServerIntegrationTest {
    private static final MSSQLServerContainer SQL = new MSSQLServerContainer(DockerImageName.parse("mcr.microsoft.com/mssql/server:2022-latest"))
            .acceptLicense();

    static {
        SQL.start();
        SQL.copyFileToContainer(MountableFile.forHostPath(Path.of("database/schema.sql").toAbsolutePath()), "/tmp/schema.sql");
        try {
            var result = SQL.execInContainer("/opt/mssql-tools18/bin/sqlcmd", "-S", "localhost", "-U", "sa", "-P", SQL.getPassword(), "-C", "-b", "-i", "/tmp/schema.sql");
            if (result.getExitCode() != 0) throw new IllegalStateException("Esquema SQL aislado: " + result.getStdout() + result.getStderr());
        } catch (Exception e) {
            throw new ExceptionInInitializerError(e);
        }
    }

    @DynamicPropertySource
    static void db(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", () -> SQL.getJdbcUrl() + ";databaseName=DulceMielBD;encrypt=true;trustServerCertificate=true");
        registry.add("spring.datasource.username", SQL::getUsername);
        registry.add("spring.datasource.password", SQL::getPassword);
    }

    @Autowired MockMvc mvc;
    @Autowired JdbcTemplate jdbc;
    @Autowired JwtService jwt;

    @BeforeEach void clean() {
        jdbc.update("DELETE FROM detalles_pedido");
        jdbc.update("DELETE FROM pedidos");
        jdbc.update("DELETE FROM carrito");
        jdbc.update("DELETE FROM productos");
        jdbc.update("DELETE FROM usuarios");
    }

    private int user() {
        jdbc.update("INSERT INTO usuarios(nombre,email,password,rol) VALUES (?,?,?,?)", "Cliente", "cliente@audit.co", "hash", "usuario");
        return jdbc.queryForObject("SELECT id FROM usuarios WHERE email=?", Integer.class, "cliente@audit.co");
    }

    private int product(int stock) {
        jdbc.update("INSERT INTO productos(nombre,precio,stock) VALUES (?,?,?)", "Torta", 10, stock);
        return jdbc.queryForObject("SELECT id FROM productos WHERE nombre=?", Integer.class, "Torta");
    }

    @Test void registroYLoginConPersistenciaReal() throws Exception {
        mvc.perform(post("/api/auth/register").contentType("application/json")
                .content("{\"nombre\":\"Ana\",\"email\":\"ana@audit.co\",\"password\":\"clave123\",\"passwordConfirm\":\"clave123\"}"))
                .andExpect(status().isCreated());
        assertEquals(1, jdbc.queryForObject("SELECT COUNT(*) FROM usuarios WHERE email='ana@audit.co'", Integer.class));
        mvc.perform(post("/api/auth/login").contentType("application/json")
                .content("{\"email\":\"ana@audit.co\",\"password\":\"clave123\"}"))
                .andExpect(status().isOk()).andExpect(jsonPath("$.token").isNotEmpty());
    }

    @Test void clienteNoAccedeListadoAdministrativo() throws Exception {
        int id = user();
        mvc.perform(get("/api/pedidos/admin/todos").header("Authorization", "Bearer " + jwt.generateToken(id, "cliente@audit.co", "usuario")))
                .andExpect(status().isForbidden());
        assertEquals(0, jdbc.queryForObject("SELECT COUNT(*) FROM pedidos", Integer.class));
    }

    @Test void pedidoCreaDetalleReduceStockYVaciaCarrito() throws Exception {
        int id = user();
        int product = product(5);
        jdbc.update("INSERT INTO carrito(usuario_id,producto_id,cantidad,precio_unitario) VALUES (?,?,?,?)", id, product, 2, 10);
        String token = "Bearer " + jwt.generateToken(id, "cliente@audit.co", "usuario");
        mvc.perform(post("/api/pedidos").header("Authorization", token).contentType("application/json")
                .content("{\"contacto_nombre\":\"Ana\",\"contacto_telefono\":\"123456\",\"direccion_entrega\":\"Calle 1\",\"distrito\":\"Centro\"}"))
                .andExpect(status().isCreated());
        assertEquals(1, jdbc.queryForObject("SELECT COUNT(*) FROM pedidos", Integer.class));
        assertEquals(2, jdbc.queryForObject("SELECT cantidad FROM detalles_pedido", Integer.class));
        assertEquals(3, jdbc.queryForObject("SELECT stock FROM productos WHERE id=?", Integer.class, product));
        assertEquals(0, jdbc.queryForObject("SELECT COUNT(*) FROM carrito", Integer.class));
    }

    @Test void pedidoConTelefonoInvalidoNoCambiaDatos() throws Exception {
        int id = user();
        int product = product(5);
        jdbc.update("INSERT INTO carrito(usuario_id,producto_id,cantidad,precio_unitario) VALUES (?,?,?,?)", id, product, 2, 10);
        mvc.perform(post("/api/pedidos").header("Authorization", "Bearer " + jwt.generateToken(id, "cliente@audit.co", "usuario"))
                .contentType("application/json")
                .content("{\"contacto_nombre\":\"Ana\",\"contacto_telefono\":\"12345\",\"direccion_entrega\":\"Calle 1\",\"distrito\":\"Centro\"}"))
                .andExpect(status().isBadRequest());
        assertEquals(0, jdbc.queryForObject("SELECT COUNT(*) FROM pedidos", Integer.class));
        assertEquals(5, jdbc.queryForObject("SELECT stock FROM productos WHERE id=?", Integer.class, product));
        assertEquals(1, jdbc.queryForObject("SELECT COUNT(*) FROM carrito", Integer.class));
    }

    @Test void carritoAgregarYRechazarCantidadSuperiorAlStock() throws Exception {
        int id = user();
        int product = product(5);
        String token = "Bearer " + jwt.generateToken(id, "cliente@audit.co", "usuario");
        mvc.perform(post("/api/carrito/agregar").header("Authorization", token).contentType("application/json")
                .content("{\"producto_id\":" + product + ",\"cantidad\":5}"))
                .andExpect(status().isCreated());
        assertEquals(5, jdbc.queryForObject("SELECT cantidad FROM carrito WHERE usuario_id=?", Integer.class, id));
        mvc.perform(post("/api/carrito/agregar").header("Authorization", token).contentType("application/json")
                .content("{\"producto_id\":" + product + ",\"cantidad\":6}"))
                .andExpect(status().isBadRequest());
        assertEquals(5, jdbc.queryForObject("SELECT cantidad FROM carrito WHERE usuario_id=?", Integer.class, id));
    }
}
