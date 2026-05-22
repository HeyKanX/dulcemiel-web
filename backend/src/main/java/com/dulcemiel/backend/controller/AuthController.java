package com.dulcemiel.backend.controller;

import com.dulcemiel.backend.model.AuthUser;
import com.dulcemiel.backend.service.JwtService;
import com.dulcemiel.backend.service.ResponseService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/auth")
public class AuthController {
    private final JdbcTemplate jdbc;
    private final PasswordEncoder passwordEncoder;
    private final JwtService jwt;
    private final ResponseService responses;

    public AuthController(JdbcTemplate jdbc, PasswordEncoder passwordEncoder, JwtService jwt, ResponseService responses) {
        this.jdbc = jdbc;
        this.passwordEncoder = passwordEncoder;
        this.jwt = jwt;
        this.responses = responses;
    }

    @PostMapping("/register")
    ResponseEntity<Map<String, Object>> register(@RequestBody Map<String, Object> body) {
        String nombre = text(body.get("nombre"));
        String email = text(body.get("email"));
        String password = text(body.get("password"));
        String passwordConfirm = text(body.get("passwordConfirm"));
        if (blank(nombre) || blank(email) || blank(password) || blank(passwordConfirm)) {
            return responses.error(HttpStatus.BAD_REQUEST, "Por favor completa todos los campos");
        }
        if (!password.equals(passwordConfirm)) {
            return responses.error(HttpStatus.BAD_REQUEST, "Las contraseñas no coinciden");
        }
        if (!jdbc.queryForList("SELECT email FROM usuarios WHERE email = ?", email).isEmpty()) {
            return responses.error(HttpStatus.BAD_REQUEST, "El email ya está registrado");
        }
        Integer id = jdbc.queryForObject(
                "INSERT INTO usuarios (nombre, email, password, rol) VALUES (?, ?, ?, ?); SELECT CAST(SCOPE_IDENTITY() AS INT)",
                Integer.class, nombre, email, passwordEncoder.encode(password), "usuario");
        return responses.created("success", true, "message", "Usuario registrado exitosamente", "userId", id);
    }

    @PostMapping("/login")
    ResponseEntity<Map<String, Object>> login(@RequestBody Map<String, Object> body) {
        String email = text(body.get("email"));
        String password = text(body.get("password"));
        if (blank(email) || blank(password)) {
            return responses.error(HttpStatus.BAD_REQUEST, "Por favor proporciona email y contraseña");
        }
        List<Map<String, Object>> users = jdbc.queryForList("SELECT * FROM usuarios WHERE email = ?", email);
        if (users.isEmpty() || !passwordEncoder.matches(password, text(users.get(0).get("password")))) {
            return responses.error(HttpStatus.UNAUTHORIZED, "Email o contraseña incorrectos");
        }
        Map<String, Object> user = users.get(0);
        if (!"activo".equals(text(user.get("estado")))) {
            return responses.error(HttpStatus.FORBIDDEN, "Usuario inactivo");
        }
        Integer id = number(user.get("id")).intValue();
        String role = text(user.get("rol"));
        return responses.ok(
                "success", true,
                "message", "Login exitoso",
                "token", jwt.generateToken(id, text(user.get("email")), role),
                "usuario", responses.body("id", id, "nombre", user.get("nombre"), "email", user.get("email"), "rol", role)
        );
    }

    @GetMapping("/perfil")
    ResponseEntity<Map<String, Object>> profile(@RequestHeader(value = "Authorization", required = false) String authorization) {
        AuthUser auth = requireAuth(authorization);
        if (auth == null) return responses.error(HttpStatus.UNAUTHORIZED, "Token no proporcionado");
        List<Map<String, Object>> users = jdbc.queryForList(
                "SELECT id, nombre, email, rol, estado, fecha_creacion FROM usuarios WHERE id = ?", auth.userId());
        if (users.isEmpty()) return responses.error(HttpStatus.NOT_FOUND, "Usuario no encontrado");
        return responses.ok("success", true, "usuario", users.get(0));
    }

