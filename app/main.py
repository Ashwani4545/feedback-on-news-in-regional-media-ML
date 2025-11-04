from flask import Flask, request, jsonify
from sqlalchemy import create_engine, text
import os, json
from app.database import init_db, engine
from app.analysis import analyze_text

app = Flask(__name__)

@app.before_first_request
def startup():
    init_db()

@app.route('/ingest_manual', methods=['POST'])
def ingest_manual():
    data = request.json
    raw_text = data.get('raw_text')
    channel = data.get('channel','email')
    with engine.begin() as conn:
        ch = conn.execute(text('SELECT channel_id FROM channels WHERE name = :n'), {'n': channel}).fetchone()
        if not ch:
            conn.execute(text('INSERT INTO channels (name, description) VALUES (:n, :d)'), {'n': channel, 'd': ''})
            ch = conn.execute(text('SELECT channel_id FROM channels WHERE name = :n'), {'n': channel}).fetchone()
        channel_id = ch[0]
        res = conn.execute(text('INSERT INTO feedback (channel_id, raw_text, raw_metadata, language) VALUES (:c,:t,:m,:l) RETURNING feedback_id'),
                           {'c': channel_id, 't': raw_text, 'm': json.dumps({}), 'l': 'en'})
        fid = res.fetchone()[0]
        ana = analyze_text(raw_text or '')
        conn.execute(text('INSERT INTO feedback_processing (feedback_id, sentiment_score, sentiment_label, urgency, correction_suggested, nlp_metadata) VALUES (:fid,:s,:sl,:u,:cs,:md)'),
                     {'fid': fid, 's': str(ana['sentiment_score']), 'sl': ana['sentiment_label'], 'u': ana['urgency'], 'cs': ana['correction_suggested'], 'md': json.dumps(ana)})
    return jsonify({'status':'ok','feedback_id': fid})

@app.route('/urgent', methods=['GET'])
def urgent():
    with engine.connect() as conn:
        rows = conn.execute(text('SELECT f.feedback_id, f.raw_text, fp.nlp_metadata FROM feedback f JOIN feedback_processing fp ON fp.feedback_id = f.feedback_id WHERE fp.urgency>=7'))
        return jsonify([dict(r) for r in rows])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('API_PORT',8000)))
