"""Configuración compartida; impide escrituras fuera de la instancia local de auditoría."""
import os
from urllib.parse import urlparse


def local_url(name: str, default: str) -> str:
    value = os.getenv(name, default).rstrip("/")
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or parsed.hostname not in ("localhost", "127.0.0.1"):
        raise RuntimeError(f"{name} debe apuntar a localhost o 127.0.0.1")
    return value


WEB_URL = local_url("QA_WEB_URL", "http://127.0.0.1:4200")
API_URL = local_url("QA_API_URL", "http://127.0.0.1:5000/api")


def require_isolated_db() -> None:
    if os.getenv("QA_ISOLATED_DB") != "1":
        raise RuntimeError("Las pruebas que escriben datos requieren QA_ISOLATED_DB=1 y SQL aislado")
