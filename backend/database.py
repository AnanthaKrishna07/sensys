from pymongo import MongoClient

class DatabaseHandler:
    def __init__(self):
        # Connects to your local MongoDB
        self.client = MongoClient("mongodb://localhost:27017/")
        self.db = self.client['sensys_db']
        self.posts_collection = self.db['posts']

    def insert_post(self, post_data):
        self.posts_collection.insert_one(post_data)

    def fetch_posts(self):
        # Return all posts, excluding the MongoDB _id for JSON compatibility
        return list(self.posts_collection.find({}, {"_id": 0}))