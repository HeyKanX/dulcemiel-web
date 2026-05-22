package com.dulcemiel.backend.controller;

import com.dulcemiel.backend.service.AuthSupport;
import com.dulcemiel.backend.service.ResponseService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/promociones")
public class PromocionesController {
    private final JdbcTemplate jdbc;
    private final AuthSupport auth;
    private final ResponseService responses;

    public PromocionesController(JdbcTemplate jdbc, AuthSupport auth, ResponseService responses) {
        this.jdbc = jdbc;
        this.auth = auth;
        this.responses = responses;
    }

    @GetMapping
    ResponseEntity<Map<String, Object>> list(@RequestHeader(value = "Authorization", required = false) String authorization) {
        if (auth.admin(authorization) == null) return responses.error(HttpStatus.FORBIDDEN, "Acceso denegado. Se requieren permisos de administrador");
        return responses.ok("success", true, "data", jdbc.queryForList(
                "SELECT id, titulo, descripcion, descuento_porcentaje, fecha_inicio, fecha_fin, activo FROM promociones ORDER BY fecha_creacion DESC"));
    }

    @PostMapping
    ResponseEntity<Map<String, Object>> create(@RequestHeader(value = "Authorization", required = false) String authorization,
                                               @RequestBody Map<String, Object> body) {
        if (auth.admin(authorization) == null) return responses.error(HttpStatus.FORBIDDEN, "Acceso denegado. Se requieren permisos de administrador");
        String error = validate(body);
        if (error != null) return responses.error(HttpStatus.BAD_REQUEST, error);
        Integer id = jdbc.queryForObject("""
                INSERT INTO promociones (titulo, descripcion, descuento_porcentaje, fecha_inicio, fecha_fin, activo)
                VALUES (?, ?, ?, ?, ?, ?); SELECT CAST(SCOPE_IDENTITY() AS INT)
                """, Integer.class, body.get("titulo"), emptyToNull(body.get("descripcion")), body.get("descuento_porcentaje"),
                body.get("fecha_inicio"), emptyToNull(body.get("fecha_fin")), toBit(body.getOrDefault("activo", true)));
        return responses.created("success", true, "message", "Promocion creada", "id", id);
    }

    @PutMapping("/{id}")
    ResponseEntity<Map<String, Object>> update(@RequestHeader(value = "Authorization", required = false) String authorization,
                                               @PathVariable Integer id,
                                               @RequestBody Map<String, Object> body) {
        if (auth.admin(authorization) == null) return responses.error(HttpStatus.FORBIDDEN, "Acceso denegado. Se requieren permisos de administrador");
        String error = validate(body);
        if (error != null) return responses.error(HttpStatus.BAD_REQUEST, error);
        int rows = jdbc.update("""
                UPDATE promociones
                SET titulo = ?, descripcion = ?, descuento_porcentaje = ?, fecha_inicio = ?, fecha_fin = ?, activo = ?
                WHERE id = ?
                """, body.get("titulo"), emptyToNull(body.get("descripcion")), body.get("descuento_porcentaje"),
                body.get("fecha_inicio"), emptyToNull(body.get("fecha_fin")), toBit(body.getOrDefault("activo", true)), id);
        if (rows == 0) return responses.error(HttpStatus.NOT_FOUND, "Promocion no encontrada");
        return responses.ok("success", true, "message", "Promocion actualizada");
    }

    @DeleteMapping("/{id}")
    ResponseEntity<Map<String, Object>> delete(@RequestHeader(value = "Authorization", required = false) String authorization,
                                               @PathVariable Integer id) {
        if (auth.admin(authorization) == null) return responses.error(HttpStatus.FORBIDDEN, "Acceso denegado. Se requieren permisos de administrador");
        int rows = jdbc.update("DELETE FROM promociones WHERE id = ?", id);
        if (rows == 0) return responses.error(HttpStatus.NOT_FOUND, "Promocion no encontrada");
        return responses.ok("success", true, "message", "Promocion eliminada");
    }

    private static String validate(Map<String, Object> body) {
        if (blank(body.get("titulo")) || body.get("descuento_porcentaje") == null || blank(body.get("fecha_inicio"))) {
            return "Titulo, descuento y fecha de inicio son requeridos";
        }
        return null;
    }

    private static boolean blank(Object value) {
        return value == null || String.valueOf(value).isBlank();
    }

    private static Boolean toBit(Object value) {
        return Boolean.TRUE.equals(value) || List.of("true", "1").contains(String.valueOf(value).toLowerCase());
    }

    private static Object emptyToNull(Object value) {
        return value == null || String.valueOf(value).isBlank() ? null : value;
    }
}
