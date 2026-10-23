package com.dulcemiel.backend.controller;

import com.dulcemiel.backend.model.AuthUser;
import com.dulcemiel.backend.service.AuthSupport;
import com.dulcemiel.backend.service.ImageUrlService;
import com.dulcemiel.backend.service.ResponseService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.JdbcTemplate;

import java.util.HashMap;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

class PedidosControllerAuditTest {
    JdbcTemplate jdbc = mock(JdbcTemplate.class);
    AuthSupport auth = mock(AuthSupport.class);
    PedidosController controller = new PedidosController(jdbc, auth, mock(ImageUrlService.class), new ResponseService());

    @BeforeEach void auth() {
        when(auth.user("cliente")).thenReturn(new AuthUser(1, "c@x.co", "usuario"));
        when(auth.admin("admin")).thenReturn(new AuthUser(2, "a@x.co", "admin"));
    }

    private Map<String, Object> delivery(String phone, String reference) {
        Map<String, Object> body = new HashMap<>(Map.of("contacto_nombre", "Ana", "contacto_telefono", phone,
                "direccion_entrega", "Calle 1", "distrito", "Centro"));
        if (reference != null) body.put("referencia", reference);
        return body;
    }

    @Test void telefonoDeCincoCaracteresSeRechazaAntesDeConsultarCarrito() {
        assertEquals(HttpStatus.BAD_REQUEST, controller.create("cliente", delivery("12345", null)).getStatusCode());
        verifyNoInteractions(jdbc);
    }

    @Test void telefonoDeSeisYVeinteCaracteresPasaValidacion() {
        assertEquals(HttpStatus.BAD_REQUEST, controller.create("cliente", delivery("123456", null)).getStatusCode());
        assertEquals(HttpStatus.BAD_REQUEST, controller.create("cliente", delivery("1".repeat(20), null)).getStatusCode());
        verify(jdbc, times(2)).queryForList(startsWith("SELECT c.id"), eq(1));
    }

    @Test void telefonoDeVeintiunCaracteresYReferencia301SeRechazan() {
        assertEquals(HttpStatus.BAD_REQUEST, controller.create("cliente", delivery("1".repeat(21), null)).getStatusCode());
        assertEquals(HttpStatus.BAD_REQUEST, controller.create("cliente", delivery("123456", "x".repeat(301))).getStatusCode());
        verifyNoInteractions(jdbc);
    }

    @Test void referencia300PasaValidacionPeroCarritoVacioImpidePedido() {
        assertEquals(HttpStatus.BAD_REQUEST, controller.create("cliente", delivery("123456", "x".repeat(300))).getStatusCode());
        verify(jdbc).queryForList(startsWith("SELECT c.id"), eq(1));
        verify(jdbc, never()).update(anyString(), any(Object[].class));
    }

    @Test void estadosValidosEInvalidos() {
        when(jdbc.update(startsWith("UPDATE pedidos"), eq("enviado"), eq(9))).thenReturn(1);
        assertEquals(HttpStatus.OK, controller.updateStatus("admin", 9, Map.of("estado", "enviado")).getStatusCode());
        assertEquals(HttpStatus.BAD_REQUEST, controller.updateStatus("admin", 9, Map.of("estado", "otro")).getStatusCode());
        assertEquals(HttpStatus.FORBIDDEN, controller.updateStatus("cliente", 9, Map.of("estado", "enviado")).getStatusCode());
        verify(jdbc, times(1)).update(startsWith("UPDATE pedidos"), eq("enviado"), eq(9));
    }
}