    @GetMapping("/usuarios")
    ResponseEntity<Map<String, Object>> users(@RequestHeader(value = "Authorization", required = false) String authorization) {
        AuthUser auth = requireAdmin(authorization);
        if (auth == null) return responses.error(HttpStatus.FORBIDDEN, "Acceso denegado. Se requieren permisos de administrador");
        return responses.ok("success", true, "data", jdbc.queryForList(
                "SELECT id, nombre, email, rol, estado, fecha_creacion FROM usuarios ORDER BY fecha_creacion DESC"));
    }

    @PostMapping("/empleados")
    ResponseEntity<Map<String, Object>> createEmployee(@RequestHeader(value = "Authorization", required = false) String authorization,
                                                       @RequestBody Map<String, Object> body) {
        AuthUser auth = requireOwnerAdmin(authorization);
        if (auth == null) return responses.error(HttpStatus.FORBIDDEN, "Acceso denegado. Solo el administrador principal puede realizar esta accion");
        String nombre = text(body.get("nombre"));
        String email = text(body.get("email"));
        String password = text(body.get("password"));
        String rol = blank(text(body.get("rol"))) ? "empleado" : text(body.get("rol"));
        if (blank(nombre) || blank(email) || blank(password)) {
            return responses.error(HttpStatus.BAD_REQUEST, "Nombre, email y contrasena son requeridos");
        }
        if (!List.of("empleado", "admin").contains(rol)) {
            return responses.error(HttpStatus.BAD_REQUEST, "Rol administrativo invalido");
        }
        if (!jdbc.queryForList("SELECT id FROM usuarios WHERE email = ?", email).isEmpty()) {
            return responses.error(HttpStatus.BAD_REQUEST, "El email ya esta registrado");
        }
        Integer id = jdbc.queryForObject(
                "INSERT INTO usuarios (nombre, email, password, rol) VALUES (?, ?, ?, ?); SELECT CAST(SCOPE_IDENTITY() AS INT)",
                Integer.class, nombre, email, passwordEncoder.encode(password), rol);
        return responses.created("success", true, "message", "Empleado registrado exitosamente", "userId", id);
    }

    @PutMapping("/usuarios/{id}")
    ResponseEntity<Map<String, Object>> updateUser(@RequestHeader(value = "Authorization", required = false) String authorization,
                                                   @PathVariable Integer id,
                                                   @RequestBody Map<String, Object> body) {
        AuthUser auth = requireOwnerAdmin(authorization);
        if (auth == null) return responses.error(HttpStatus.FORBIDDEN, "Acceso denegado. Solo el administrador principal puede realizar esta accion");
        String nombre = text(body.get("nombre"));
        String email = text(body.get("email"));
        String rol = text(body.get("rol"));
        String estado = text(body.get("estado"));
        if (blank(nombre) || blank(email) || !List.of("admin", "empleado", "usuario").contains(rol) || !List.of("activo", "inactivo").contains(estado)) {
            return responses.error(HttpStatus.BAD_REQUEST, "Datos de usuario invalidos");
        }
        int rows = jdbc.update("UPDATE usuarios SET nombre = ?, email = ?, rol = ?, estado = ? WHERE id = ?", nombre, email, rol, estado, id);
        if (rows == 0) return responses.error(HttpStatus.NOT_FOUND, "Usuario no encontrado");
        return responses.ok("success", true, "message", "Usuario actualizado");
    }

    private AuthUser requireAuth(String authorization) {
        return jwt.parse(authorization);
    }

    private AuthUser requireAdmin(String authorization) {
        AuthUser auth = jwt.parse(authorization);
        return auth != null && auth.canAdmin() ? auth : null;
    }

    private AuthUser requireOwnerAdmin(String authorization) {
        AuthUser auth = jwt.parse(authorization);
        return auth != null && auth.isOwnerAdmin() ? auth : null;
    }

    private static String text(Object value) {
        return value == null ? "" : String.valueOf(value);
    }

    private static boolean blank(String value) {
        return value == null || value.trim().isEmpty();
    }

    private static Number number(Object value) {
        return (Number) value;
    }
}
