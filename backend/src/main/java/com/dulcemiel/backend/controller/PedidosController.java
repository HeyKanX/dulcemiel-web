package com.dulcemiel.backend.controller;

import com.dulcemiel.backend.model.AuthUser;
import com.dulcemiel.backend.service.AuthSupport;
import com.dulcemiel.backend.service.ImageUrlService;
import com.dulcemiel.backend.service.ResponseService;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/pedidos")
public class PedidosController {
    private final JdbcTemplate jdbc;
    private final AuthSupport auth;
    private final ImageUrlService images;
    private final ResponseService responses;

    public PedidosController(JdbcTemplate jdbc, AuthSupport auth, ImageUrlService images, ResponseService responses) {
        this.jdbc = jdbc;
        this.auth = auth;
        this.images = images;
        this.responses = responses;
    }

    @PostMapping
    @Transactional
    ResponseEntity<Map<String, Object>> create(@RequestHeader(value = "Authorization", required = false) String authorization,
                                               @RequestBody Map<String, Object> body) {
        AuthUser user = auth.user(authorization);
        if (user == null) return responses.error(HttpStatus.UNAUTHORIZED, "Token no proporcionado");
        String validation = validateDelivery(body);
        if (validation != null) return responses.error(HttpStatus.BAD_REQUEST, validation);

        var items = jdbc.queryForList("""
                SELECT c.id, c.producto_id, c.cantidad, c.precio_unitario, p.stock, p.nombre
                FROM carrito c JOIN productos p ON c.producto_id = p.id
                WHERE c.usuario_id = ?
                """, user.userId());
        if (items.isEmpty()) return responses.error(HttpStatus.BAD_REQUEST, "El carrito está vacío");
        for (Map<String, Object> item : items) {
            if (integer(item.get("stock")) < integer(item.get("cantidad"))) {
                return responses.error(HttpStatus.BAD_REQUEST, "Stock insuficiente para " + item.get("nombre"));
            }
        }

        BigDecimal total = items.stream()
                .map(item -> decimal(item.get("cantidad")).multiply(decimal(item.get("precio_unitario"))))
                .reduce(BigDecimal.ZERO, BigDecimal::add);
        String orderNumber = "PED-" + System.currentTimeMillis();
        Integer orderId = jdbc.queryForObject("""
                INSERT INTO pedidos (
                  usuario_id, numero_pedido, total, contacto_nombre, contacto_telefono,
                  contacto_email, direccion_entrega, distrito, referencia, notas
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?); SELECT CAST(SCOPE_IDENTITY() AS INT)
                """, Integer.class, user.userId(), orderNumber, total, body.get("contacto_nombre"), body.get("contacto_telefono"),
                emptyToNull(body.get("contacto_email")), body.get("direccion_entrega"), body.get("distrito"),
                emptyToNull(body.get("referencia")), emptyToNull(body.get("notas")));

        for (Map<String, Object> item : items) {
            BigDecimal subtotal = decimal(item.get("cantidad")).multiply(decimal(item.get("precio_unitario")));
            jdbc.update("INSERT INTO detalles_pedido (pedido_id, producto_id, cantidad, precio_unitario, subtotal) VALUES (?, ?, ?, ?, ?)",
                    orderId, item.get("producto_id"), item.get("cantidad"), item.get("precio_unitario"), subtotal);
            jdbc.update("UPDATE productos SET stock = stock - ?, estado = CASE WHEN stock - ? <= 0 THEN 'agotado' ELSE estado END WHERE id = ?",
                    item.get("cantidad"), item.get("cantidad"), item.get("producto_id"));
        }
        jdbc.update("DELETE FROM carrito WHERE usuario_id = ?", user.userId());
        return responses.created("success", true, "message", "Pedido creado exitosamente",
                "pedido", responses.body("id", orderId, "numero_pedido", orderNumber, "total", total.setScale(2).toString()));
    }

    @GetMapping
    ResponseEntity<Map<String, Object>> userOrders(@RequestHeader(value = "Authorization", required = false) String authorization) {
        AuthUser user = auth.user(authorization);
        if (user == null) return responses.error(HttpStatus.UNAUTHORIZED, "Token no proporcionado");
        var rows = jdbc.queryForList("""
                SELECT id, numero_pedido, total, estado, fecha_pedido, fecha_entrega,
                       contacto_nombre, contacto_telefono, contacto_email, direccion_entrega, distrito, referencia, notas
                FROM pedidos WHERE usuario_id = ? ORDER BY fecha_pedido DESC
                """, user.userId());
        return responses.ok("success", true, "data", rows);
    }

