package com.dulcemiel.backend.service;

import com.dulcemiel.backend.model.AuthUser;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class JwtServiceTest {
    private static final String SECRET = "clave-de-auditoria-criterio-cuatro-2026";

    @Test void tokenValidoConservaIdentidadYRol() {
        JwtService service = new JwtService(SECRET, 60_000);
        String token = service.generateToken(7, "cliente@example.com", "cliente");
        assertEquals(new AuthUser(7, "cliente@example.com", "cliente"), service.parse("Bearer " + token));
    }

    @Test void encabezadosInvalidosNoAutentican() {
        JwtService service = new JwtService(SECRET, 60_000);
        assertNull(service.parse(null));
        assertNull(service.parse("Basic 123"));
        assertNull(service.parse("Bearer alterado"));
    }

    @Test void tokenVencidoNoAutentica() {
        JwtService service = new JwtService(SECRET, -1);
        assertNull(service.parse("Bearer " + service.generateToken(7, "cliente@example.com", "cliente")));
    }

    @Test void permisosDistinguenTresRoles() {
        JwtService service = new JwtService(SECRET, 60_000);
        AuthSupport support = new AuthSupport(service);
        String cliente = "Bearer " + service.generateToken(1, "c@x.co", "cliente");
        String empleado = "Bearer " + service.generateToken(2, "e@x.co", "empleado");
        String admin = "Bearer " + service.generateToken(3, "a@x.co", "admin");
        assertNotNull(support.user(cliente));
        assertNull(support.admin(cliente));
        assertNotNull(support.admin(empleado));
        assertNull(support.ownerAdmin(empleado));
        assertNotNull(support.ownerAdmin(admin));
    }
}
