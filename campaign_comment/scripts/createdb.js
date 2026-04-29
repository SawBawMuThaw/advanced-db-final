// 1. Switch to (or create) the 'charitydb' database
db = db.getSiblingDB('charitydb');

// 2. Create the 'campaigns' collection
// This is optional if you're just going to insert data, 
// but useful if you want to specify validation or options.
db.createCollection('campaigns');

console.log("Database 'charitydb' and collection 'campaigns' initialized.");