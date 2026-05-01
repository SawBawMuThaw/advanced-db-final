from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from .db import get_connection


class DonationRepository:

    def create_donation(
        self,
        user_id: int,
        campaign_id: str,
        amount: Decimal,
        time: datetime,
    ) -> int:
    
        if time.tzinfo is not None:
            time = time.replace(tzinfo=None)
    
        sql_insert = """
            INSERT INTO dbo.Donations (userID, campaignID, amount, [time])
            VALUES (?, ?, ?, ?);
        """
    
        sql_get_id = """
            SELECT TOP 1 donationID
            FROM dbo.Donations
            ORDER BY donationID DESC;
        """
    
        with get_connection() as conn:
            cursor = conn.cursor()
    
            try:
                print("EXECUTING SQL:", user_id, campaign_id, amount, time)
    
                # Step 1: insert
                cursor.execute(sql_insert, user_id, campaign_id, amount, time)
                conn.commit()
    
                # Step 2: get ID
                cursor.execute(sql_get_id)
                row = cursor.fetchone()
    
                if not row:
                    raise Exception("Failed to retrieve donationID")
    
                return int(row[0])
    
            except Exception as e:
                print("SQL ERROR:", repr(e))
                conn.rollback()
                raise


    def delete_donation(self, donation_id: int) -> None:
        sql = "DELETE FROM dbo.Donations WHERE donationID = ?"

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, donation_id)
            conn.commit()


    def get_by_campaign(self, campaign_id: str) -> list[dict]:
        sql = """
            SELECT u.username, d.amount, d.time
            FROM dbo.Donations d
            JOIN dbo.Users u ON u.userID = d.userID
            WHERE d.campaignID = ?
            ORDER BY d.time DESC
        """

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, campaign_id)
            rows = cursor.fetchall()

            return [
                {
                    "username": r.username,
                    "amount": r.amount,
                    "time": r.time
                }
                for r in rows
            ]


    def get_by_id(self, donation_id: int) -> Optional[dict]:
        sql = """
            SELECT donationID, userID, campaignID, amount, time
            FROM dbo.Donations
            WHERE donationID = ?
        """

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, donation_id)
            row = cursor.fetchone()

            if row is None:
                return None

            return {
                "donationId": row.donationID,
                "userId": row.userID,
                "campaignId": row.campaignID,
                "amount": row.amount,
                "time": row.time,
            }