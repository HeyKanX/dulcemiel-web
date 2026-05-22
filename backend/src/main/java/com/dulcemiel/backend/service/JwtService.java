package com.dulcemiel.backend.service;

import com.dulcemiel.backend.model.AuthUser;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Date;

@Service
public class JwtService {
    private final SecretKey key;
    private final long expirationMs;

    public JwtService(@Value("${app.jwt.secret}") String secret, @Value("${app.jwt.expiration-ms}") long expirationMs) {
        String normalized = secret.length() >= 32 ? secret : secret + "0".repeat(32 - secret.length());
        this.key = Keys.hmacShaKeyFor(normalized.getBytes(StandardCharsets.UTF_8));
        this.expirationMs = expirationMs;
    }

    public String generateToken(Integer userId, String email, String role) {
        Instant now = Instant.now();
        return Jwts.builder()
                .claim("userId", userId)
                .claim("email", email)
                .claim("role", role)
                .issuedAt(Date.from(now))
                .expiration(Date.from(now.plusMillis(expirationMs)))
                .signWith(key)
                .compact();
    }

    public AuthUser parse(String authorizationHeader) {
        if (authorizationHeader == null || !authorizationHeader.startsWith("Bearer ")) {
            return null;
        }
        try {
            var claims = Jwts.parser().verifyWith(key).build()
                    .parseSignedClaims(authorizationHeader.substring(7))
                    .getPayload();
            Number userId = claims.get("userId", Number.class);
            return new AuthUser(userId.intValue(), claims.get("email", String.class), claims.get("role", String.class));
        } catch (Exception ignored) {
            return null;
        }
    }
}
