"""Integration tests for the complete system."""
import pytest
import json
from app.main import app
from app.database import init_db, engine
from sqlalchemy import text


@pytest.fixture(scope='module')
def setup_database():
    """Set up database for integration tests."""
    init_db()
    yield
    # Cleanup is not strictly necessary for SQLite in-memory/test databases


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_complete_feedback_workflow(client, setup_database):
    """Test the complete feedback workflow from ingestion to retrieval."""
    # Step 1: Ingest a normal feedback
    response = client.post(
        '/ingest_manual',
        data=json.dumps({
            'raw_text': 'This is a great news article!',
            'channel': 'email'
        }),
        content_type='application/json'
    )
    assert response.status_code == 201
    normal_feedback_id = json.loads(response.data)['feedback_id']
    
    # Step 2: Ingest an urgent feedback (with correction keywords)
    response = client.post(
        '/ingest_manual',
        data=json.dumps({
            'raw_text': 'Please correct the wrong information in this article',
            'channel': 'twitter'
        }),
        content_type='application/json'
    )
    assert response.status_code == 201
    urgent_feedback_id = json.loads(response.data)['feedback_id']
    
    # Step 3: Retrieve urgent feedback
    response = client.get('/urgent')
    assert response.status_code == 200
    urgent_items = json.loads(response.data)
    
    # Verify that only urgent feedback is returned
    urgent_ids = [item['feedback_id'] for item in urgent_items]
    assert urgent_feedback_id in urgent_ids
    assert normal_feedback_id not in urgent_ids
    
    # Step 4: Verify the data in the database
    with engine.connect() as conn:
        # Check feedback table
        result = conn.execute(
            text('SELECT COUNT(*) FROM feedback')
        ).fetchone()
        assert result[0] >= 2
        
        # Check feedback_processing table
        result = conn.execute(
            text('SELECT sentiment_score, urgency FROM feedback_processing WHERE feedback_id = :id'),
            {'id': urgent_feedback_id}
        ).fetchone()
        assert result is not None
        sentiment_score, urgency = result
        # Verify sentiment_score is a float
        assert isinstance(sentiment_score, float)
        assert urgency == 8  # Urgent because of correction keywords


def test_channel_creation(client, setup_database):
    """Test that channels are created automatically."""
    # Ingest feedback with new channel
    response = client.post(
        '/ingest_manual',
        data=json.dumps({
            'raw_text': 'Test feedback',
            'channel': 'facebook'
        }),
        content_type='application/json'
    )
    assert response.status_code == 201
    
    # Verify channel was created
    with engine.connect() as conn:
        result = conn.execute(
            text('SELECT name FROM channels WHERE name = :name'),
            {'name': 'facebook'}
        ).fetchone()
        assert result is not None
        assert result[0] == 'facebook'
