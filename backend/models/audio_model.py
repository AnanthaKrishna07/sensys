import os aa
import torch
import librosa
import numpy as np
from transformers import Wav2Vec2ForSequenceClassification, Wav2Vec2FeatureExtractor

class AudioAnalyzer:
    def __init__(self):
        """ Initializes the Wav2Vec2 Vocal Emotion model """
        # We use a pre-trained model fine-tuned on RAVDESS/CREMA-D emotional datasets
        self.model_name = "superb/wav2vec2-base-superb-er"
        self.feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(self.model_name)
        self.model = Wav2Vec2ForSequenceClassification.from_pretrained(self.model_name)
        
        # SENSYS Standardization (0=Neg, 1=Neu, 2=Pos)
        # Model classes: 0:neu, 1:hap, 2:ang, 3:sad
        self.id_map = {0: 1, 1: 2, 2: 0, 3: 0} 

    def analyze(self, audio_path):
        if not os.path.exists(audio_path):
            return {"label": "Neutral", "label_id": 1, "score": 0.0}

        try:
            # Load audio and force resampling to 16kHz
            speech, sr = librosa.load(audio_path, sr=16000, mono=True)
            
            # Normalize volume (Critical for consistent analysis)
            speech = librosa.util.normalize(speech)
            
            # Preprocess
            inputs = self.feature_extractor(speech, sampling_rate=16000, return_tensors="pt", padding=True)
            
            # Inference
            with torch.no_grad():
                logits = self.model(**inputs).logits
            
            scores = torch.nn.functional.softmax(logits, dim=-1)
            pred_id = torch.argmax(scores, dim=-1).item()
            
            # Map result to SENSYS labels
            label_id = self.id_map.get(pred_id, 1)
            labels = {0: "Negative", 1: "Neutral", 2: "Positive"}
            
            confidence = float(torch.max(scores).item())
            
            return {
                "label": labels[label_id],
                "label_id": label_id,
                "score": round(confidence, 4)
            }
            
        except Exception as e:
            print(f"🔊 Audio AI Error: {e}")
            return {"label": "Neutral", "label_id": 1, "score": 0.0}