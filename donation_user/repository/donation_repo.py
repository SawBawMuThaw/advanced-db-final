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
                donation_id = int(row[0]) 
                
                #Check whether Trigger generaed and receipt was created
                cursor.execute(
                    "SELECT receiptID, tax FROM dbo.Receipts WHERE donationID = ?", donation_id
                )
                receipt_row = cursor.fetchone()
    
                if not row:
                    raise Exception("Failed to retrieve donationID")
    
                return {
                    "donationId": donation_id,
                    "receiptGenerated": receipt_row is not None,
                    "receiptId": receipt_row.receiptID if receipt_row else None,
                    "tax": receipt_row.tax if receipt_row else None,
                }
    
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
            
            
    def get_receipt_by_donation(self, donation_id: int) -> Optional[dict]:
        sql = """
            SELECT receiptID, taxPercent, tax, donationID
            FROM dbo.Receipts
            WHERE donationID = ?
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, donation_id)
            row = cursor.fetchone()
    
            if row is None:
                return None
    
            return {
                "receiptId": row.receiptID,
                "taxPercent": row.taxPercent,
                "tax": row.tax,
                "donationId": row.donationID,
            }
            
            
    def get_running_total(self, campaign_id: str) -> list[dict]:
        sql = """
            SELECT
                d.campaignID,
                d.donationID,
                u.username,
                d.amount,
                d.time,
                SUM(d.amount) OVER (
                    PARTITION BY d.campaignID
                    ORDER BY d.time
                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                ) AS runningTotal
            FROM dbo.Donations d
            JOIN dbo.Users u ON u.userID = d.userID
            WHERE d.campaignID = ?
            ORDER BY d.time ASC;
        """
    
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, campaign_id)
            rows = cursor.fetchall()
    
            return [
                {
                    "donationId": row.donationID,
                    "username": row.username,
                    "amount": float(row.amount),
                    "time": row.time,
                    "runningTotal": float(row.runningTotal),
                }
                for row in rows
            ]