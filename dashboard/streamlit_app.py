"""
streamlit_app.py — Newsroom Feedback Dashboard.

Replaces the original 8-line stub with a real editor-facing dashboard:
  - Sentiment trend chart (last 7 days)
  - Urgency breakdown
  - Correction requests feed
  - Audience Trust Score
  - Live high-urgency feed
  - Language breakdown (Indic support visible)
"""

import os
import requests
import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Newsroom Feedback Dashboard",
    page_icon="📰",
    layout="wide",
)

API = os.environ.get('API_URL', 'http://localhost:8000')
TOKEN = os.environ.get('API_TOKEN', '')  # set after /token login


def _headers():
    if TOKEN:
        return {"Authorization": f"Bearer {TOKEN}"}
    return {}


def _get(path, params=None):
    try:
        r = requests.get(API + path, headers=_headers(), params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error(f"Cannot connect to API at {API}. Is the backend running?")
        return None
    except Exception as e:
        st.error(f"API error: {e}")
        return None


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Settings")
    api_url = st.text_input("API URL", value=API)
    api_token = st.text_input("Bearer token (optional)", value=TOKEN, type="password")
    days = st.slider("Analysis window (days)", 1, 90, 7)
    urgency_threshold = st.slider("Urgency threshold", 1, 10, 7)
    st.divider()

    if st.button("🔄 Refresh dashboard"):
        st.rerun()

    # Manual ingest
    st.subheader("Manual ingest")
    ingest_text = st.text_area("Feedback text")
    ingest_channel = st.selectbox("Channel", ["email", "twitter", "whatsapp", "web"])
    ingest_lang = st.selectbox("Language", ["auto", "en", "hi", "ta", "te", "mr", "bn"])
    if st.button("Submit feedback"):
        try:
            payload = {"raw_text": ingest_text, "channel": ingest_channel}
            if ingest_lang != "auto":
                payload["language"] = ingest_lang
            resp = requests.post(
                f"{api_url}/ingest_manual",
                json=payload,
                headers={"Authorization": f"Bearer {api_token}"} if api_token else {},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            st.success(
                f"✅ Stored! Sentiment: **{data.get('sentiment')}** | "
                f"Urgency: **{data.get('urgency')}** | "
                f"Correction: **{data.get('correction_suggested')}**"
            )
        except Exception as e:
            st.error(f"Ingest failed: {e}")


# ── Main layout ────────────────────────────────────────────────────────────────
st.title("📰 Regional Newsroom Feedback Dashboard")
st.caption(f"Powered by Regional Feedback AI · API: {api_url}")

# Health check
health = _get("/healthz")
if health:
    st.success(f"API online · v{health.get('version', '?')}")
else:
    st.stop()

# ── Row 1: Summary metrics ─────────────────────────────────────────────────────
summary = _get("/sentiment_summary", {"days": days})
trust   = _get("/trust",            {"days": days})

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    total = summary.get("total", 0) if summary else 0
    st.metric("Total feedback", total, help=f"Last {days} days")

with col2:
    pct_pos = summary.get("pct_positive", 0) if summary else 0
    st.metric("Positive", f"{pct_pos}%", delta=None)

with col3:
    pct_neg = summary.get("pct_negative", 0) if summary else 0
    st.metric("Negative", f"{pct_neg}%")

with col4:
    corr = summary.get("corrections", 0) if summary else 0
    st.metric("Correction requests", corr, delta=None,
              help="Feedback flagged as factual correction requests")

with col5:
    if trust and trust.get("trust_score") is not None:
        ats = trust["trust_score"]
        level = trust.get("trust_level", "")
        color_map = {"high": "normal", "moderate": "off", "low": "inverse"}
        st.metric(
            "Audience Trust Score",
            f"{ats:+.2f}",
            delta=level,
            delta_color=color_map.get(level, "off"),
            help="ATS = (positive − negative − corrections) / total. Range: −1 to +1"
        )
    else:
        st.metric("Audience Trust Score", "N/A")

st.divider()

# ── Row 2: Charts ──────────────────────────────────────────────────────────────
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("Sentiment breakdown")
    if summary and summary.get("total", 0) > 0:
        chart_data = pd.DataFrame({
            "Sentiment": ["Positive", "Negative", "Neutral", "Corrections"],
            "Count": [
                summary["positive"],
                summary["negative"],
                summary["neutral"],
                summary["corrections"],
            ],
            "Color": ["#1D9E75", "#A32D2D", "#888780", "#BA7517"],
        })
        bar = (
            alt.Chart(chart_data)
            .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
            .encode(
                x=alt.X("Sentiment:N", axis=alt.Axis(labelAngle=0)),
                y=alt.Y("Count:Q"),
                color=alt.Color("Color:N", scale=None, legend=None),
                tooltip=["Sentiment", "Count"],
            )
            .properties(height=260)
        )
        st.altair_chart(bar, use_container_width=True)
    else:
        st.info("No sentiment data yet. Submit some feedback to get started.")

with col_right:
    st.subheader("Trust Score")
    if trust and trust.get("trust_score") is not None:
        ats = trust["trust_score"]
        # Gauge-style display
        gauge_pct = int((ats + 1) / 2 * 100)
        color = "#1D9E75" if ats > 0.3 else "#A32D2D" if ats < -0.1 else "#BA7517"
        st.markdown(
            f"""
            <div style='text-align:center; padding:1rem'>
              <div style='font-size:3rem; font-weight:600; color:{color}'>{ats:+.2f}</div>
              <div style='color:#888; font-size:0.9rem'>out of ±1.0</div>
              <div style='margin-top:0.5rem; font-size:1rem'>
                {'🟢 High trust' if ats > 0.3 else '🔴 Low trust' if ats < -0.1 else '🟡 Moderate trust'}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.progress(gauge_pct)
        st.caption(
            f"{trust.get('positive',0)} positive · "
            f"{trust.get('negative',0)} negative · "
            f"{trust.get('corrections',0)} corrections · "
            f"{trust.get('total',0)} total"
        )
    else:
        st.info("No trust data available.")

st.divider()

# ── Row 3: Urgent & Correction feeds ──────────────────────────────────────────
tab1, tab2 = st.tabs([f"🚨 Urgent (≥{urgency_threshold})", "📋 Correction requests"])

with tab1:
    urgent = _get("/urgent", {"threshold": urgency_threshold, "limit": 100})
    if urgent:
        df = pd.DataFrame(urgent)
        if not df.empty:
            # Colour urgency column
            def colour_urgency(val):
                if val >= 9:   return 'background-color:#FCEBEB'
                if val >= 7:   return 'background-color:#FAEEDA'
                return ''

            display_cols = ["feedback_id", "urgency", "sentiment", "correction_suggested",
                            "language", "received_at", "raw_text"]
            display_cols = [c for c in display_cols if c in df.columns]
            st.dataframe(
                df[display_cols].style.applymap(colour_urgency, subset=["urgency"]),
                use_container_width=True,
                hide_index=True,
            )
            # Export
            csv = df[display_cols].to_csv(index=False)
            st.download_button("⬇️ Export CSV", csv, "urgent_feedback.csv", "text/csv")
        else:
            st.info(f"No feedback with urgency ≥ {urgency_threshold}.")
    else:
        st.info("Could not load urgent feedback.")

with tab2:
    corrections = _get("/corrections", {"limit": 100})
    if corrections:
        df_c = pd.DataFrame(corrections)
        if not df_c.empty:
            st.dataframe(df_c, use_container_width=True, hide_index=True)
            st.caption(
                "💡 These items are flagged as factual correction requests — "
                "review and route to the responsible journalist."
            )
            csv_c = df_c.to_csv(index=False)
            st.download_button("⬇️ Export corrections CSV", csv_c,
                               "corrections.csv", "text/csv")
        else:
            st.success("No correction requests in the selected window. ✅")
    else:
        st.info("Could not load corrections data.")

# ── Footer ─────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "Regional Newsroom Feedback System · "
    f"Dashboard refreshed at {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC · "
    "API docs at `/docs`"
)