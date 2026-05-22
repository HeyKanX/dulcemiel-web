package com.dulcemiel.backend.controller;

import com.dulcemiel.backend.service.AuthSupport;
import com.dulcemiel.backend.service.ImageUrlService;
import com.dulcemiel.backend.service.ResponseService;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/sitio")
public class SitioController {
    private final JdbcTemplate jdbc;
    private final AuthSupport auth;
    private final ImageUrlService images;
    private final ResponseService responses;

    public SitioController(JdbcTemplate jdbc, AuthSupport auth, ImageUrlService images, ResponseService responses) {
        this.jdbc = jdbc;
        this.auth = auth;
        this.images = images;
        this.responses = responses;
    }

    @GetMapping("/inicio")
    ResponseEntity<Map<String, Object>> home(HttpServletRequest request) {
        var settings = jdbc.queryForList("""
                SELECT id, nombre_empresa, descripcion_inicio, mision, vision,
                       CAST(CASE WHEN logo_data IS NULL THEN 0 ELSE 1 END AS BIT) AS tiene_logo
                FROM configuracion_sitio WHERE id = 1
                """);
        var carousel = jdbc.queryForList("""
                SELECT id, titulo, descripcion, orden, activo,
                       CAST(CASE WHEN imagen_data IS NULL THEN 0 ELSE 1 END AS BIT) AS tiene_imagen
                FROM carrusel_inicio WHERE activo = 1 ORDER BY orden ASC, id ASC
                """);
        var promos = jdbc.queryForList("""
                SELECT id, titulo, descripcion, descuento_porcentaje, fecha_inicio, fecha_fin, activo
                FROM promociones WHERE activo = 1 AND (fecha_fin IS NULL OR fecha_fin >= CONVERT(date, GETDATE()))
                ORDER BY fecha_creacion DESC
                """);
        return responses.ok(
                "success", true,
                "configuracion", images.siteSettings(request, settings.isEmpty() ? null : settings.get(0)),
                "carrusel", carousel.stream().map(row -> images.carousel(request, row)).toList(),
                "promociones", promos
        );
    }

    @PutMapping("/configuracion")
    ResponseEntity<Map<String, Object>> updateConfig(@RequestHeader(value = "Authorization", required = false) String authorization,
                                                     @RequestParam Map<String, String> body,
                                                     @RequestParam(value = "logo", required = false) MultipartFile logo) throws IOException {
        if (auth.admin(authorization) == null) return responses.error(HttpStatus.FORBIDDEN, "Acceso denegado. Se requieren permisos de administrador");
        for (String key : List.of("nombre_empresa", "descripcion_inicio", "mision", "vision")) {
            if (body.get(key) == null || body.get(key).isBlank()) return responses.error(HttpStatus.BAD_REQUEST, messageFor(key));
        }
        if (logo == null || logo.isEmpty()) {
            jdbc.update("UPDATE configuracion_sitio SET nombre_empresa = ?, descripcion_inicio = ?, mision = ?, vision = ? WHERE id = 1",
                    body.get("nombre_empresa"), body.get("descripcion_inicio"), body.get("mision"), body.get("vision"));
        } else {
            jdbc.update("UPDATE configuracion_sitio SET nombre_empresa = ?, descripcion_inicio = ?, mision = ?, vision = ?, logo_data = ?, logo_mime = ?, logo_nombre = ? WHERE id = 1",
                    body.get("nombre_empresa"), body.get("descripcion_inicio"), body.get("mision"), body.get("vision"),
                    logo.getBytes(), logo.getContentType(), logo.getOriginalFilename());
        }
        return responses.ok("success", true, "message", "Configuracion actualizada");
    }

