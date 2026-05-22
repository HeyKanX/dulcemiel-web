package com.dulcemiel.backend.controller;

import org.springframework.http.*;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/imagenes")
public class ImagenesController {
    private final JdbcTemplate jdbc;

    public ImagenesController(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    @GetMapping("/{tipo}/{id}")
    ResponseEntity<?> image(@PathVariable String tipo, @PathVariable Integer id) {
        String query = switch (tipo) {
            case "producto" -> "SELECT imagen_data AS data, imagen_mime AS mime FROM productos WHERE id = ?";
            case "carrusel" -> "SELECT imagen_data AS data, imagen_mime AS mime FROM carrusel_inicio WHERE id = ?";
            case "logo" -> "SELECT logo_data AS data, logo_mime AS mime FROM configuracion_sitio WHERE id = ?";
            default -> null;
        };
        if (query == null) return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("success", false, "message", "Tipo de imagen no encontrado"));
        var rows = jdbc.queryForList(query, id);
        if (rows.isEmpty() || rows.get(0).get("data") == null) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("success", false, "message", "Imagen no encontrada"));
        }
        byte[] data = (byte[]) rows.get(0).get("data");
        String mime = String.valueOf(rows.get(0).getOrDefault("mime", "image/png"));
        return ResponseEntity.ok()
                .contentType(MediaType.parseMediaType(mime))
                .cacheControl(CacheControl.noStore())
                .body(data);
    }
}
