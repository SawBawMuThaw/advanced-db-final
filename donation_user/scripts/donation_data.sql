-- 30 sample donations using users from user_data.sql (exclude 'admin')
-- Assumes Users were inserted in order so userIDs 2..10 correspond to user1..user9
-- campaignID values are Mongo ObjectId strings for sample campaigns

INSERT INTO dbo.Donations (userID, campaignID, amount) VALUES (2, '650000000000000000000001', 45.00);
INSERT INTO dbo.Donations (userID, campaignID, amount) VALUES (3, '650000000000000000000002', 120.50);
INSERT INTO dbo.Donations (userID, campaignID, amount) VALUES (4, '650000000000000000000003', 7.25);
INSERT INTO dbo.Donations (userID, campaignID, amount) VALUES (5, '650000000000000000000004', 300.00);
INSERT INTO dbo.Donations (userID, campaignID, amount) VALUES (6, '650000000000000000000005', 15.75);
INSERT INTO dbo.Donations (userID, campaignID, amount) VALUES (7, '650000000000000000000001', 50.00);
INSERT INTO dbo.Donations (userID, campaignID, amount) VALUES (8, '650000000000000000000002', 9.99);
INSERT INTO dbo.Donations (userID, campaignID, amount) VALUES (9, '650000000000000000000003', 250.00);
INSERT INTO dbo.Donations (userID, campaignID, amount) VALUES (10, '650000000000000000000004', 3.00);
INSERT INTO dbo.Donations (userID, campaignID, amount) VALUES (2, '650000000000000000000005', 88.88);

INSERT INTO dbo.Donations (userID, campaignID, amount) VALUES (3, '650000000000000000000001', 42.00);
INSERT INTO dbo.Donations (userID, campaignID, amount) VALUES (4, '650000000000000000000002', 19.50);
INSERT INTO dbo.Donations (userID, campaignID, amount) VALUES (5, '650000000000000000000003', 5.00);
INSERT INTO dbo.Donations (userID, campaignID, amount) VALUES (6, '650000000000000000000004', 499.99);
INSERT INTO dbo.Donations (userID, campaignID, amount) VALUES (7, '650000000000000000000005', 25.00);
INSERT INTO dbo.Donations (userID, campaignID, amount) VALUES (8, '650000000000000000000001', 100.00);
INSERT INTO dbo.Donations (userID, campaignID, amount) VALUES (9, '650000000000000000000002', 37.30);
INSERT INTO dbo.Donations (userID, campaignID, amount) VALUES (10, '650000000000000000000003', 13.13);
INSERT INTO dbo.Donations (userID, campaignID, amount) VALUES (2, '650000000000000000000004', 7.00);
INSERT INTO dbo.Donations (userID, campaignID, amount) VALUES (3, '650000000000000000000005', 250.00);

INSERT INTO dbo.Donations (userID, campaignID, amount) VALUES (4, '650000000000000000000001', 44.44);
INSERT INTO dbo.Donations (userID, campaignID, amount) VALUES (5, '650000000000000000000002', 66.66);
INSERT INTO dbo.Donations (userID, campaignID, amount) VALUES (6, '650000000000000000000003', 18.00);
INSERT INTO dbo.Donations (userID, campaignID, amount) VALUES (7, '650000000000000000000004', 5.55);
INSERT INTO dbo.Donations (userID, campaignID, amount) VALUES (8, '650000000000000000000005', 7.77);
INSERT INTO dbo.Donations (userID, campaignID, amount) VALUES (9, '650000000000000000000001', 199.99);
INSERT INTO dbo.Donations (userID, campaignID, amount) VALUES (10, '650000000000000000000002', 23.45);
INSERT INTO dbo.Donations (userID, campaignID, amount) VALUES (2, '650000000000000000000003', 300.00);
INSERT INTO dbo.Donations (userID, campaignID, amount) VALUES (3, '650000000000000000000004', 4.50);
INSERT INTO dbo.Donations (userID, campaignID, amount) VALUES (4, '650000000000000000000005', 499.00);

