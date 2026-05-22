package com.dulcemiel.backend.controller;

import com.dulcemiel.backend.service.AuthSupport;
import com.dulcemiel.backend.service.ResponseService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/dashboard")
public class DashboardController {
    private final JdbcTemplate jdbc;
    private final AuthSupport auth;
    private final ResponseService responses;

    public DashboardController(JdbcTemplate jdbc, AuthSupport auth, ResponseService responses) {
        this.jdbc = jdbc;
        this.auth = auth;
        this.responses = responses;
    }

    @GetMapping("/resumen")
    ResponseEntity<Map<String, Object>> summary(@RequestHeader(value = "Authorization", required = false) String authorization) {
        if (auth.admin(authorization) == null) return responses.error(HttpStatus.FORBIDDEN, "Acceso denegado. Se requieren permisos de administrador");
        var resumen = jdbc.queryForList("""
                SELECT
                  (SELECT COUNT(*) FROM productos) AS productos,
                  (SELECT COUNT(*) FROM pedidos) AS pedidos,
                  (SELECT COUNT(*) FROM usuarios WHERE rol = 'usuario') AS clientes,
                  (SELECT COUNT(*) FROM usuarios WHERE rol IN ('admin', 'empleado')) AS equipo,
                  (SELECT ISNULL(SUM(total), 0) FROM pedidos WHERE estado = 'entregado') AS ventas,
                  (SELECT COUNT(*) FROM pedidos WHERE estado = 'pendiente') AS pedidos_pendientes,
                  (SELECT COUNT(*) FROM productos WHERE stock <= 5) AS stock_bajo
                """).get(0);
        var porEstado = jdbc.queryForList("SELECT estado, COUNT(*) AS total FROM pedidos GROUP BY estado ORDER BY estado");
        var recientes = jdbc.queryForList("""
                SELECT TOP 8 p.id, p.numero_pedido, p.total, p.estado, p.fecha_pedido, u.nombre, u.email
                FROM pedidos p JOIN usuarios u ON p.usuario_id = u.id
                ORDER BY p.fecha_pedido DESC
                """);
        return responses.ok("success", true, "resumen", resumen, "porEstado", porEstado, "recientes", recientes);
    }
}
