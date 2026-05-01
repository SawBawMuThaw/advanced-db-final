"""
 pyodbc connection pool for SQL Server (SSMS).
"""
import pyodbc
from pydantic_settings import BaseSettings


class _DBSettings(BaseSettings):
    DB_SERVER: str 
    DB_NAME: str 
    DB_USER: str 
    DB_PASSWORD: str

    class Config:
        env_file = ".env"
        extra = "ignore"


_cfg = _DBSettings()

_CONNECTION_STRING = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    f"SERVER={_cfg.DB_SERVER};"
    f"DATABASE={_cfg.DB_NAME};"
    f"UID={_cfg.DB_USER};"
    f"PWD={_cfg.DB_PASSWORD};"
    "Encrypt=no;"
    "TrustServerCertificate=yes;"
)


def get_connection() -> pyodbc.Connection:
    """Return a new pyodbc connection (caller must close it)."""
    return pyodbc.connect(_CONNECTION_STRING, autocommit=False)