import random
import datetime
abc
class BotEngine:
    def __init__(self):
        # Sample users for the simulation
        self.users = ["TechExplorer", "CriticalMind", "NeutralObserver", "HappyTraveler", "DataWizard"]
        
        # Templates for generating random text with associated ground truth sentiment
        self.templates = [
            {"text": "This is the best product in the market! Highly recommend.", "sentiment": "Positive"},
            {"text": "Absolutely love the new features in this update.", "sentiment": "Positive"},
            {"text": "Extremely disappointed with the service. Waste of money.", "sentiment": "Negative"},
            {"text": "The quality has dropped significantly lately. Very sad.", "sentiment": "Negative"},
            {"text": "Is this available in blue? Just curious.", "sentiment": "Neutral"},
            {"text": "The delivery was on time, but the packaging was okay.", "sentiment": "Neutral"},
            {"text": "Testing out the new SENSYS multimodal platform today!", "sentiment": "Positive"}
        ]

    def generate_post(self):
        """
        Generates a random social media post containing text and occasionally an image.
        """
        user = random.choice(self.users)
        template = random.choice(self.templates)
        
        # Randomly decide if the post is just text or has an image
        # 60% chance of being an image post to help test your new model
        media_type = random.choices(["text", "image"], weights=[40, 60])[0]
        
        post = {
            "post_id": hex(random.getrandbits(32))[2:],
            "username": user,
            "text": template["text"],
            "ground_truth": template["sentiment"],
            "media_type": media_type,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "likes": random.randint(5, 500)
        }

        # If it's an image post, link it to one of the 5 local sample images
        if media_type == "image":
            # This generates a number between 1 and 5
            img_num = random.randint(1, 5)
            
            # The path stored in the database for the frontend to use
            # React will call: http://127.0.0.1:5000/uploads/sample_image_X.jpg
            post["media_url"] = f"uploads/sample_image_{img_num}.jpg"
        else:
            post["media_url"] = None
        
        return post

# Quick test to verify output
if __name__ == "__main__":
    bot = BotEngine()
    print(bot.generate_post())