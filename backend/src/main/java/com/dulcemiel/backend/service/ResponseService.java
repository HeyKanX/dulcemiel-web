package com.dulcemiel.backend.service;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;

import java.util.LinkedHashMap;
import java.util.Map;

@Service
public class ResponseService {
    public Map<String, Object> body(Object... pairs) {
        Map<String, Object> map = new LinkedHashMap<>();
        for (int i = 0; i < pairs.length; i += 2) {
            map.put(String.valueOf(pairs[i]), pairs[i + 1]);
        }
        return map;
    }

    public ResponseEntity<Map<String, Object>> ok(Object... pairs) {
        return ResponseEntity.ok(body(pairs));
    }

    public ResponseEntity<Map<String, Object>> created(Object... pairs) {
        return ResponseEntity.status(HttpStatus.CREATED).body(body(pairs));
    }

    public ResponseEntity<Map<String, Object>> error(HttpStatus status, String message) {
        return ResponseEntity.status(status).body(body("success", false, "message", message));
    }
}
