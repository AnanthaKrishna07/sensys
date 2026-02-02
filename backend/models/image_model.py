import osa
from deepface import DeepFace

# Disable TensorFlow logging to keep the console clean
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 

class ImageAnalyzer:
    def __init__(self):
        """
        Initializes the DeepFace Emotion Engine.
        """
        print("SENSYS: Initializing Vision-Based Emotion Engine (DeepFace)...")

    def analyze(self, image_path):
        """
        Analyzes a single image with STRICT confidence thresholds.
        """
        # 1. Fallback for missing files
        if not os.path.exists(image_path) or image_path == "None":
            return {
                "label": "Neutral", "label_id": 1, 
                "confidence": 0.0, "detected_emotion": "none"
            }

        try:
            # 2. Perform Emotion Analysis
            # 'ssd' is the best balance of speed and accuracy for CPU
            results = DeepFace.analyze(
                img_path = image_path, 
                actions = ['emotion'],
                enforce_detection = False, 
                detector_backend = 'ssd', 
                silent = True
            )

            if isinstance(results, list):
                result = results[0]
            else:
                result = results

            # 3. Extract Dominant Emotion and Score
            dominant_emotion = result['dominant_emotion']
            # Convert percentage (0-100) to float (0.0-1.0)
            confidence = float(result['emotion'][dominant_emotion] / 100)

            # --- FIX: STRICT SENSYS MAPPING ---
            
            # Logic A: If confidence is too low, don't guess. Stay Neutral.
            # This prevents "Laughing" faces from accidentally triggering "Fear/Disgust"
            if confidence < 0.45:
                return {
                    "label": "Neutral",
                    "label_id": 1,
                    "confidence": round(confidence, 4),
                    "detected_emotion": f"{dominant_emotion} (Low Conf)"
                }

            # Logic B: Refined Pools
            # "Surprise" is moved to Neutral because it is too ambiguous (Good vs Bad surprise)
            
            # High Valence (Positive) - ONLY Happy
            if dominant_emotion == 'happy':
                label = "Positive"
                label_id = 2
            
            # Low Valence (Negative)
            elif dominant_emotion in ['angry', 'disgust', 'fear', 'sad']:
                label = "Negative"
                label_id = 0
            
            # Neutral / Ambiguous (Surprise, Neutral)
            else:
                label = "Neutral"
                label_id = 1

            return {
                "label": label,
                "label_id": label_id,
                "confidence": round(confidence, 4),
                "detected_emotion": dominant_emotion
            }

        except Exception as e:
            print(f"🖼️ Vision AI Error on {image_path}: {e}")
            return {
                "label": "Neutral", "label_id": 1, 
                "confidence": 0.0, "detected_emotion": "error"
            }

# --- TEST BLOCK ---
# This allows you to run 'python models/image_model.py' to test just this file
if __name__ == "__main__":
    analyzer = ImageAnalyzer()
    
    # Auto-find a test image in the uploads folder
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    upload_dir = os.path.join(base_dir, "uploads")
    
    # Try to find the first jpg/png file
    test_files = [f for f in os.listdir(upload_dir) if f.endswith(('.jpg', '.png'))]
    
    if test_files:
        test_path = os.path.join(upload_dir, test_files[0])
        print(f"Testing on: {test_files[0]}")
        print(analyzer.analyze(test_path))
    else:
        print("No test images found in 'uploads' folder.")