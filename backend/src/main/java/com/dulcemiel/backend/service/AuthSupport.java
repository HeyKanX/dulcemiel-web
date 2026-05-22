package com.dulcemiel.backend.service;

import com.dulcemiel.backend.model.AuthUser;
import org.springframework.stereotype.Service;

@Service
public class AuthSupport {
    private final JwtService jwt;

    public AuthSupport(JwtService jwt) {
        this.jwt = jwt;
    }

    public AuthUser user(String authorization) {
        return jwt.parse(authorization);
    }

    public AuthUser admin(String authorization) {
        AuthUser user = jwt.parse(authorization);
        return user != null && user.canAdmin() ? user : null;
    }

    public AuthUser ownerAdmin(String authorization) {
        AuthUser user = jwt.parse(authorization);
        return user != null && user.isOwnerAdmin() ? user : null;
    }
}
