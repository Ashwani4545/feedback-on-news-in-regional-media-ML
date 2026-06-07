"""
analysis.py — NLP engine for the Regional Newsroom Feedback System.

Upgrade path:
  Tier 1 (default)  : VADER — works offline, no GPU needed, fast.
  Tier 2 (USE_TRANSFORMER=true) : cardiffnlp/twitter-roberta-base-sentiment-latest
                                  ~20 pp accuracy gain on social text.
  Indic             : Google's 'google/muril-base-cased' for Hindi/Tamil/Marathi/Bengali.
                      Activated when language != 'en'.

Set env vars:
  USE_TRANSFORMER=true   — enable RoBERTa tier
  USE_INDIC_MODEL=true   — enable MuRIL for Indic languages
"""

import os
import re
import json
import logging

logger = logging.getLogger(__name__)

# ── Tier 1: VADER (always available as fallback) ──────────────────────────────
import nltk
nltk.download('vader_lexicon', quiet=True)
from nltk.sentiment import SentimentIntensityAnalyzer
_vader = SentimentIntensityAnalyzer()

# ── Tier 2: Transformer (optional) ────────────────────────────────────────────
_transformer_pipeline = None
USE_TRANSFORMER = os.environ.get('USE_TRANSFORMER', 'false').lower() == 'true'

if USE_TRANSFORMER:
    try:
        from transformers import pipeline as hf_pipeline
        _transformer_pipeline = hf_pipeline(
            'text-classification',
            model='cardiffnlp/twitter-roberta-base-sentiment-latest',
            truncation=True,
            max_length=512,
        )
        logger.info('Transformer sentiment model loaded.')
    except Exception as e:
        logger.warning(f'Transformer load failed, falling back to VADER: {e}')

# ── Tier 3: Indic model (optional) ────────────────────────────────────────────
_indic_pipeline = None
USE_INDIC = os.environ.get('USE_INDIC_MODEL', 'false').lower() == 'true'

if USE_INDIC:
    try:
        from transformers import pipeline as hf_pipeline
        _indic_pipeline = hf_pipeline(
            'text-classification',
            model='google/muril-base-cased',
            truncation=True,
            max_length=512,
        )
        logger.info('Indic MuRIL model loaded.')
    except Exception as e:
        logger.warning(f'Indic model load failed: {e}')

# ── Indic language detection ──────────────────────────────────────────────────
try:
    from langdetect import detect as _langdetect
    _langdetect_available = True
except ImportError:
    _langdetect_available = False

INDIC_LANGS = {'hi', 'ta', 'te', 'ml', 'mr', 'bn', 'gu', 'kn', 'pa', 'ur'}

# ── Correction keywords (English + Indic transliterated) ──────────────────────
CORRECTION_PATTERNS = [
    # English
    r'\bwrong\b', r'\bincorrect\b', r'\berror\b', r'\bmistake\b',
    r'\bplease correct\b', r'\bcorrection\b', r'\bmissing\b',
    r'\bfact.?check\b', r'\bwhere is the source\b', r'\bsource\b',
    r'\bfalse\b', r'\bmisleading\b', r'\binaccurate\b', r'\bunverified\b',
    r'\bfake news\b', r'\bno source\b', r'\bproof\b', r'\bunfair\b',
    # Hindi transliterated
    r'\bgalat\b', r'\bsahi nahi\b', r'\bsudharo\b', r'\bsudhaar\b',
    r'\bgalti\b',
]
_correction_re = re.compile('|'.join(CORRECTION_PATTERNS), re.IGNORECASE)

URGENCY_SIGNALS = {
    'correction': 5,   # +5 if correction flagged
    'negative':   2,   # +2 if sentiment is negative
    'viral_kw':   2,   # +2 for urgency keywords
}
VIRAL_KW_RE = re.compile(
    r'\bbreaking\b|\burgent\b|\bscandal\b|\bshocking\b|\bexclusive\b',
    re.IGNORECASE
)


def _detect_language(text: str) -> str:
    if not _langdetect_available or not text:
        return 'en'
    try:
        return _langdetect(text)
    except Exception:
        return 'en'


def _sentiment_transformer(text: str, lang: str) -> dict:
    """Use transformer model; falls back to VADER on error."""
    pipeline = _indic_pipeline if (lang in INDIC_LANGS and _indic_pipeline) else _transformer_pipeline
    if pipeline is None:
        return _sentiment_vader(text)
    try:
        result = pipeline(text[:512])[0]
        label_raw = result['label'].lower()
        # Normalise label variants across models
        if 'pos' in label_raw:
            label = 'positive'
        elif 'neg' in label_raw:
            label = 'negative'
        else:
            label = 'neutral'
        score_raw = result['score']
        # Convert confidence → compound-like score
        if label == 'positive':
            compound = score_raw
        elif label == 'negative':
            compound = -score_raw
        else:
            compound = 0.0
        return {
            'compound': round(compound, 4),
            'label': label,
            'model': 'transformer',
            'raw': result,
        }
    except Exception as e:
        logger.warning(f'Transformer inference failed: {e}')
        return _sentiment_vader(text)


def _sentiment_vader(text: str) -> dict:
    s = _vader.polarity_scores(text)
    compound = s['compound']
    if compound > 0.2:
        label = 'positive'
    elif compound < -0.2:
        label = 'negative'
    else:
        label = 'neutral'
    return {'compound': compound, 'label': label, 'model': 'vader', 'raw': s}


def analyze_text(text: str, language: str = None) -> dict:
    """
    Full NLP analysis pipeline.

    Returns
    -------
    {
        sentiment_score   : float   compound score [-1, 1]
        sentiment_label   : str     positive / negative / neutral
        urgency           : int     1-10
        correction_suggested: bool
        language          : str     detected ISO code
        model_used        : str     vader | transformer | muril
        meta              : dict    raw model output
    }
    """
    if not text:
        return {
            'sentiment_score': 0.0,
            'sentiment_label': 'neutral',
            'urgency': 1,
            'correction_suggested': False,
            'language': language or 'en',
            'model_used': 'none',
            'meta': {},
        }

    # Language detection
    lang = language or _detect_language(text)

    # Sentiment
    if _transformer_pipeline or (_indic_pipeline and lang in INDIC_LANGS):
        result = _sentiment_transformer(text, lang)
    else:
        result = _sentiment_vader(text)

    compound     = result['compound']
    label        = result['label']
    model_used   = result.get('model', 'vader')

    # Correction detection
    correction = bool(_correction_re.search(text))

    # Urgency scoring (1-10 scale)
    urgency = 3  # baseline
    if correction:
        urgency += URGENCY_SIGNALS['correction']
    if label == 'negative':
        urgency += URGENCY_SIGNALS['negative']
    if VIRAL_KW_RE.search(text):
        urgency += URGENCY_SIGNALS['viral_kw']
    urgency = min(urgency, 10)

    return {
        'sentiment_score':     round(compound, 4),
        'sentiment_label':     label,
        'urgency':             urgency,
        'correction_suggested': correction,
        'language':            lang,
        'model_used':          model_used,
        'meta':                result.get('raw', {}),
    }