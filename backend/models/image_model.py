import os
from deepface import DeepFace
import logging
# Disable TensorFlow logging to keep the console clean and focused on AI results
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 

class ImageAnalyzer:
    def __init__(self):
        """
        Initializes the DeepFace Emotion Engine (FER Architecture).
        """
        print("Initializing DeepFace Emotion Engine (FER Architecture)...")

    def analyze(self, image_path):
        """
        Analyzes a single image file and returns a sentiment label based on facial/emoji expressions.
        """
        try:
            # Check if the physical file exists at the provided path
            if not os.path.exists(image_path):
                print(f"File not found: {image_path}")
                return {"label": "Neutral", "confidence": 0.5}

            # Perform emotion analysis using the OpenCV backend (best for emojis)
            results = DeepFace.analyze(
                img_path = image_path, 
                actions = ['emotion'],
                enforce_detection = False, 
                detector_backend = 'opencv'
            )

            # Extract dominant emotion
            dominant_emotion = results[0]['dominant_emotion']
            
            # CRITICAL FIX: Explicitly convert from NumPy float to Python float
            confidence = float(results[0]['emotion'][dominant_emotion] / 100)

            # --- UPDATED MAPPING LOGIC FOR NEUTRAL ACCURACY ---
            negative_emotions = ['angry', 'disgust', 'fear', 'sad']
            positive_emotions = ['happy', 'surprise']

            # Explicit check for the 'neutral' category first
            if dominant_emotion == "neutral":
                label = "Neutral"
            elif dominant_emotion in negative_emotions:
                label = "Negative"
            elif dominant_emotion in positive_emotions:
                label = "Positive"
            else:
                label = "Neutral"

            return {
                "label": label, 
                "confidence": confidence,
                "detected_emotion": dominant_emotion
            }

        except Exception as e:
            print(f"DeepFace Analysis Error: {e}")
            return {"label": "Neutral", "confidence": 0.5}

if __name__ == "__main__":
    analyzer = ImageAnalyzer()
    test_path = "../uploads/sample_image_1.jpg"
    print(f"Test Result: {analyzer.analyze(test_path)}")