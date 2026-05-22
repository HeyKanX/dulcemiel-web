package com.dulcemiel.backend.model;

public record AuthUser(Integer userId, String email, String role) {
    public boolean canAdmin() {
        return "admin".equals(role) || "empleado".equals(role);
    }

    public boolean isOwnerAdmin() {
        return "admin".equals(role);
    }
}
