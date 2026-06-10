"""
twitter_etl.py — Fetch tweets and run full NLP analysis pipeline.

Fixes vs original:
  - analyze_text() now called for every tweet (was completely missing)
  - Deduplication: tweet_id checked before insert — no more duplicate rows
  - Graceful error handling: 401, 429, network errors are caught and logged
  - Returns structured result dict instead of just printing
  - insert_tweets() writes to feedback_processing as well
"""

import os
import json
import logging
import argparse
import requests
from datetime import datetime

from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal, Channel, Feedback, FeedbackProcessing
from app.analysis import analyze_text

logger = logging.getLogger(__name__)

BEARER_TOKEN = os.environ.get('TWITTER_BEARER_TOKEN')
TWITTER_API = 'https://api.twitter.com/2/tweets/search/recent'


def fetch_tweets(query: str, max_results: int = 10) -> list:
    """
    Fetch recent tweets matching query.
    Returns list of tweet dicts, or [] on any failure.
    """
    if not BEARER_TOKEN:
        logger.warning("TWITTER_BEARER_TOKEN not set — skipping fetch.")
        return []

    headers = {'Authorization': f'Bearer {BEARER_TOKEN}'}
    params = {
        'query': query,
        'max_results': max(10, min(max_results, 100)),  # API min is 10
        'tweet.fields': 'created_at,author_id,lang',
    }

    try:
        r = requests.get(TWITTER_API, headers=headers,
                         params=params, timeout=30)
        if r.status_code == 401:
            logger.error("Twitter 401: Bearer token invalid or expired.")
            return []
        if r.status_code == 429:
            logger.warning("Twitter 429: Rate limit hit. Try again later.")
            return []
        r.raise_for_status()
        return r.json().get('data', [])
    except requests.exceptions.Timeout:
        logger.error("Twitter API request timed out.")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"Twitter API error: {e}")
        return []


def insert_tweets(tweets: list) -> dict:
    """
    Insert tweets into feedback + feedback_processing tables.
    Skips duplicates silently (tweet_id uniqueness enforced at DB level).

    Returns summary dict: {inserted, skipped, errors}
    """
    if not tweets:
        return {"inserted": 0, "skipped": 0, "errors": 0}

    db = SessionLocal()
    inserted = skipped = errors = 0

    try:
        # Get or create twitter channel
        ch = db.query(Channel).filter(Channel.name == 'twitter').first()
        if not ch:
            ch = Channel(name='twitter', description='Twitter/X feed')
            db.add(ch)
            db.flush()
        channel_id = ch.channel_id

        for t in tweets:
            tweet_id = t.get('id')
            text = t.get('text', '')
            lang = t.get('lang', 'en')
            created = t.get('created_at')

            # Parse timestamp safely
            received_at = datetime.utcnow()
            if created:
                try:
                    received_at = datetime.fromisoformat(
                        created.replace('Z', '+00:00'))
                except ValueError:
                    pass

            try:
                fb = Feedback(
                    channel_id=channel_id,
                    raw_text=text,
                    raw_metadata=json.dumps(
                        {'tweet_id': tweet_id, 'author_id': t.get('author_id')}),
                    received_at=received_at,
                    language=lang,
                    tweet_id=tweet_id,   # unique constraint prevents duplicates
                )
                db.add(fb)
                db.flush()  # get fb.feedback_id — no RETURNING needed

                # Fix: analysis was completely missing in original
                ana = analyze_text(text, language=lang)
                fp = FeedbackProcessing(
                    feedback_id=fb.feedback_id,
                    sentiment_score=ana['sentiment_score'],
                    sentiment_label=ana['sentiment_label'],
                    urgency=ana['urgency'],
                    correction_suggested=ana['correction_suggested'],
                    nlp_metadata=json.dumps(ana),
                )
                db.add(fp)
                db.commit()
                inserted += 1

            except IntegrityError:
                # Duplicate tweet_id — silently skip
                db.rollback()
                skipped += 1
            except Exception as e:
                db.rollback()
                logger.error(f"Failed to insert tweet {tweet_id}: {e}")
                errors += 1

    finally:
        db.close()

    logger.info(
        f"ETL done — inserted={inserted} skipped={skipped} errors={errors}")
    return {"inserted": inserted, "skipped": skipped, "errors": errors}


def run_etl(query: str, max_results: int = 50) -> dict:
    """Full ETL: fetch → analyse → store."""
    tweets = fetch_tweets(query, max_results)
    if not tweets:
        return {"fetched": 0, "inserted": 0, "skipped": 0, "errors": 0}
    result = insert_tweets(tweets)
    result["fetched"] = len(tweets)
    return result


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(
        description="Twitter ETL for newsroom feedback")
    parser.add_argument('--query', required=True,
                        help='Twitter search query')
    parser.add_argument('--max_results', type=int, default=50)
    args = parser.parse_args()

    summary = run_etl(args.query, args.max_results)
    print(f"ETL complete: {summary}")
