from transformers import pipeline
class TextAnalyzer:
    def __init__(self):
        # We use 'bertweet' - it is a BERT model specifically trained on social media text
        print("Loading BERT model... this happens only once.")
        self.model = pipeline(
            "sentiment-analysis", 
            model="finiteautomata/bertweet-base-sentiment-analysis"
        )
abc
    def analyze(self, text):
        result = self.model(text)[0]
        # Mapping labels: POS -> Positive, NEG -> Negative, NEU -> Neutral
        mapping = {"POS": "Positive", "NEG": "Negative", "NEU": "Neutral"}
        return {
            "label": mapping.get(result['label'], "Neutral"),
            "score": round(result['score'], 4)
        }