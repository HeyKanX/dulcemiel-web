package com.dulcemiel.backend.controller;

import com.dulcemiel.backend.model.AuthUser;
import com.dulcemiel.backend.service.AuthSupport;
import com.dulcemiel.backend.service.ImageUrlService;
import com.dulcemiel.backend.service.ResponseService;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.JdbcTemplate;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

class CarritoCa11TddTest {
    @Test void stockCincoConCuatroEnCarritoRechazaAgregarDosSinActualizar() {
        JdbcTemplate jdbc = mock(JdbcTemplate.class);
        AuthSupport auth = mock(AuthSupport.class);
        when(auth.user("Bearer cliente")).thenReturn(new AuthUser(1, "c@x.co", "cliente"));
        when(jdbc.queryForList(startsWith("SELECT precio"), eq(9))).thenReturn(List.of(Map.of("precio", BigDecimal.TEN, "stock", 5)));
        when(jdbc.queryForList(startsWith("SELECT id, cantidad"), eq(1), eq(9))).thenReturn(List.of(Map.of("id", 13, "cantidad", 4)));
        var controller = new CarritoController(jdbc, auth, mock(ImageUrlService.class), new ResponseService());

        assertEquals(HttpStatus.BAD_REQUEST, controller.add("Bearer cliente", Map.of("producto_id", 9, "cantidad", 2)).getStatusCode());
        verify(jdbc, never()).update(startsWith("UPDATE carrito"), anyInt(), anyInt());
    }
}
