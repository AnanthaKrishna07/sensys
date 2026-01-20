import os
import time
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash 
from werkzeug.utils import secure_filename 
from bson.objectid import ObjectId

# SENSYS Modular AI Imports
from simulation.bot_engine import BotEngine
from database import DatabaseHandler
from models.text_model import TextAnalyzer
from models.image_model import ImageAnalyzer
from models.video_model import VideoAnalyzer 

# 1. Initialize Flask App
app = Flask(__name__)
CORS(app) 

# 2. Path Configuration
# Pathlib ensures your /uploads folder is found correctly on Windows and Linux
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / 'uploads'

if not UPLOAD_FOLDER.exists():
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

# Define allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'avi', 'mov'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 3. Initialize AI Engines (The 3 Senses)
bot = BotEngine()
db = DatabaseHandler()
text_ai = TextAnalyzer()
image_ai = ImageAnalyzer()
video_ai = VideoAnalyzer() 

# ==========================================
# AUTHENTICATION ROUTES
# ==========================================
@app.route('/api/register', methods=['POST'])
def register_user():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        email = data.get('email', '')

        if db.users_collection.find_one({"username": username}):
            return jsonify({"status": "error", "message": "Username already exists!"}), 400

        hashed_pw = generate_password_hash(password)
        db.users_collection.insert_one({
            "username": username,
            "email": email,
            "password": hashed_pw,
            "role": "user" 
        })
        
        return jsonify({"status": "success", "role": "user", "username": username})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login_user():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')

        user = db.users_collection.find_one({"username": username})
        
        if user and check_password_hash(user['password'], password):
            return jsonify({
                "status": "success", 
                "role": user['role'], 
                "username": user['username']
            })
            
        return jsonify({"status": "error", "message": "Invalid username or password"}), 401
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ==========================================
# USER LIVE UPLOAD ROUTE
# ==========================================
@app.route('/api/user_post', methods=['POST'])
def user_post():
    try:
        # Extract text and user data sent from the React FormData
        text = request.form.get('text', '')
        username = request.form.get('username', 'Anonymous')
        file = request.files.get('file')

        # Create the base post structure with a real, formatted timestamp
        post = {
            "username": username,
            "text": text,
            "timestamp": time.strftime("%b %d, %Y at %I:%M %p"), # <-- UPDATED TO REAL TIME
            "likes": 0,
            "comments": [], # Added empty comments array for new posts
            "media_url": "None",
            "media_type": "text",
            "ai_label": "Neutral",
            "ai_score": 0.0,
            "img_label": "None",
            "img_score": 0.0,
            "detected_emotion": "None",
            "fusion_note": "Unimodal Analysis (Text Only)"
        }

        # Step 1: Text AI Analysis (If text exists)
        if text.strip():
            text_res = text_ai.analyze(text)
            text_id = int(text_res.get('label_id', 1))
            post['ai_label'] = text_res['label']
            post['ai_score'] = float(text_res.get('score', 0.0))
        else:
            text_id = 1 # Neutral fallback if no text provided

        # Media default states
        media_vision_id = 1
        media_audio_id = 1

        # Step 2: Handle File Upload & Vision/Audio AI Analysis
        if file and file.filename != '' and allowed_file(file.filename):
            # Secure the filename and save it locally
            filename = secure_filename(f"{int(time.time())}_{file.filename}")
            filepath = UPLOAD_FOLDER / filename
            file.save(filepath)
            
            post['media_url'] = f"uploads/{filename}"
            ext = filename.rsplit('.', 1)[1].lower()
            
            # Image Analysis
            if ext in {'png', 'jpg', 'jpeg', 'gif'}:
                post['media_type'] = 'image'
                img_res = image_ai.analyze(str(filepath))
                media_vision_id = int(img_res.get('label_id', 1))
                
                post['img_label'] = img_res.get('label', 'Neutral')
                post['img_score'] = float(img_res.get('confidence', 0.0))
                post['detected_emotion'] = img_res.get('detected_emotion', 'neutral')
            
            # Video Analysis
            elif ext in {'mp4', 'avi', 'mov'}:
                post['media_type'] = 'video'
                vid_res = video_ai.analyze(str(filepath))
                
                media_vision_id = int(vid_res['vision']['label_id'])
                media_audio_id = int(vid_res['audio']['label_id'])
                
                post['img_label'] = vid_res['vision']['label']
                post['img_score'] = float(vid_res['vision']['confidence'])
                post['detected_emotion'] = vid_res.get('detected_emotion', 'mixed')

        # Step 3: SENSYS MULTIMODAL FUSION BRAIN
        if text_id == 2 and (media_vision_id == 0 or media_audio_id == 0):
            post['fusion_note'] = "Sarcasm Detected ⚠️ (Happy Words + Negative Tone/Face)"
            post['ai_label'] = "Sarcastic"
        elif text_id == 0 and (media_vision_id == 2 or media_audio_id == 2):
            post['fusion_note'] = "Potential Deception: Positive expression paired with negative words"
        elif file and file.filename != '':
            if text_id == media_vision_id:
                post['fusion_note'] = "Consistent Multimodal Alignment ✅"
            else:
                post['fusion_note'] = "Varying Multi-Sense Sentiment (Mixed Signals)"

        # Step 4: Save to Database
        db.insert_post(post)

        # Convert MongoDB ID to string so frontend can use it immediately for liking/deleting
        if '_id' in post: 
            post['_id'] = str(post['_id'])

        return jsonify({"status": "success", "post": post})

    except Exception as e:
        print(f"🔥 SENSYS Live Post Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# ==========================================
# INTERACTION ROUTES (LIKES, DELETES, COMMENTS)
# ==========================================
@app.route('/api/like/<post_id>', methods=['POST'])
def like_post(post_id):
    try:
        # Finds the post by its exact MongoDB ID and adds 1 to the 'likes' count
        db.posts_collection.update_one({"_id": ObjectId(post_id)}, {"$inc": {"likes": 1}})
        return jsonify({"status": "success", "message": "Post liked!"})
    except Exception as e:
        print(f"🔥 SENSYS Like Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/delete/<post_id>', methods=['DELETE'])
def delete_post(post_id):
    try:
        # Finds the post by its exact MongoDB ID and deletes it permanently
        db.posts_collection.delete_one({"_id": ObjectId(post_id)})
        return jsonify({"status": "success", "message": "Post deleted!"})
    except Exception as e:
        print(f"🔥 SENSYS Delete Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/comment/<post_id>', methods=['POST'])
def add_comment(post_id):
    try:
        data = request.json
        comment = {
            "username": data.get("username", "Anonymous"),
            "text": data.get("text", ""),
            "timestamp": time.strftime("%b %d, %Y at %I:%M %p") # <-- UPDATED TO REAL TIME
        }
        
        # Pushes the new comment into the specific post's 'comments' array in MongoDB
        db.posts_collection.update_one(
            {"_id": ObjectId(post_id)}, 
            {"$push": {"comments": comment}}
        )
        return jsonify({"status": "success", "comment": comment})
    except Exception as e:
        print(f"🔥 SENSYS Comment Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# ==========================================
# SIMULATION & FEED ROUTES
# ==========================================
@app.route('/')
def home():
    return jsonify({
        "project": "SENSYS Max Fusion Engine", 
        "status": "Online",
        "modules": ["BERT-NLP", "Vision-ER", "Audio-ER"]
    })

@app.route('/uploads/<path:filename>')
def serve_media(filename):
    """ Serves media with proper browser compatibility """
    return send_from_directory(str(UPLOAD_FOLDER), filename)

@app.route('/api/simulate', methods=['GET'])
def simulate():
    try:
        post = bot.generate_post()
        
        text_res = text_ai.analyze(post['text'])
        text_id = int(text_res.get('label_id', 1)) 
        post['ai_label'] = text_res['label']
        post['ai_score'] = float(text_res.get('score', 0.0))

        media_vision_id = 1
        media_audio_id = 1
        post['img_label'] = "None"
        post['img_score'] = 0.0
        post['detected_emotion'] = "None"
        post['fusion_note'] = "Unimodal Analysis (Text Only)"
        post['comments'] = [] # Ensure simulated posts have a comments array too
        post['timestamp'] = time.strftime("%b %d, %Y at %I:%M %p") # Updated simulation timestamp too

        if post.get('media_url') and post['media_url'] != "None":
            file_name = post['media_url'].split('/')[-1]
            media_path = UPLOAD_FOLDER / file_name

            if media_path.exists():
                if post['media_type'] == 'image':
                    img_res = image_ai.analyze(str(media_path))
                    media_vision_id = int(img_res.get('label_id', 1))
                    
                    post['img_label'] = img_res.get('label', 'Neutral')
                    post['img_score'] = float(img_res.get('confidence', 0.0))
                    post['detected_emotion'] = img_res.get('detected_emotion', 'neutral')
                    media_audio_id = 1 
                
                elif post['media_type'] == 'video':
                    vid_res = video_ai.analyze(str(media_path))
                    
                    media_vision_id = int(vid_res['vision']['label_id'])
                    media_audio_id = int(vid_res['audio']['label_id'])
                    
                    post['img_label'] = vid_res['vision']['label']
                    post['img_score'] = float(vid_res['vision']['confidence'])
                    post['detected_emotion'] = vid_res.get('detected_emotion', 'mixed')

                if text_id == 2 and (media_vision_id == 0 or media_audio_id == 0):
                    post['fusion_note'] = "Sarcasm Detected ⚠️ (Happy Words + Negative Tone/Face)"
                    post['ai_label'] = "Sarcastic"
                elif text_id == 0 and (media_vision_id == 2 or media_audio_id == 2):
                    post['fusion_note'] = "Potential Deception: Positive expression paired with negative words"
                elif text_id == media_vision_id:
                    post['fusion_note'] = "Consistent Multimodal Alignment ✅"
                else:
                    post['fusion_note'] = "Varying Multi-Sense Sentiment (Mixed Signals)"

        db.insert_post(post)
        
        if '_id' in post: 
            post['_id'] = str(post['_id']) # Convert to string for React
        
        return jsonify({"status": "success", "post": post})

    except Exception as e:
        print(f"🔥 SENSYS Simulation Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/feed', methods=['GET'])
def get_feed():
    """ Returns all historical analyzed posts from the DB """
    try:
        posts = db.fetch_posts()
        for p in posts:
            if '_id' in p: p['_id'] = str(p['_id'])
        return jsonify(posts[::-1]) # Return newest posts first
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/clear', methods=['GET'])
def clear_db():
    """ Wipes the simulation database for a fresh start """
    try:
        db.posts_collection.delete_many({})
        return jsonify({"status": "success", "message": "Simulation database cleared"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🔥 SENSYS MAX FUSION ENGINE STARTED")
    print("   - API URL: http://localhost:5000")
    print("   - Status: Fusion Active (Text + Vision + Audio)")
    print("="*50 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)