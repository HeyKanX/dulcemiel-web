package com.dulcemiel.backend.service;

import jakarta.servlet.http.HttpServletRequest;
import org.springframework.stereotype.Service;
import org.springframework.web.servlet.support.ServletUriComponentsBuilder;

import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.Map;

@Service
public class ImageUrlService {
    public Map<String, Object> product(HttpServletRequest request, Map<String, Object> row) {
        return image(request, row, "tiene_imagen", "producto", "imagen_url");
    }

    public Map<String, Object> carousel(HttpServletRequest request, Map<String, Object> row) {
        return image(request, row, "tiene_imagen", "carrusel", "imagen_url");
    }

    public Map<String, Object> siteSettings(HttpServletRequest request, Map<String, Object> row) {
        if (row == null) {
            return null;
        }
        return image(request, row, "tiene_logo", "logo", "logo_url");
    }

    private Map<String, Object> image(HttpServletRequest request, Map<String, Object> row, String flag, String tipo, String urlKey) {
        Map<String, Object> mapped = new LinkedHashMap<>(row);
        Object value = row.get(flag);
        boolean hasImage = Boolean.TRUE.equals(value) || "true".equalsIgnoreCase(String.valueOf(value)) || "1".equals(String.valueOf(value));
        mapped.put(urlKey, hasImage ? baseUrl(request) + "/api/imagenes/" + tipo + "/" + row.get("id") + version(row) : null);
        return mapped;
    }

    private String version(Map<String, Object> row) {
        Object version = row.get("fecha_actualizacion");
        if (version == null) {
            version = row.get("fecha_creacion");
        }
        if (version == null) {
            return "";
        }
        return "?v=" + URLEncoder.encode(String.valueOf(version), StandardCharsets.UTF_8);
    }

    private String baseUrl(HttpServletRequest request) {
        return ServletUriComponentsBuilder.fromCurrentContextPath().build().toUriString();
    }
}
