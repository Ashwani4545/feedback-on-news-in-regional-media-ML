"""Twitter/X ETL module for fetching and storing tweets."""
import logging
import argparse
import json
from typing import List, Dict, Any, Optional
import requests
from sqlalchemy import text
from app.database import engine
from app.config import config

logger = logging.getLogger(__name__)

BEARER_TOKEN = config.TWITTER_BEARER_TOKEN


def fetch_tweets(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """Fetch tweets from Twitter API based on query.
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return (default: 10)
        
    Returns:
        List of tweet dictionaries
    """
    if not BEARER_TOKEN:
        logger.warning("Twitter bearer token not configured, skipping fetch")
        return []
    
    headers = {'Authorization': f'Bearer {BEARER_TOKEN}'}
    url = 'https://api.twitter.com/2/tweets/search/recent'
    params = {
        'query': query,
        'max_results': max_results,
        'tweet.fields': 'created_at,author_id,lang'
    }
    
    try:
        logger.info(f"Fetching tweets with query: {query}")
        r = requests.get(url, headers=headers, params=params, timeout=config.REQUEST_TIMEOUT)
        r.raise_for_status()
        
        data = r.json().get('data', [])
        logger.info(f"Successfully fetched {len(data)} tweets")
        return data
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            logger.error("Twitter API rate limit exceeded")
        elif e.response.status_code == 401:
            logger.error("Twitter API authentication failed - check bearer token")
        else:
            logger.error(f"Twitter API HTTP error: {e}")
        return []
    
    except requests.exceptions.Timeout:
        logger.error(f"Twitter API request timed out after {config.REQUEST_TIMEOUT} seconds")
        return []
    
    except requests.exceptions.ConnectionError:
        logger.error("Failed to connect to Twitter API - check network connection")
        return []
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Twitter API request failed: {e}")
        return []
    
    except Exception as e:
        logger.error(f"Unexpected error fetching tweets: {e}", exc_info=True)
        return []

def insert_tweets(tweets: List[Dict[str, Any]]) -> None:
    """Insert tweets into the database.
    
    Args:
        tweets: List of tweet dictionaries from Twitter API
    """
    if not tweets:
        logger.info("No tweets to insert")
        return
    
    try:
        with engine.begin() as conn:
            # Get or create twitter channel
            row = conn.execute(
                text('SELECT channel_id FROM channels WHERE name = :n'),
                {'n': 'twitter'}
            ).fetchone()
            
            if not row:
                conn.execute(
                    text("INSERT INTO channels (name, description) VALUES (:n,:d)"),
                    {'n': 'twitter', 'd': 'Twitter'}
                )
                row = conn.execute(
                    text('SELECT channel_id FROM channels WHERE name = :n'),
                    {'n': 'twitter'}
                ).fetchone()
            
            channel_id = row[0]
            
            # Insert each tweet
            inserted_count = 0
            for t in tweets:
                try:
                    meta = json.dumps({'tweet_id': t.get('id')})
                    ts = t.get('created_at')
                    text_content = t.get('text', '')
                    
                    conn.execute(
                        text("""INSERT INTO feedback 
                                (channel_id, raw_text, raw_metadata, received_at, language)
                                VALUES (:c,:txt,:meta,:ts,:lang)"""),
                        {
                            'c': channel_id,
                            'txt': text_content,
                            'meta': meta,
                            'ts': ts,
                            'lang': t.get('lang', 'en')
                        }
                    )
                    inserted_count += 1
                except Exception as e:
                    logger.error(f"Failed to insert tweet {t.get('id')}: {e}")
                    continue
            
            logger.info(f"Successfully inserted {inserted_count} out of {len(tweets)} tweets")
    
    except Exception as e:
        logger.error(f"Error inserting tweets: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Fetch tweets from Twitter API')
    parser.add_argument('--query', type=str, default='#news -is:retweet lang:en',
                        help='Twitter search query')
    parser.add_argument('--max-results', type=int, default=10,
                        help='Maximum number of tweets to fetch')
    args = parser.parse_args()
    
    logger.info(f"Starting Twitter ETL with query: {args.query}")
    tweets = fetch_tweets(args.query, args.max_results)
    insert_tweets(tweets)
    logger.info("Twitter ETL completed")
