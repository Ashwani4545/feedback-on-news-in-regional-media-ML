"""NLP analysis module for sentiment and urgency detection."""
import logging
from typing import Dict, Any
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk
from app.config import config

logger = logging.getLogger(__name__)

# Download VADER lexicon
try:
    nltk.download('vader_lexicon', quiet=True)
    logger.info("VADER lexicon downloaded successfully")
except Exception as e:
    logger.error(f"Failed to download VADER lexicon: {e}")

sia = SentimentIntensityAnalyzer()


def analyze_text(text: str) -> Dict[str, Any]:
    """Analyze text for sentiment, urgency, and correction indicators.
    
    Args:
        text: The text to analyze
        
    Returns:
        Dictionary containing sentiment_score, sentiment_label, urgency,
        correction_suggested, and meta information
    """
    try:
        s = sia.polarity_scores(text)
        score = s['compound']
        
        # Determine sentiment label using configurable thresholds
        if score > config.SENTIMENT_POSITIVE_THRESHOLD:
            label = 'positive'
        elif score < config.SENTIMENT_NEGATIVE_THRESHOLD:
            label = 'negative'
        else:
            label = 'neutral'
        
        # Check for correction indicators
        correction_keywords = ['wrong', 'incorrect', 'please correct', 'missing', 'where is the source']
        correction = any(k in text.lower() for k in correction_keywords)
        
        # Determine urgency using configurable scores
        urgency = config.URGENCY_SCORE_CORRECTION if correction else config.URGENCY_SCORE_NORMAL
        
        logger.debug(f"Analyzed text: sentiment={label}, score={score}, urgency={urgency}")
        
        return {
            'sentiment_score': score,
            'sentiment_label': label,
            'urgency': urgency,
            'correction_suggested': correction,
            'meta': s
        }
    except Exception as e:
        logger.error(f"Error analyzing text: {e}")
        # Return default values on error
        return {
            'sentiment_score': 0.0,
            'sentiment_label': 'neutral',
            'urgency': config.URGENCY_SCORE_NORMAL,
            'correction_suggested': False,
            'meta': {}
        }
