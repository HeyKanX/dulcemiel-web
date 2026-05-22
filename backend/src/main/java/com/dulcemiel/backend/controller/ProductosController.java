package com.dulcemiel.backend.controller;

import com.dulcemiel.backend.model.AuthUser;
import com.dulcemiel.backend.service.ImageUrlService;
import com.dulcemiel.backend.service.JwtService;
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
@RequestMapping("/api/productos")
public class ProductosController {
    private final JdbcTemplate jdbc;
    private final JwtService jwt;
    private final ImageUrlService images;
    private final ResponseService responses;

    public ProductosController(JdbcTemplate jdbc, JwtService jwt, ImageUrlService images, ResponseService responses) {
        this.jdbc = jdbc;
        this.jwt = jwt;
        this.images = images;
        this.responses = responses;
    }

    @GetMapping
    ResponseEntity<Map<String, Object>> list(HttpServletRequest request) {
        var rows = jdbc.queryForList("SELECT id, nombre, descripcion, precio, stock, categoria, estado, fecha_actualizacion, CAST(CASE WHEN imagen_data IS NULL THEN 0 ELSE 1 END AS BIT) AS tiene_imagen FROM productos WHERE estado = 'disponible'");
        return responses.ok("success", true, "data", rows.stream().map(row -> images.product(request, row)).toList());
    }

    @GetMapping("/admin/todos")
    ResponseEntity<Map<String, Object>> listAll(@RequestHeader(value = "Authorization", required = false) String authorization, HttpServletRequest request) {
        if (!isAdmin(authorization)) return responses.error(HttpStatus.FORBIDDEN, "Acceso denegado. Se requieren permisos de administrador");
        var rows = jdbc.queryForList("SELECT id, nombre, descripcion, precio, stock, categoria, estado, fecha_actualizacion, CAST(CASE WHEN imagen_data IS NULL THEN 0 ELSE 1 END AS BIT) AS tiene_imagen FROM productos ORDER BY fecha_creacion DESC");
        return responses.ok("success", true, "data", rows.stream().map(row -> images.product(request, row)).toList());
    }

    @GetMapping("/{id}")
    ResponseEntity<Map<String, Object>> get(@PathVariable Integer id, HttpServletRequest request) {
        var rows = jdbc.queryForList("SELECT id, nombre, descripcion, precio, stock, categoria, estado, fecha_creacion, fecha_actualizacion, CAST(CASE WHEN imagen_data IS NULL THEN 0 ELSE 1 END AS BIT) AS tiene_imagen FROM productos WHERE id = ?", id);
        if (rows.isEmpty()) return responses.error(HttpStatus.NOT_FOUND, "Producto no encontrado");
        return responses.ok("success", true, "data", images.product(request, rows.get(0)));
    }

    @PostMapping
    ResponseEntity<Map<String, Object>> create(@RequestHeader(value = "Authorization", required = false) String authorization,
                                               @RequestParam Map<String, String> body,
                                               @RequestParam(value = "imagen", required = false) MultipartFile image) throws IOException {
        if (!isAdmin(authorization)) return responses.error(HttpStatus.FORBIDDEN, "Acceso denegado. Se requieren permisos de administrador");
        String error = validateProduct(body.get("nombre"), body.get("precio"), body.get("stock"), "disponible");
        if (error != null) return responses.error(HttpStatus.BAD_REQUEST, error);
        Integer id = jdbc.queryForObject("""
                INSERT INTO productos (nombre, descripcion, precio, stock, categoria, imagen_data, imagen_mime, imagen_nombre)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?); SELECT CAST(SCOPE_IDENTITY() AS INT)
                """, Integer.class, body.get("nombre"), emptyToNull(body.get("descripcion")), body.get("precio"), body.get("stock"), emptyToNull(body.get("categoria")),
                imageBytes(image), image == null ? null : image.getContentType(), image == null ? null : image.getOriginalFilename());
        return responses.created("success", true, "message", "Producto creado exitosamente", "productId", id);
    }

