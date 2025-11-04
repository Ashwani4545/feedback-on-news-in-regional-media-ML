from nltk.sentiment import SentimentIntensityAnalyzer
import nltk, json
nltk.download('vader_lexicon', quiet=True)
sia = SentimentIntensityAnalyzer()

def analyze_text(text):
    s = sia.polarity_scores(text)
    score = s['compound']
    label = 'positive' if score>0.2 else 'negative' if score<-0.2 else 'neutral'
    correction = any(k in text.lower() for k in ['wrong','incorrect','please correct','missing','where is the source'])
    urgency = 8 if correction else 3
    return {'sentiment_score': score, 'sentiment_label': label, 'urgency': urgency, 'correction_suggested': correction, 'meta': s}
