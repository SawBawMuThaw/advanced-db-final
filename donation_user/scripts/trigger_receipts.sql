-- ============================================================
-- trigger_receipts.sql
-- Auto-creates a Receipt row every time a Donation is inserted.
-- tax = gross_payment - net_amount
--   gross = amount / (1 - taxPercent/100)
-- ============================================================

IF OBJECT_ID('dbo.trg_CreateReceipt', 'TR') IS NOT NULL
    DROP TRIGGER dbo.trg_CreateReceipt;
GO

CREATE TRIGGER dbo.trg_CreateReceipt
ON dbo.Donations
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @taxPercent INT = 10;   -- default 10 %

    INSERT INTO dbo.Receipts (taxPercent, tax, donationID)
    SELECT
        @taxPercent,
        -- gross = net / (1 - rate);  tax = gross - net
        ROUND(
            (i.amount / (1.0 - @taxPercent / 100.0)) - i.amount,
            2
        ),
        i.donationID
    FROM inserted i;
END;
GO