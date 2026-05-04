IF OBJECT_ID('dbo.trg_CreateReceipt', 'TR') IS NOT NULL
    DROP TRIGGER dbo.trg_CreateReceipt;
GO

CREATE TRIGGER dbo.trg_CreateReceipt
ON dbo.Donations
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @taxPercent INT = 10;

    INSERT INTO dbo.Receipts (taxPercent, tax, donationID)
    SELECT
        @taxPercent,
        ROUND(
            (i.amount / (1.0 - @taxPercent / 100.0)) - i.amount,
            2
        ),
        i.donationID
    FROM inserted i
    WHERE i.amount >= 50;  
END;
GO