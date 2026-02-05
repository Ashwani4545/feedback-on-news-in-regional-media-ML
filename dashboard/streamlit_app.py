"""Streamlit dashboard for viewing feedback insights."""
import streamlit as st
import os
import requests
from typing import Optional

# Configure page
st.set_page_config(page_title="Feedback Dashboard", page_icon="📊")

st.title('📊 Feedback Dashboard')

# API configuration
API = st.sidebar.text_input(
    'API URL',
    os.environ.get('API_URL', 'http://localhost:8000')
)

# Set timeout for requests
TIMEOUT = 10


def fetch_urgent_feedback(api_url: str) -> Optional[dict]:
    """Fetch urgent feedback from the API.
    
    Args:
        api_url: Base URL of the API
        
    Returns:
        JSON response or None if request fails
    """
    try:
        url = f"{api_url.rstrip('/')}/urgent"
        response = requests.get(url, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        st.error(f"⏱️ Request timed out after {TIMEOUT} seconds. Please check if the API is running.")
        return None
    except requests.exceptions.ConnectionError:
        st.error(f"❌ Could not connect to API at {api_url}. Please check if the API is running.")
        return None
    except requests.exceptions.HTTPError as e:
        st.error(f"❌ API returned error: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
        return None


# Load urgent feedback button
if st.sidebar.button('Load Urgent Feedback'):
    with st.spinner('Loading urgent feedback...'):
        data = fetch_urgent_feedback(API)
        
        if data is not None:
            if len(data) == 0:
                st.info("✅ No urgent feedback items found.")
            else:
                st.success(f"Found {len(data)} urgent feedback item(s)")
                
                # Display each feedback item
                for idx, item in enumerate(data, 1):
                    with st.expander(f"Feedback #{item.get('feedback_id', idx)}"):
                        st.write("**Text:**")
                        st.write(item.get('raw_text', 'N/A'))
                        
                        # Parse and display metadata if available
                        if 'nlp_metadata' in item:
                            st.write("**NLP Metadata:**")
                            st.json(item.get('nlp_metadata'))

# Sidebar information
st.sidebar.markdown("---")
st.sidebar.markdown("### ℹ️ About")
st.sidebar.info(
    "This dashboard displays urgent feedback items that require immediate attention. "
    "Feedback is automatically analyzed for sentiment and urgency."
)

# Health check
st.sidebar.markdown("---")
if st.sidebar.button("Check API Health"):
    try:
        url = f"{API.rstrip('/')}/health"
        response = requests.get(url, timeout=TIMEOUT)
        if response.status_code == 200:
            st.sidebar.success("✅ API is healthy")
        else:
            st.sidebar.error("❌ API is not responding correctly")
    except Exception as e:
        st.sidebar.error(f"❌ Cannot reach API: {str(e)}")
