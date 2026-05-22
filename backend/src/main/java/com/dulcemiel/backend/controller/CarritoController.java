package com.dulcemiel.backend.controller;

import com.dulcemiel.backend.model.AuthUser;
import com.dulcemiel.backend.service.AuthSupport;
import com.dulcemiel.backend.service.ImageUrlService;
import com.dulcemiel.backend.service.ResponseService;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.util.Map;

@RestController
@RequestMapping("/api/carrito")
public class CarritoController {
    private final JdbcTemplate jdbc;
    private final AuthSupport auth;
    private final ImageUrlService images;
    private final ResponseService responses;

    public CarritoController(JdbcTemplate jdbc, AuthSupport auth, ImageUrlService images, ResponseService responses) {
        this.jdbc = jdbc;
        this.auth = auth;
        this.images = images;
        this.responses = responses;
    }

    @GetMapping
    ResponseEntity<Map<String, Object>> get(@RequestHeader(value = "Authorization", required = false) String authorization,
                                            HttpServletRequest request) {
        AuthUser user = auth.user(authorization);
        if (user == null) return responses.error(HttpStatus.UNAUTHORIZED, "Token no proporcionado");
        var rows = jdbc.queryForList("""
                SELECT c.id, c.producto_id, c.cantidad, c.precio_unitario,
                       p.nombre, p.precio, CAST(CASE WHEN p.imagen_data IS NULL THEN 0 ELSE 1 END AS BIT) AS tiene_imagen
                FROM carrito c JOIN productos p ON c.producto_id = p.id
                WHERE c.usuario_id = ?
                """, user.userId());
        var data = rows.stream().map(row -> images.product(request, row)).toList();
        BigDecimal total = data.stream()
                .map(row -> decimal(row.get("precio")).multiply(decimal(row.get("cantidad"))))
                .reduce(BigDecimal.ZERO, BigDecimal::add);
        return responses.ok("success", true, "data", data, "total", total.setScale(2).toString());
    }

    @PostMapping("/agregar")
    ResponseEntity<Map<String, Object>> add(@RequestHeader(value = "Authorization", required = false) String authorization,
                                            @RequestBody Map<String, Object> body) {
        AuthUser user = auth.user(authorization);
        if (user == null) return responses.error(HttpStatus.UNAUTHORIZED, "Token no proporcionado");
        Integer productId = integer(body.get("producto_id"));
        Integer quantity = integer(body.get("cantidad"));
        if (productId == null || quantity == null) return responses.error(HttpStatus.BAD_REQUEST, "Producto ID y cantidad son requeridos");
        var products = jdbc.queryForList("SELECT precio, stock FROM productos WHERE id = ?", productId);
        if (products.isEmpty()) return responses.error(HttpStatus.NOT_FOUND, "Producto no encontrado");
        if (integer(products.get(0).get("stock")) < quantity) return responses.error(HttpStatus.BAD_REQUEST, "Stock insuficiente");
        var existing = jdbc.queryForList("SELECT id, cantidad FROM carrito WHERE usuario_id = ? AND producto_id = ?", user.userId(), productId);
        if (existing.isEmpty()) {
            jdbc.update("INSERT INTO carrito (usuario_id, producto_id, cantidad, precio_unitario) VALUES (?, ?, ?, ?)",
                    user.userId(), productId, quantity, products.get(0).get("precio"));
        } else {
            jdbc.update("UPDATE carrito SET cantidad = ? WHERE id = ?",
                    integer(existing.get(0).get("cantidad")) + quantity, existing.get(0).get("id"));
        }
        return responses.created("success", true, "message", "Producto agregado al carrito");
    }

    @PutMapping("/actualizar")
    ResponseEntity<Map<String, Object>> update(@RequestHeader(value = "Authorization", required = false) String authorization,
                                               @RequestBody Map<String, Object> body) {
        AuthUser user = auth.user(authorization);
        if (user == null) return responses.error(HttpStatus.UNAUTHORIZED, "Token no proporcionado");
        Integer cartId = integer(body.get("carrito_id"));
        Integer quantity = integer(body.get("cantidad"));
        if (cartId == null || quantity == null) return responses.error(HttpStatus.BAD_REQUEST, "Carrito ID y cantidad son requeridos");
        var items = jdbc.queryForList("SELECT producto_id FROM carrito WHERE id = ? AND usuario_id = ?", cartId, user.userId());
        if (items.isEmpty()) return responses.error(HttpStatus.NOT_FOUND, "Item no encontrado en el carrito");
        Number stock = jdbc.queryForObject("SELECT stock FROM productos WHERE id = ?", Number.class, items.get(0).get("producto_id"));
        if (stock != null && stock.intValue() < quantity) return responses.error(HttpStatus.BAD_REQUEST, "Stock insuficiente");
        jdbc.update("UPDATE carrito SET cantidad = ? WHERE id = ?", quantity, cartId);
        return responses.ok("success", true, "message", "Carrito actualizado");
    }

    @DeleteMapping("/{carritoId}")
    ResponseEntity<Map<String, Object>> delete(@RequestHeader(value = "Authorization", required = false) String authorization,
                                               @PathVariable Integer carritoId) {
        AuthUser user = auth.user(authorization);
        if (user == null) return responses.error(HttpStatus.UNAUTHORIZED, "Token no proporcionado");
        int rows = jdbc.update("DELETE FROM carrito WHERE id = ? AND usuario_id = ?", carritoId, user.userId());
        if (rows == 0) return responses.error(HttpStatus.NOT_FOUND, "Item no encontrado");
        return responses.ok("success", true, "message", "Producto eliminado del carrito");
    }

    @DeleteMapping
    ResponseEntity<Map<String, Object>> clear(@RequestHeader(value = "Authorization", required = false) String authorization) {
        AuthUser user = auth.user(authorization);
        if (user == null) return responses.error(HttpStatus.UNAUTHORIZED, "Token no proporcionado");
        jdbc.update("DELETE FROM carrito WHERE usuario_id = ?", user.userId());
        return responses.ok("success", true, "message", "Carrito vaciado");
    }

    private static Integer integer(Object value) {
        return value == null ? null : ((Number) value).intValue();
    }

    private static BigDecimal decimal(Object value) {
        return value instanceof BigDecimal bd ? bd : new BigDecimal(String.valueOf(value));
    }
}
