from __future__ import annotations

from typing import Optional

from .db import get_connection


class UserRepository:
    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------
    def create_user(self, username: str, hashed_password: str, email: str) -> int:
        sql = """
            INSERT INTO dbo.Users (username, password, email)
            OUTPUT INSERTED.userID
            VALUES (?, ?, ?)
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, username, hashed_password, email)
            row = cursor.fetchone()
            conn.commit()
            return row[0]

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------
    def get_by_id(self, user_id: int) -> Optional[dict]:
        sql = "SELECT userID, username, email, role FROM dbo.Users WHERE userID = ?"
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, user_id)
            row = cursor.fetchone()
            if row is None:
                return None
            return {
                "userId": row.userID,
                "username": row.username,
                "email": row.email,
                "role": row.role,
            }

    def get_by_username(self, username: str) -> Optional[dict]:
        sql = "SELECT userID, username, password, email, role FROM dbo.Users WHERE username = ?"
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, username)
            row = cursor.fetchone()
            if row is None:
                return None
            return {
                "userId": row.userID,
                "username": row.username,
                "password": row.password,
                "email": row.email,
                "role": row.role,
            }

    def username_exists(self, username: str) -> bool:
        sql = "SELECT 1 FROM dbo.Users WHERE username = ?"
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, username)
            return cursor.fetchone() is not None

    def email_exists(self, email: str) -> bool:
        sql = "SELECT 1 FROM dbo.Users WHERE email = ?"
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, email)
            return cursor.fetchone() is not None