    @PostMapping("/carrusel")
    ResponseEntity<Map<String, Object>> createCarousel(@RequestHeader(value = "Authorization", required = false) String authorization,
                                                       @RequestParam Map<String, String> body,
                                                       @RequestParam(value = "imagen", required = false) MultipartFile image) throws IOException {
        if (auth.admin(authorization) == null) return responses.error(HttpStatus.FORBIDDEN, "Acceso denegado. Se requieren permisos de administrador");
        if (body.get("titulo") == null || body.get("titulo").isBlank()) return responses.error(HttpStatus.BAD_REQUEST, "El titulo del carrusel es requerido");
        if (image == null || image.isEmpty()) return responses.error(HttpStatus.BAD_REQUEST, "Debes seleccionar una imagen JPG, PNG o ICO para crear el carrusel");
        Integer id = jdbc.queryForObject("""
                INSERT INTO carrusel_inicio (titulo, descripcion, orden, activo, imagen_data, imagen_mime, imagen_nombre)
                VALUES (?, ?, ?, ?, ?, ?, ?); SELECT CAST(SCOPE_IDENTITY() AS INT)
                """, Integer.class, body.get("titulo"), emptyToNull(body.get("descripcion")),
                body.getOrDefault("orden", "0"), toBit(body.getOrDefault("activo", "true")),
                image.getBytes(), image.getContentType(), image.getOriginalFilename());
        return responses.created("success", true, "message", "Imagen de carrusel creada", "id", id);
    }

    @PutMapping("/carrusel/{id}")
    ResponseEntity<Map<String, Object>> updateCarousel(@RequestHeader(value = "Authorization", required = false) String authorization,
                                                       @PathVariable Integer id,
                                                       @RequestParam Map<String, String> body,
                                                       @RequestParam(value = "imagen", required = false) MultipartFile image) throws IOException {
        if (auth.admin(authorization) == null) return responses.error(HttpStatus.FORBIDDEN, "Acceso denegado. Se requieren permisos de administrador");
        if (body.get("titulo") == null || body.get("titulo").isBlank()) return responses.error(HttpStatus.BAD_REQUEST, "El titulo del carrusel es requerido");
        int rows;
        if (image == null || image.isEmpty()) {
            rows = jdbc.update("UPDATE carrusel_inicio SET titulo = ?, descripcion = ?, orden = ?, activo = ? WHERE id = ?",
                    body.get("titulo"), emptyToNull(body.get("descripcion")), body.getOrDefault("orden", "0"), toBit(body.getOrDefault("activo", "true")), id);
        } else {
            rows = jdbc.update("UPDATE carrusel_inicio SET titulo = ?, descripcion = ?, orden = ?, activo = ?, imagen_data = ?, imagen_mime = ?, imagen_nombre = ? WHERE id = ?",
                    body.get("titulo"), emptyToNull(body.get("descripcion")), body.getOrDefault("orden", "0"), toBit(body.getOrDefault("activo", "true")),
                    image.getBytes(), image.getContentType(), image.getOriginalFilename(), id);
        }
        if (rows == 0) return responses.error(HttpStatus.NOT_FOUND, "Imagen de carrusel no encontrada");
        return responses.ok("success", true, "message", "Imagen de carrusel actualizada");
    }

    @DeleteMapping("/carrusel/{id}")
    ResponseEntity<Map<String, Object>> deleteCarousel(@RequestHeader(value = "Authorization", required = false) String authorization,
                                                       @PathVariable Integer id) {
        if (auth.admin(authorization) == null) return responses.error(HttpStatus.FORBIDDEN, "Acceso denegado. Se requieren permisos de administrador");
        int rows = jdbc.update("DELETE FROM carrusel_inicio WHERE id = ?", id);
        if (rows == 0) return responses.error(HttpStatus.NOT_FOUND, "Imagen de carrusel no encontrada");
        return responses.ok("success", true, "message", "Imagen eliminada");
    }

    private static String messageFor(String key) {
        return switch (key) {
            case "nombre_empresa" -> "El nombre de la empresa es requerido";
            case "descripcion_inicio" -> "La descripcion de inicio es requerida";
            case "mision" -> "La mision es requerida";
            default -> "La vision es requerida";
        };
    }

    private static Object emptyToNull(String value) {
        return value == null || value.isBlank() ? null : value;
    }

    private static Boolean toBit(String value) {
        return "true".equalsIgnoreCase(value) || "1".equals(value);
    }
}
