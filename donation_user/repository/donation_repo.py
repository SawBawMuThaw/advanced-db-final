# from __future__ import annotations

# from datetime import datetime
# from decimal import Decimal
# from typing import Optional

# from .db import get_connection


# class DonationRepository:

#     def create_donation(
#         self,
#         user_id: int,
#         campaign_id: str,
#         amount: Decimal,
#         time: datetime,
#     ) -> int:
#         """
#         Insert a Donation row and return the new donationID.
#         Uses OUTPUT INTO a temp table to avoid the SQL Server restriction:
#         'table with triggers cannot use OUTPUT clause without INTO clause'.
#         """
#         sql = """
#             DECLARE @ids TABLE (donationID INT);
#             INSERT INTO dbo.Donations (userID, campaignID, amount, time)
#             OUTPUT INSERTED.donationID INTO @ids
#             VALUES (?, ?, ?, ?);
#             SELECT donationID FROM @ids;
#         """
#         with get_connection() as conn:
#             cursor = conn.cursor()
#             cursor.execute(sql, user_id, campaign_id, amount, time)
#             row = cursor.fetchone()
#             conn.commit()
#             return row[0]

#     def delete_donation(self, donation_id: int) -> None:
#         """Saga rollback – CASCADE removes the Receipt too."""
#         sql = "DELETE FROM dbo.Donations WHERE donationID = ?"
#         with get_connection() as conn:
#             cursor = conn.cursor()
#             cursor.execute(sql, donation_id)
#             conn.commit()

#     def get_by_campaign(self, campaign_id: str) -> list[dict]:
#         """Return all donors and their net donation amounts for a campaign."""
#         sql = """
#             SELECT u.username, d.amount, d.time
#             FROM   dbo.Donations d
#             JOIN   dbo.Users u ON u.userID = d.userID
#             WHERE  d.campaignID = ?
#             ORDER  BY d.time DESC
#         """
#         with get_connection() as conn:
#             cursor = conn.cursor()
#             cursor.execute(sql, campaign_id)
#             rows = cursor.fetchall()
#             return [
#                 {"username": r.username, "amount": r.amount, "time": r.time}
#                 for r in rows
#             ]

#     def get_by_id(self, donation_id: int) -> Optional[dict]:
#         sql = """
#             SELECT donationID, userID, campaignID, amount, time
#             FROM   dbo.Donations
#             WHERE  donationID = ?
#         """
#         with get_connection() as conn:
#             cursor = conn.cursor()
#             cursor.execute(sql, donation_id)
#             row = cursor.fetchone()
#             if row is None:
#                 return None
#             return {
#                 "donationId": row.donationID,
#                 "userId": row.userID,
#                 "campaignId": row.campaignID,
#                 "amount": row.amount,
#                 "time": row.time,
#             }