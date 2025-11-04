import os, argparse, json, requests
from sqlalchemy import text
from app.database import engine
from datetime import datetime

BEARER_TOKEN = os.environ.get('TWITTER_BEARER_TOKEN')

def fetch_tweets(query, max_results=10):
    if not BEARER_TOKEN:
        return []
    headers = {'Authorization': f'Bearer {BEARER_TOKEN}'}
    url = 'https://api.twitter.com/2/tweets/search/recent'
    params = {'query': query, 'max_results': max_results, 'tweet.fields': 'created_at,author_id,lang'}
    r = requests.get(url, headers=headers, params=params, timeout=30)
    r.raise_for_status()
    return r.json().get('data', [])

def insert_tweets(tweets):
    with engine.begin() as conn:
        row = conn.execute(text('SELECT channel_id FROM channels WHERE name = :n'), {'n':'twitter'}).fetchone()
        if not row:
            conn.execute(text("INSERT INTO channels (name, description) VALUES (:n,:d)"), {'n':'twitter','d':'Twitter'})
            row = conn.execute(text('SELECT channel_id FROM channels WHERE name = :n'), {'n':'twitter'}).fetchone()
        channel_id = row[0]
        for t in tweets:
            meta = json.dumps({'tweet_id': t.get('id')})
            ts = t.get('created_at')
            conn.execute(text("""INSERT INTO feedback (channel_id, raw_text, raw_metadata, received_at, language)
                               VALUES (:c,:txt,:meta,:ts,:lang)"""), {'c':channel_id,'txt':t.get('text'),'meta':meta,'ts':ts,'lang':t.get('lang','en')})
    print('Inserted', len(tweets))
