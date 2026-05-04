"""
pyodbc connection helper for SQL Server (SSMS).
"""
import pyodbc
from pydantic_settings import BaseSettings


class _DBSettings(BaseSettings):
    DB_SERVER: str = "localhost"
    DB_NAME: str = "donation_db"
    DB_USER: str | None = None
    DB_PASSWORD: str | None = None
    DB_DRIVER: str = "ODBC Driver 17 for SQL Server"
    DB_TRUSTED_CONNECTION: bool = False
    DB_ENCRYPT: str = "no"
    DB_TRUST_SERVER_CERTIFICATE: str = "yes"

    class Config:
        env_file = "donation_user/.env"
        extra = "ignore"


_cfg = _DBSettings()


def _available_driver() -> str:
    drivers = pyodbc.drivers()
    if _cfg.DB_DRIVER in drivers:
        return _cfg.DB_DRIVER

    for candidate in ("ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server", "SQL Server"):
        if candidate in drivers:
            return candidate

    return _cfg.DB_DRIVER


def _server_candidates() -> list[str]:
    server = _cfg.DB_SERVER.strip()
    candidates = [server]

    # MSSQLSERVER is the default SQL Server instance name. Client connection
    # strings normally use just the machine name for that instance.
    if server.upper().endswith("\\MSSQLSERVER"):
        candidates.append(server.rsplit("\\", 1)[0])

    seen = set()
    result = []
    for candidate in candidates:
        key = candidate.lower()
        if key not in seen:
            seen.add(key)
            result.append(candidate)
    return result


def _connection_string(server: str) -> str:
    parts = [
        f"DRIVER={{{_available_driver()}}}",
        f"SERVER={server}",
        f"DATABASE={_cfg.DB_NAME}",
        f"Encrypt={_cfg.DB_ENCRYPT}",
        f"TrustServerCertificate={_cfg.DB_TRUST_SERVER_CERTIFICATE}",
    ]

    if _cfg.DB_TRUSTED_CONNECTION or not (_cfg.DB_USER and _cfg.DB_PASSWORD):
        parts.append("Trusted_Connection=yes")
    else:
        parts.append(f"UID={_cfg.DB_USER}")
        parts.append(f"PWD={_cfg.DB_PASSWORD}")

    return ";".join(parts) + ";"


def get_connection() -> pyodbc.Connection:
    """Return a new pyodbc connection (caller must close it)."""
    errors = []

    for server in _server_candidates():
        try:
            return pyodbc.connect(
                _connection_string(server),
                autocommit=False,
                timeout=5,
            )
        except pyodbc.Error as exc:
            errors.append(f"{server}: {exc}")

    raise RuntimeError(
        "Could not connect to SQL Server. "
        f"Tried server(s): {', '.join(_server_candidates())}. "
        f"Last error: {errors[-1] if errors else 'unknown'}"
    )
