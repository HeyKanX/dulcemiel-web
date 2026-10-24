package com.dulcemiel.backend.controller;

import com.dulcemiel.backend.model.AuthUser;
import com.dulcemiel.backend.service.AuthSupport;
import com.dulcemiel.backend.service.ImageUrlService;
import com.dulcemiel.backend.service.ResponseService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.JdbcTemplate;

import java.math.BigDecimal;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

/** Verificaciones unitarias vinculadas parcialmente a TC-F-009, TC-F-010 y TC-F-012. */
class CarritoControllerAuditTest {
    private JdbcTemplate jdbc;
    private AuthSupport auth;
    private CarritoController controller;

    @BeforeEach void setup() {
        jdbc = mock(JdbcTemplate.class);
        auth = mock(AuthSupport.class);
        controller = new CarritoController(jdbc, auth, mock(ImageUrlService.class), new ResponseService());
        when(auth.user("Bearer cliente")).thenReturn(new AuthUser(1, "c@x.co", "cliente"));
    }

    @Test void sinTokenNoConsultaNiModificaDatos() {
        assertEquals(HttpStatus.UNAUTHORIZED, controller.add(null, Map.of("producto_id", 9, "cantidad", 1)).getStatusCode());
        verifyNoInteractions(jdbc);
    }

    @Test void cantidadIgualAlStockSePermite() {
        when(jdbc.queryForList(startsWith("SELECT precio"), eq(9))).thenReturn(java.util.List.of(Map.of("precio", BigDecimal.TEN, "stock", 5)));
        when(jdbc.queryForList(startsWith("SELECT id, cantidad"), eq(1), eq(9))).thenReturn(java.util.List.of());
        assertEquals(HttpStatus.CREATED, controller.add("Bearer cliente", Map.of("producto_id", 9, "cantidad", 5)).getStatusCode());
        verify(jdbc).update(startsWith("INSERT INTO carrito"), eq(1), eq(9), eq(5), eq(BigDecimal.TEN));
    }

    @Test void cantidadMayorQueStockSeRechaza() {
        when(jdbc.queryForList(startsWith("SELECT precio"), eq(9))).thenReturn(java.util.List.of(Map.of("precio", BigDecimal.TEN, "stock", 5)));
        assertEquals(HttpStatus.BAD_REQUEST, controller.add("Bearer cliente", Map.of("producto_id", 9, "cantidad", 6)).getStatusCode());
        verify(jdbc, never()).update(anyString(), any(Object[].class));
    }

    @Test void acumuladoMayorQueStockDebeRechazarseSinActualizar_TC_F_012() {
        when(jdbc.queryForList(startsWith("SELECT precio"), eq(9))).thenReturn(java.util.List.of(Map.of("precio", BigDecimal.TEN, "stock", 5)));
        when(jdbc.queryForList(startsWith("SELECT id, cantidad"), eq(1), eq(9))).thenReturn(java.util.List.of(Map.of("id", 13, "cantidad", 4)));
        assertEquals(HttpStatus.BAD_REQUEST, controller.add("Bearer cliente", Map.of("producto_id", 9, "cantidad", 2)).getStatusCode());
        verify(jdbc, never()).update(startsWith("UPDATE carrito"), anyInt(), anyInt());
    }

    @Test void cantidadCeroDebeRechazarseAntesDeEscribir() {
        when(jdbc.queryForList(startsWith("SELECT precio"), eq(9))).thenReturn(java.util.List.of(Map.of("precio", BigDecimal.TEN, "stock", 5)));
        when(jdbc.queryForList(startsWith("SELECT id, cantidad"), eq(1), eq(9))).thenReturn(java.util.List.of());
        assertEquals(HttpStatus.BAD_REQUEST, controller.add("Bearer cliente", Map.of("producto_id", 9, "cantidad", 0)).getStatusCode());
        verify(jdbc, never()).update(startsWith("INSERT INTO carrito"), any(), any(), any(), any());
    }
}
