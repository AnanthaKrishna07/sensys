import os
import cv2
# UPDATED: Compatible with MoviePy v2.0+
from moviepy import VideoFileClip 
from models.image_model import ImageAnalyzer
from models.audio_model import AudioAnalyzer

class VideoAnalyzer:
    def __init__(self):
        """
        Initializes the Video Pipeline with Vision and Audio specialists.
        """
        self.image_ai = ImageAnalyzer()
        self.audio_ai = AudioAnalyzer()

    def analyze(self, video_path):
        """
        Performs Max Fusion: Extracts and analyzes both Vision and Audio signals.
        Returns a dictionary containing separate results for each modality.
        """
        results = {
            "vision": {"label": "Neutral", "label_id": 1, "confidence": 0.0},
            "audio": {"label": "Neutral", "label_id": 1, "score": 0.0},
            "detected_emotion": "neutral"
        }

        if not os.path.exists(video_path):
            print(f"❌ Video file not found: {video_path}")
            return results

        # Construct a unique temp filename to avoid conflicts
        base_name = os.path.basename(video_path)
        temp_audio = f"temp_audio_{base_name}.wav"
        temp_frame = f"temp_frame_{base_name}.jpg"

        # --- STEP 1: AUDIO EXTRACTION & ANALYSIS ---
        try:
            # Context manager ensures the file is closed automatically
            with VideoFileClip(video_path) as video_clip:
                if video_clip.audio is not None:
                    # Exporting as 16kHz Mono (Standard for Wav2Vec2)
                    video_clip.audio.write_audiofile(
                        temp_audio, 
                        fps=16000, 
                        nbytes=2, 
                        codec='pcm_s16le', 
                        logger=None
                    )
                    # Run Analysis
                    results["audio"] = self.audio_ai.analyze(temp_audio)
                else:
                    print("ℹ️ Video has no audio track, skipping audio analysis.")
        
        except Exception as e:
            print(f"🔊 Audio Extraction Error: {e}")
        
        finally:
            # Cleanup audio file immediately
            if os.path.exists(temp_audio):
                try:
                    os.remove(temp_audio)
                except PermissionError:
                    pass # File might still be briefly locked by OS

        # --- STEP 2: VISION (FRAME) EXTRACTION & ANALYSIS ---
        try:
            cap = cv2.VideoCapture(video_path)
            
            # Strategy: Capture at ~1.5 seconds mark for a natural expression
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps <= 0: fps = 30 # Fallback
            
            target_frame = int(fps * 1.5)
            cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
            
            success, frame = cap.read()
            if success:
                cv2.imwrite(temp_frame, frame)
                
                # Run Vision Analysis
                vision_res = self.image_ai.analyze(temp_frame)
                results["vision"] = vision_res
                results["detected_emotion"] = vision_res.get("detected_emotion", "neutral")
                
                # Cleanup frame file
                if os.path.exists(temp_frame): 
                    os.remove(temp_frame)
            
            cap.release()
            
        except Exception as e:
            print(f"📸 Vision Extraction Error: {e}")

        return results