    @PutMapping("/{id}")
    ResponseEntity<Map<String, Object>> update(@RequestHeader(value = "Authorization", required = false) String authorization,
                                               @PathVariable Integer id,
                                               @RequestParam Map<String, String> body,
                                               @RequestParam(value = "imagen", required = false) MultipartFile image) throws IOException {
        if (!isAdmin(authorization)) return responses.error(HttpStatus.FORBIDDEN, "Acceso denegado. Se requieren permisos de administrador");
        String estado = body.getOrDefault("estado", "disponible");
        String error = validateProduct(body.get("nombre"), body.get("precio"), body.get("stock"), estado);
        if (error != null) return responses.error(HttpStatus.BAD_REQUEST, error);
        if (jdbc.queryForList("SELECT id FROM productos WHERE id = ?", id).isEmpty()) return responses.error(HttpStatus.NOT_FOUND, "Producto no encontrado");
        if (image == null || image.isEmpty()) {
            jdbc.update("UPDATE productos SET nombre = ?, descripcion = ?, precio = ?, stock = ?, categoria = ?, estado = ? WHERE id = ?",
                    body.get("nombre"), emptyToNull(body.get("descripcion")), body.get("precio"), body.get("stock"), emptyToNull(body.get("categoria")), estado, id);
        } else {
            jdbc.update("UPDATE productos SET nombre = ?, descripcion = ?, precio = ?, stock = ?, categoria = ?, estado = ?, imagen_data = ?, imagen_mime = ?, imagen_nombre = ? WHERE id = ?",
                    body.get("nombre"), emptyToNull(body.get("descripcion")), body.get("precio"), body.get("stock"), emptyToNull(body.get("categoria")), estado,
                    image.getBytes(), image.getContentType(), image.getOriginalFilename(), id);
        }
        return responses.ok("success", true, "message", "Producto actualizado exitosamente");
    }

    @DeleteMapping("/{id}")
    ResponseEntity<Map<String, Object>> delete(@RequestHeader(value = "Authorization", required = false) String authorization, @PathVariable Integer id) {
        if (!isAdmin(authorization)) return responses.error(HttpStatus.FORBIDDEN, "Acceso denegado. Se requieren permisos de administrador");
        Number assigned = jdbc.queryForObject("SELECT COUNT(*) FROM detalles_pedido WHERE producto_id = ?", Number.class, id);
        if (assigned != null && assigned.intValue() > 0) {
            return responses.error(HttpStatus.CONFLICT, "No se puede eliminar este producto porque ya esta asignado a uno o mas pedidos. Cambia su estado a discontinuado para ocultarlo del catalogo.");
        }
        int rows = jdbc.update("DELETE FROM productos WHERE id = ?", id);
        if (rows == 0) return responses.error(HttpStatus.NOT_FOUND, "Producto no encontrado");
        return responses.ok("success", true, "message", "Producto eliminado exitosamente");
    }

    private boolean isAdmin(String authorization) {
        AuthUser user = jwt.parse(authorization);
        return user != null && user.canAdmin();
    }

    private static String validateProduct(String nombre, String precio, String stock, String estado) {
        if (nombre == null || nombre.trim().isEmpty()) return "El nombre del producto es requerido";
        if (precio == null || precio.isBlank() || Double.parseDouble(precio) < 0) return "El precio es requerido y debe ser mayor o igual a 0";
        if (stock == null || stock.isBlank() || Integer.parseInt(stock) < 0) return "El stock es requerido y debe ser mayor o igual a 0";
        if (!List.of("disponible", "agotado", "discontinuado").contains(estado)) return "El estado del producto no es valido";
        return null;
    }

    private static Object emptyToNull(String value) {
        return value == null || value.isBlank() ? null : value;
    }

    private static byte[] imageBytes(MultipartFile image) throws IOException {
        return image == null || image.isEmpty() ? null : image.getBytes();
    }
}
