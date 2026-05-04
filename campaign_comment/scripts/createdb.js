// 1. Switch to (or create) the 'charitydb' database
db = db.getSiblingDB('charitydb');

// 2. Create the 'campaigns' collection
// This is optional if you're just going to insert data, 
// but useful if you want to specify validation or options.
db.createCollection('campaigns');
db.createCollection('comments');

db.campaigns.createIndex({'info.title' : 1})
db.campaigns.createIndex({'info.ownerId' : 1})
db.comments.createIndex({'campaignId' : 1})
db.comments.createIndex({'userId' : 1})

console.log("Database 'charitydb' and collection 'campaigns' initialized.");

// Insert 5 sample campaigns (owners use users from donation_user/scripts/user_data.sql excluding 'admin')
const sampleCampaigns = [
	{
		_id: ObjectId("650000000000000000000001"),
		goal: 5000.00,
		current: 481.43,
		available: 0,
		isOpen: true,
		info: {
			title: "Clean Water Project - Village A",
			owner: { userId: 2, username: "user1" },
			description: "Provide wells and filtration systems to Village A.",
			videolink: "https://www.youtube.com/watch?v=EngW7tLk6R8",
			likes: 12,
			likedBy: [3,4],
			created: new Date("2026-04-01T12:00:00Z")
		},
		reports: []
	},
	{
		_id: ObjectId("650000000000000000000002"),
		goal: 12000.00,
		current: 277.40,
		available: 0,
		isOpen: true,
		info: {
			title: "School Supplies for Children",
			owner: { userId: 3, username: "user2" },
			description: "Buy books, uniforms and stationery for local school children.",
			videolink: "https://www.youtube.com/watch?v=EngW7tLk6R8",
			likes: 34,
			likedBy: [2,5,6],
			created: new Date("2026-03-20T09:30:00Z")
		},
		reports: []
	},
	{
		_id: ObjectId("650000000000000000000003"),
		goal: 8000.00,
		current: 593.38,
		available: 0,
		isOpen: true,
		info: {
			title: "Community Health Clinic",
			owner: { userId: 4, username: "user3" },
			description: "Support a pop-up clinic to provide basic healthcare services.",
			videolink: "https://www.youtube.com/watch?v=EngW7tLk6R8",
			likes: 5,
			likedBy: [],
			created: new Date("2026-02-10T15:45:00Z")
		},
		reports: []
	},
	{
		_id: ObjectId("650000000000000000000004"),
		goal: 15000.00,
		current: 820.04,
		available: 0,
		isOpen: false,
		info: {
			title: "Solar Power for Community Center",
			owner: { userId: 5, username: "user4" },
			description: "Install solar panels to provide reliable electricity.",
			videolink: "https://www.youtube.com/watch?v=EngW7tLk6R8",
			likes: 78,
			likedBy: [2,3,4,6],
			created: new Date("2025-12-05T08:00:00Z")
		},
		reports: []
	},
	{
		_id: ObjectId("650000000000000000000005"),
		goal: 3000.00,
		current: 886.40,
		available: 0,
		isOpen: true,
		info: {
			title: "Books for the Youth Library",
			owner: { userId: 6, username: "user5" },
			description: "Expand the youth library with age-appropriate books.",
			videolink: "https://www.youtube.com/watch?v=EngW7tLk6R8",
			likes: 2,
			likedBy: [],
			created: new Date("2026-04-15T11:20:00Z")
		},
		reports: []
	}
];

db.campaigns.insertMany(sampleCampaigns);
console.log("Inserted 5 sample campaigns into 'campaigns' collection.");

