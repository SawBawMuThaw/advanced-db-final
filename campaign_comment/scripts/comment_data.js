// Sample comment documents for the 'comments' collection in charitydb
// Uses users from donation_user/scripts/user_data.sql (user1..user9, userIDs 2..10)
db = db.getSiblingDB('charitydb');

const comments = [
  // Top-level comments for campaign 1
  {
    _id: ObjectId("660000000000000000000001"),
    campaignId: ObjectId("650000000000000000000001"),
    parentId: null,
    user: { userId: 2, username: "user1" },
    text: "Great initiative — happy to help!",
    createdAt: new Date("2026-04-02T10:00:00Z")
  },
  {
    _id: ObjectId("660000000000000000000002"),
    campaignId: ObjectId("650000000000000000000001"),
    parentId: null,
    user: { userId: 3, username: "user2" },
    text: "Is there a way to volunteer in addition to donating?",
    createdAt: new Date("2026-04-02T11:15:00Z")
  },
  // Reply to comment 2
  {
    _id: ObjectId("660000000000000000000003"),
    campaignId: ObjectId("650000000000000000000001"),
    parentId: ObjectId("660000000000000000000002"),
    user: { userId: 4, username: "user3" },
    text: "I asked the organizer and they welcome volunteers on weekends.",
    createdAt: new Date("2026-04-02T12:00:00Z")
  },

  // Top-level comments for campaign 2
  {
    _id: ObjectId("660000000000000000000004"),
    campaignId: ObjectId("650000000000000000000002"),
    parentId: null,
    user: { userId: 5, username: "user4" },
    text: "Perfect cause — donated earlier today.",
    createdAt: new Date("2026-03-21T09:00:00Z")
  },
  {
    _id: ObjectId("660000000000000000000005"),
    campaignId: ObjectId("650000000000000000000002"),
    parentId: null,
    user: { userId: 6, username: "user5" },
    text: "Can we get a breakdown of how funds are used?",
    createdAt: new Date("2026-03-21T09:10:00Z")
  },
  // Reply chain for campaign 2
  {
    _id: ObjectId("660000000000000000000006"),
    campaignId: ObjectId("650000000000000000000002"),
    parentId: ObjectId("660000000000000000000005"),
    user: { userId: 7, username: "user6" },
    text: "They posted a short report in the updates section last week.",
    createdAt: new Date("2026-03-21T10:00:00Z")
  },
  {
    _id: ObjectId("660000000000000000000007"),
    campaignId: ObjectId("650000000000000000000002"),
    parentId: ObjectId("660000000000000000000006"),
    user: { userId: 5, username: "user4" },
    text: "Thanks — I see it now.",
    createdAt: new Date("2026-03-21T10:05:00Z")
  },

  // Campaign 3 comments
  {
    _id: ObjectId("660000000000000000000008"),
    campaignId: ObjectId("650000000000000000000003"),
    parentId: null,
    user: { userId: 8, username: "user7" },
    text: "Any medical professionals involved?",
    createdAt: new Date("2026-02-11T08:30:00Z")
  },
  {
    _id: ObjectId("660000000000000000000009"),
    campaignId: ObjectId("650000000000000000000003"),
    parentId: ObjectId("660000000000000000000008"),
    user: { userId: 9, username: "user8" },
    text: "I know a nurse who offered to help — putting you in touch.",
    createdAt: new Date("2026-02-11T09:00:00Z")
  },

  // Campaign 4 comments
  {
    _id: ObjectId("66000000000000000000000A"),
    campaignId: ObjectId("650000000000000000000004"),
    parentId: null,
    user: { userId: 10, username: "user9" },
    text: "Amazing progress — congrats to the team!",
    createdAt: new Date("2025-12-06T14:20:00Z")
  },
  {
    _id: ObjectId("66000000000000000000000B"),
    campaignId: ObjectId("650000000000000000000004"),
    parentId: null,
    user: { userId: 2, username: "user1" },
    text: "Is the project fully funded now?",
    createdAt: new Date("2025-12-06T15:00:00Z")
  },
  {
    _id: ObjectId("66000000000000000000000C"),
    campaignId: ObjectId("650000000000000000000004"),
    parentId: ObjectId("66000000000000000000000B"),
    user: { userId: 5, username: "user4" },
    text: "They reached their goal and have started installation.",
    createdAt: new Date("2025-12-07T08:00:00Z")
  },

  // Campaign 5 single comment
  {
    _id: ObjectId("66000000000000000000000D"),
    campaignId: ObjectId("650000000000000000000005"),
    parentId: null,
    user: { userId: 6, username: "user5" },
    text: "Looking forward to seeing the new books in the library.",
    createdAt: new Date("2026-04-16T10:10:00Z")
  }
];

db.comments.insertMany(comments);
print('Inserted ' + comments.length + ' sample comments into comments collection.');
