"""Tests for Flask API endpoints."""
import pytest
import json
from app.main import app
from app.database import init_db


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'


def test_ingest_manual_success(client):
    """Test successful manual feedback ingestion."""
    response = client.post(
        '/ingest_manual',
        data=json.dumps({
            'raw_text': 'This is a test feedback',
            'channel': 'email'
        }),
        content_type='application/json'
    )
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['status'] == 'ok'
    assert 'feedback_id' in data


def test_ingest_manual_missing_text(client):
    """Test ingestion fails without raw_text."""
    response = client.post(
        '/ingest_manual',
        data=json.dumps({'channel': 'email'}),
        content_type='application/json'
    )
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data


def test_ingest_manual_no_json(client):
    """Test ingestion fails without JSON content type."""
    response = client.post(
        '/ingest_manual',
        data='not json'
    )
    assert response.status_code == 500


def test_urgent_endpoint(client):
    """Test urgent feedback retrieval."""
    # First add an urgent feedback
    client.post(
        '/ingest_manual',
        data=json.dumps({
            'raw_text': 'Please correct this wrong information',
            'channel': 'email'
        }),
        content_type='application/json'
    )
    
    # Then retrieve urgent items
    response = client.get('/urgent')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
