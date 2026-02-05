"""Flask API server for the Regional Newsroom Feedback System."""
import logging
import json
from typing import Dict, Any
from flask import Flask, request, jsonify
from sqlalchemy import create_engine, text
from app.database import init_db, engine
from app.analysis import analyze_text
from app.config import config

logger = logging.getLogger(__name__)

app = Flask(__name__)


def initialize_database() -> None:
    """Initialize the database on application startup."""
    try:
        init_db()
        logger.info("Database initialization completed")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


# Initialize database before first request using app context
with app.app_context():
    initialize_database()

@app.route('/ingest_manual', methods=['POST'])
def ingest_manual() -> tuple[Dict[str, Any], int]:
    """Ingest manual feedback from any channel.
    
    Request JSON:
        {
            "raw_text": "Feedback text",
            "channel": "email" (optional, defaults to "email")
        }
    
    Returns:
        JSON response with status and feedback_id
    """
    try:
        # Validate request data
        if not request.json:
            logger.warning("Received request without JSON body")
            return jsonify({'error': 'Request must be JSON'}), 400
        
        data = request.json
        raw_text = data.get('raw_text')
        
        if not raw_text:
            logger.warning("Received request without raw_text")
            return jsonify({'error': 'raw_text is required'}), 400
        
        channel = data.get('channel', 'email')
        
        with engine.begin() as conn:
            # Get or create channel
            ch = conn.execute(
                text('SELECT channel_id FROM channels WHERE name = :n'),
                {'n': channel}
            ).fetchone()
            
            if not ch:
                conn.execute(
                    text('INSERT INTO channels (name, description) VALUES (:n, :d)'),
                    {'n': channel, 'd': ''}
                )
                ch = conn.execute(
                    text('SELECT channel_id FROM channels WHERE name = :n'),
                    {'n': channel}
                ).fetchone()
            
            channel_id = ch[0]
            
            # Insert feedback
            res = conn.execute(
                text('INSERT INTO feedback (channel_id, raw_text, raw_metadata, language) '
                     'VALUES (:c,:t,:m,:l) RETURNING feedback_id'),
                {'c': channel_id, 't': raw_text, 'm': json.dumps({}), 'l': 'en'}
            )
            fid = res.fetchone()[0]
            
            # Analyze text
            ana = analyze_text(raw_text or '')
            
            # Insert processing results with Float sentiment_score
            conn.execute(
                text('INSERT INTO feedback_processing '
                     '(feedback_id, sentiment_score, sentiment_label, urgency, '
                     'correction_suggested, nlp_metadata) '
                     'VALUES (:fid,:s,:sl,:u,:cs,:md)'),
                {
                    'fid': fid,
                    's': ana['sentiment_score'],  # Now a Float, not a String
                    'sl': ana['sentiment_label'],
                    'u': ana['urgency'],
                    'cs': ana['correction_suggested'],
                    'md': json.dumps(ana)
                }
            )
        
        logger.info(f"Ingested feedback {fid} from channel {channel}")
        return jsonify({'status': 'ok', 'feedback_id': fid}), 201
    
    except Exception as e:
        logger.error(f"Error ingesting manual feedback: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@app.route('/urgent', methods=['GET'])
def urgent() -> tuple[Any, int]:
    """Get all urgent feedback items (urgency >= 7).
    
    Returns:
        JSON array of urgent feedback with metadata
    """
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                text('SELECT f.feedback_id, f.raw_text, fp.nlp_metadata '
                     'FROM feedback f '
                     'JOIN feedback_processing fp ON fp.feedback_id = f.feedback_id '
                     'WHERE fp.urgency >= 7')
            )
            result = [dict(r._mapping) for r in rows]
            logger.info(f"Retrieved {len(result)} urgent feedback items")
            return jsonify(result), 200
    
    except Exception as e:
        logger.error(f"Error retrieving urgent feedback: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500


@app.route('/health', methods=['GET'])
def health() -> tuple[Dict[str, str], int]:
    """Health check endpoint.
    
    Returns:
        JSON response with status
    """
    return jsonify({'status': 'healthy'}), 200


if __name__ == '__main__':
    app.run(host=config.API_HOST, port=config.API_PORT)