    @GetMapping("/admin/todos")
    ResponseEntity<Map<String, Object>> allOrders(@RequestHeader(value = "Authorization", required = false) String authorization) {
        if (auth.admin(authorization) == null) return responses.error(HttpStatus.FORBIDDEN, "Acceso denegado. Se requieren permisos de administrador");
        var rows = jdbc.queryForList("""
                SELECT p.id, p.numero_pedido, p.total, p.estado, p.fecha_pedido, p.fecha_entrega,
                       p.contacto_nombre, p.contacto_telefono, p.contacto_email,
                       p.direccion_entrega, p.distrito, p.referencia, p.notas,
                       u.nombre, u.email
                FROM pedidos p JOIN usuarios u ON p.usuario_id = u.id
                ORDER BY p.fecha_pedido DESC
                """);
        return responses.ok("success", true, "data", rows);
    }

    @GetMapping("/{pedidoId}")
    ResponseEntity<Map<String, Object>> detail(@RequestHeader(value = "Authorization", required = false) String authorization,
                                               @PathVariable Integer pedidoId,
                                               HttpServletRequest request) {
        AuthUser user = auth.user(authorization);
        if (user == null) return responses.error(HttpStatus.UNAUTHORIZED, "Token no proporcionado");
        boolean admin = user.canAdmin();
        var pedidos = admin
                ? jdbc.queryForList("SELECT * FROM pedidos WHERE id = ?", pedidoId)
                : jdbc.queryForList("SELECT * FROM pedidos WHERE id = ? AND usuario_id = ?", pedidoId, user.userId());
        if (pedidos.isEmpty()) return responses.error(HttpStatus.NOT_FOUND, "Pedido no encontrado");
        var detalles = jdbc.queryForList("""
                SELECT dp.id, dp.producto_id, p.nombre, dp.cantidad, dp.precio_unitario, dp.subtotal,
                       CAST(CASE WHEN p.imagen_data IS NULL THEN 0 ELSE 1 END AS BIT) AS tiene_imagen
                FROM detalles_pedido dp JOIN productos p ON dp.producto_id = p.id
                WHERE dp.pedido_id = ?
                """, pedidoId);
        return responses.ok("success", true, "pedido", pedidos.get(0),
                "detalles", detalles.stream().map(row -> images.product(request, row)).toList());
    }

    @PutMapping("/{pedidoId}")
    ResponseEntity<Map<String, Object>> updateStatus(@RequestHeader(value = "Authorization", required = false) String authorization,
                                                     @PathVariable Integer pedidoId,
                                                     @RequestBody Map<String, Object> body) {
        if (auth.admin(authorization) == null) return responses.error(HttpStatus.FORBIDDEN, "Acceso denegado. Se requieren permisos de administrador");
        String estado = String.valueOf(body.getOrDefault("estado", ""));
        if (estado.isBlank()) return responses.error(HttpStatus.BAD_REQUEST, "Estado es requerido");
        if (!List.of("pendiente", "procesando", "enviado", "entregado", "cancelado").contains(estado)) {
            return responses.error(HttpStatus.BAD_REQUEST, "Estado inválido");
        }
        int rows = jdbc.update("UPDATE pedidos SET estado = ? WHERE id = ?", estado, pedidoId);
        if (rows == 0) return responses.error(HttpStatus.NOT_FOUND, "Pedido no encontrado");
        return responses.ok("success", true, "message", "Estado del pedido actualizado");
    }

    private static String validateDelivery(Map<String, Object> body) {
        if (blank(body.get("contacto_nombre"))) return "Ingresa el nombre de la persona que recibira el pedido";
        if (blank(body.get("contacto_telefono"))) return "Ingresa un numero de celular o telefono de contacto";
        if (!String.valueOf(body.get("contacto_telefono")).trim().matches("^[0-9+()\\s-]{6,20}$")) return "Ingresa un numero de contacto valido";
        if (blank(body.get("direccion_entrega"))) return "Ingresa la direccion de entrega";
        if (blank(body.get("distrito"))) return "Ingresa el distrito o ciudad de entrega";
        if (body.get("referencia") != null && String.valueOf(body.get("referencia")).length() > 300) return "La referencia no debe superar los 300 caracteres";
        return null;
    }

    private static boolean blank(Object value) {
        return value == null || String.valueOf(value).trim().isEmpty();
    }

    private static Object emptyToNull(Object value) {
        return value == null || String.valueOf(value).isBlank() ? null : value;
    }

    private static Integer integer(Object value) {
        return ((Number) value).intValue();
    }

    private static BigDecimal decimal(Object value) {
        return value instanceof BigDecimal bd ? bd : new BigDecimal(String.valueOf(value));
    }
}
