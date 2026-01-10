import os
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
abc
# Import custom modules
from simulation.bot_engine import BotEngine
from database import DatabaseHandler
from models.text_model import TextAnalyzer
from models.image_model import ImageAnalyzer

# 1. Initialize Flask App
app = Flask(__name__)

# 2. Enable CORS
CORS(app)

# 3. Path Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 4. Initialize AI Engines & Handlers
bot = BotEngine()
db = DatabaseHandler()
text_ai = TextAnalyzer()
image_ai = ImageAnalyzer()

# --- ROUTES ---

@app.route('/')
def home():
    return jsonify({
        "project": "SENSYS - Advanced Multimodal Sentiment Analysis",
        "status": "Backend Online"
    })

@app.route('/uploads/<path:filename>')
def serve_media(filename):
    """Serves physical images to the React Frontend."""
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/api/simulate', methods=['GET'])
def simulate():
    """
    Main AI Pipeline:
    1. BERT analyzes Text.
    2. DeepFace analyzes Image Emotion.
    3. NumPy values are converted to Python floats for MongoDB compatibility.
    """
    try:
        # A. Generate mock post
        post = bot.generate_post()
        
        # B. Text Analysis (BERT Engine)
        text_results = text_ai.analyze(post['text'])
        post['ai_label'] = text_results['label']
        
        # CRITICAL FIX: Convert np.float32 to standard python float
        post['ai_score'] = float(text_results['score'])
        
        # C. Image Analysis (DeepFace Engine)
        if post['media_type'] == 'image' and post['media_url']:
            file_name = post['media_url'].split('/')[-1]
            img_physical_path = os.path.join(UPLOAD_FOLDER, file_name)
            
            img_results = image_ai.analyze(img_physical_path)
            post['img_label'] = img_results['label']
            
            # CRITICAL FIX: Convert np.float32 to standard python float
            post['img_score'] = float(img_results['confidence'])
            post['detected_emotion'] = img_results.get('detected_emotion', 'neutral')
            
            # --- MULTIMODAL FUSION LOGIC ---
            if post['ai_label'] != post['img_label']:
                post['fusion_note'] = f"Conflict: Text is {post['ai_label']} but Image is {post['detected_emotion']}"
            else:
                post['fusion_note'] = "Consistent Multimodal Sentiment"
        
        # D. Save to MongoDB (This will no longer fail with the float conversion)
        db.insert_post(post)
        
        # E. Clean for JSON response
        if '_id' in post:
            del post['_id']
            
        return jsonify({"status": "success", "post": post})

    except Exception as e:
        print(f"Server Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/feed', methods=['GET'])
def get_feed():
    """Fetches analyzed posts in reverse order."""
    try:
        posts = db.fetch_posts()
        for p in posts:
            if '_id' in p:
                p['_id'] = str(p['_id'])
        return jsonify(posts[::-1])
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/clear', methods=['GET'])
def clear_db():
    """Wipes the database for fresh demonstrations."""
    db.posts_collection.delete_many({})
    return jsonify({"status": "success", "message": "Database cleared"})

if __name__ == '__main__':
    print("\n[INIT] SENSYS Backend Running...")
    app.run(debug=True, port=5000)