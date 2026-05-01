-- ============================================================
-- schema.sql  –  donation_user service  (SSMS / SQL Server)
-- ============================================================

-- Drop tables in dependency order (child → parent)
IF OBJECT_ID('dbo.Receipts',  'U') IS NOT NULL DROP TABLE dbo.Receipts;
IF OBJECT_ID('dbo.Donations', 'U') IS NOT NULL DROP TABLE dbo.Donations;
IF OBJECT_ID('dbo.Users',     'U') IS NOT NULL DROP TABLE dbo.Users;

-- ------------------------------------------------------------
-- Users
-- ------------------------------------------------------------
CREATE TABLE dbo.Users (
    userID   INT           IDENTITY(1,1) PRIMARY KEY,
    username VARCHAR(100)  NOT NULL UNIQUE,
    password VARCHAR(255)  NOT NULL,          -- bcrypt hash
    email    VARCHAR(255)  NOT NULL UNIQUE,
    role     VARCHAR(50)   NOT NULL DEFAULT 'user'
);

-- ------------------------------------------------------------
-- Donations
-- ------------------------------------------------------------
CREATE TABLE dbo.Donations (
    donationID  INT            IDENTITY(1,1) PRIMARY KEY,
    userID      INT            NOT NULL,
    campaignID  VARCHAR(255)   NOT NULL,       -- MongoDB ObjectId stored as string
    amount      DECIMAL(10,2)  NOT NULL CHECK (amount >= 0),
    time        DATETIME       NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_Donations_Users FOREIGN KEY (userID)
        REFERENCES dbo.Users(userID)
        ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- Receipts  (one receipt per donation – created by trigger)
-- ------------------------------------------------------------
CREATE TABLE dbo.Receipts (
    receiptID    INT            IDENTITY(1,1) PRIMARY KEY,
    taxPercent   INT            NOT NULL DEFAULT 10,   -- percent
    tax          DECIMAL(10,2)  NOT NULL,
    donationID   INT            NOT NULL UNIQUE,
    CONSTRAINT FK_Receipts_Donations FOREIGN KEY (donationID)
        REFERENCES dbo.Donations(donationID)
        ON DELETE CASCADE
);