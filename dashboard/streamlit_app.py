import streamlit as st, os, requests
st.title('Feedback Dashboard')
API = st.sidebar.text_input('API', os.environ.get('API_URL','http://localhost:8000'))
if st.sidebar.button('Load urgent'):
    r = requests.get(API + '/urgent')
    st.write(r.json())
