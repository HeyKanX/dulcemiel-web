package com.dulcemiel.backend.controller;

import com.dulcemiel.backend.service.ResponseService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.Instant;
import java.util.Map;

@RestController
public class HealthController {
    private final ResponseService responses;

    public HealthController(ResponseService responses) {
        this.responses = responses;
    }

    @GetMapping("/api/health")
    Map<String, Object> health() {
        return responses.body("success", true, "message", "Servidor funcionando correctamente", "timestamp", Instant.now().toString());
    }
}
