import streamlit as tf
import requests
import pandas as pd
import datetime

# Using st alias tf to avoid name clashes if any, but let's use standard st.
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Personalized Networking Assistant",
    page_icon="🤝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Endpoint Configuration
API_URL = "http://localhost:8000"

# Custom CSS for Premium Look
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    .main-title {
        background: linear-gradient(135deg, #FF6B6B 0%, #4D96FF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        font-size: 2.8rem;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        color: #8E9AAB;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    /* Glassmorphism Containers */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        backdrop-filter: blur(12px);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .glass-card:hover {
        transform: translateY(-2px);
        border-color: rgba(255, 255, 255, 0.2);
    }
    
    /* Starter Prompts Styles */
    .prompt-box {
        background: rgba(77, 150, 255, 0.08);
        border-left: 5px solid #4D96FF;
        border-radius: 8px;
        padding: 16px;
        font-size: 1.15rem;
        line-height: 1.6;
        font-style: italic;
        color: #E2E8F0;
        margin-bottom: 12px;
        position: relative;
    }
    
    .prompt-card-liked {
        background: rgba(78, 203, 113, 0.08) !important;
        border-left: 5px solid #4ECB71 !important;
    }
    
    .prompt-card-disliked {
        background: rgba(255, 107, 107, 0.08) !important;
        border-left: 5px solid #FF6B6B !important;
    }
    
    /* Badges */
    .theme-badge {
        display: inline-block;
        background: linear-gradient(135deg, rgba(77, 150, 255, 0.2) 0%, rgba(108, 92, 231, 0.2) 100%);
        border: 1px solid rgba(77, 150, 255, 0.4);
        color: #E2E8F0;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
        margin-right: 8px;
        margin-bottom: 8px;
    }
    
    /* KPI Cards */
    .kpi-container {
        display: flex;
        gap: 16px;
        margin-bottom: 24px;
    }
    .kpi-card {
        flex: 1;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    }
    .kpi-val {
        font-size: 2.2rem;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 4px;
    }
    .kpi-lbl {
        color: #8E9AAB;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Fact Check Status Badges */
    .status-badge {
        display: inline-flex;
        align-items: center;
        padding: 8px 16px;
        border-radius: 8px;
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 16px;
    }
    
    .status-supported {
        background-color: rgba(78, 203, 113, 0.15);
        color: #4ECB71;
        border: 1px solid rgba(78, 203, 113, 0.4);
        box-shadow: 0 0 12px rgba(78, 203, 113, 0.2);
    }
    
    .status-refuted {
        background-color: rgba(255, 107, 107, 0.15);
        color: #FF6B6B;
        border: 1px solid rgba(255, 107, 107, 0.4);
        box-shadow: 0 0 12px rgba(255, 107, 107, 0.2);
    }
    
    .status-neutral {
        background-color: rgba(255, 168, 1, 0.15);
        color: #FFA801;
        border: 1px solid rgba(255, 168, 1, 0.4);
        box-shadow: 0 0 12px rgba(255, 168, 1, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# Helper function to check API Health
def check_backend_health():
    try:
        response = requests.get(f"{API_URL}/", timeout=2.0)
        return response.status_code == 200
    except requests.RequestException:
        return False

backend_online = check_backend_health()

# Initialize Session State
if "starters" not in st.session_state:
    st.session_state.starters = []
if "themes" not in st.session_state:
    st.session_state.themes = []
if "generation_id" not in st.session_state:
    st.session_state.generation_id = None
if "feedback_status" not in st.session_state:
    st.session_state.feedback_status = {} # {generation_id: 'like'/'dislike'}

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### ⚙️ Settings & System Status")
    
    # Status Indicator
    if backend_online:
        st.success("🟢 FastAPI Backend: Connected")
    else:
        st.error("🔴 FastAPI Backend: Offline")
        st.warning("Please ensure your FastAPI backend is running on `http://localhost:8000`. Run: `uvicorn backend.main:app --reload`")
        
    # AI Mode Selection
    offline_mode = st.toggle(
        "⚡ Offline / Mock AI Mode",
        value=False,
        help="Skips loading heavy transformers (DistilBERT/GPT-2) and uses fast keyword matchers + templates. Great for development speed and offline testing!"
    )
    
    st.markdown("---")
    st.markdown("### 📊 Metrics at a Glance")
    
    if backend_online:
        try:
            stats_resp = requests.get(f"{API_URL}/feedback/stats").json()
            history_resp = requests.get(f"{API_URL}/history").json()
            
            st.metric("Total Generations", len(history_resp))
            likes = stats_resp.get("likes", 0)
            ratio = stats_resp.get("like_ratio", 0.0) * 100
            st.metric("Positive Feedback Rate", f"{ratio:.1f}%", f"{likes} Likes")
        except Exception:
            st.info("Log metrics could not be loaded.")
    else:
        st.info("Connect backend to see metrics.")
        
    st.markdown("---")
    st.markdown("### 🧹 Data Control")
    if st.button("🗑️ Clear History & Logs"):
        if backend_online:
            try:
                requests.post(f"{API_URL}/history/clear")
                requests.post(f"{API_URL}/feedback/clear")
                st.session_state.starters = []
                st.session_state.themes = []
                st.session_state.generation_id = None
                st.session_state.feedback_status = {}
                st.success("History and logs cleared!")
                st.rerun()
            except Exception as e:
                st.error(f"Error clearing data: {e}")
        else:
            st.error("Backend offline. Cannot clear logs.")

# --- MAIN APP LAYOUT ---
st.markdown('<div class="main-title">Personalized Networking Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">AI-powered smart conversation starters tailored for your next professional event.</div>', unsafe_allow_html=True)

# Main Tab navigation
tab_generator, tab_factcheck, tab_history = st.tabs([
    "✨ Conversation Generator",
    "🔍 Fact Checker",
    "📈 History & Feedback Analytics"
])

# --- TAB 1: GENERATOR ---
with tab_generator:
    col_input, col_output = st.columns([1, 1], gap="large")
    
    with col_input:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("Event & User Profile")
        
        event_desc = st.text_area(
            "Event Description",
            placeholder="e.g., A summit bringing together startup founders, venture capitalists, and engineering leaders to discuss AI scalability, LLM fine-tuning, and early-stage seed funding...",
            height=150,
            help="Describe the event's goals, themes, or panel topics."
        )
        
        user_interests = st.text_input(
            "Your Interests (comma-separated)",
            placeholder="e.g., neural networks, raising seed capital, B2B SaaS marketing",
            help="Your areas of expertise or topics you want to discuss with others."
        )
        
        generate_btn = st.button("✨ Generate Personalized Starters", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Example prompt builder helper
        with st.expander("💡 View Example Event Inputs"):
            st.markdown("""
            **Example 1: Tech & Startups**
            * **Description:** *TechCrunch Disrupt 2026 panel on SaaS growth, bootstrap strategies, and customer acquisition.*
            * **Interests:** *Bootstrapping, customer feedback loops, SEO*
            
            **Example 2: Healthcare & Science**
            * **Description:** *BioMed Innovate annual meeting discussing gene therapy, ethics in AI diagnostics, and healthcare venture capital.*
            * **Interests:** *AI ethics, digital health scaling*
            """)
            
    with col_output:
        if generate_btn:
            if not backend_online:
                st.error("Cannot generate. The FastAPI backend server is offline. Please start it to proceed.")
            elif not event_desc.strip() or not user_interests.strip():
                st.error("Please provide both an event description and your interests.")
            else:
                with st.spinner("Analyzing event themes and generating bespoke prompts..."):
                    try:
                        payload = {
                            "event_description": event_desc,
                            "user_interests": user_interests,
                            "mock": offline_mode
                        }
                        response = requests.post(f"{API_URL}/generate-conversation", json=payload)
                        if response.status_code == 200:
                            data = response.json()
                            st.session_state.generation_id = data.get("generation_id")
                            st.session_state.themes = data.get("themes", [])
                            st.session_state.starters = data.get("conversation_starters", [])
                        else:
                            st.error(f"Backend returned an error: {response.text}")
                    except Exception as e:
                        st.error(f"Error communicating with backend: {e}")
                        
        # Display Results
        if st.session_state.starters:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.subheader("Tailored Conversation Starters")
            
            # Show Extracted Themes
            st.markdown("##### Extracted Event Themes:")
            theme_badges_html = "".join([f'<span class="theme-badge">🏷️ {t}</span>' for t in st.session_state.themes])
            st.markdown(theme_badges_html, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Show Starters
            for idx, starter in enumerate(st.session_state.starters):
                card_id = f"{st.session_state.generation_id}_{idx}"
                current_feedback = st.session_state.feedback_status.get(card_id, None)
                
                # Check status styling class
                css_class = "prompt-box"
                if current_feedback == "like":
                    css_class += " prompt-card-liked"
                elif current_feedback == "dislike":
                    css_class += " prompt-card-disliked"
                    
                st.markdown(f'<div class="{css_class}">“{starter}”</div>', unsafe_allow_html=True)
                
                # Create buttons for feedback
                col_like, col_dislike, col_space = st.columns([0.15, 0.15, 0.7])
                
                with col_like:
                    # Disable if already rated, or display highlighted
                    like_lbl = "👍 Liked" if current_feedback == "like" else "👍 Like"
                    if st.button(like_lbl, key=f"like_{card_id}"):
                        try:
                            # Log to API
                            requests.post(f"{API_URL}/feedback", json={
                                "generation_id": st.session_state.generation_id,
                                "rating": "like"
                            })
                            st.session_state.feedback_status[card_id] = "like"
                            st.rerun()
                        except Exception as e:
                            st.error(f"Feedback error: {e}")
                            
                with col_dislike:
                    dislike_lbl = "👎 Disliked" if current_feedback == "dislike" else "👎 Dislike"
                    if st.button(dislike_lbl, key=f"dislike_{card_id}"):
                        try:
                            # Log to API
                            requests.post(f"{API_URL}/feedback", json={
                                "generation_id": st.session_state.generation_id,
                                "rating": "dislike"
                            })
                            st.session_state.feedback_status[card_id] = "dislike"
                            st.rerun()
                        except Exception as e:
                            st.error(f"Feedback error: {e}")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("Input event details and click generate to view conversation starters.")

# --- TAB 2: FACT CHECKER ---
with tab_factcheck:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("AI Wikipedia Fact-Checker")
    st.write("Verifies networking topics, conversation starters, or factual claims against Wikipedia using search and NLI (Natural Language Inference).")
    
    claim_to_check = st.text_input(
        "Enter claim to verify",
        placeholder="e.g., Python was created by Guido van Rossum and released in 1991.",
        help="Input any factual claim or statement you wish to verify."
    )
    
    check_btn = st.button("🔍 Verify Claim", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    if check_btn:
        if not backend_online:
            st.error("FastAPI backend is offline. Cannot perform fact check.")
        elif not claim_to_check.strip():
            st.error("Please enter a claim to check.")
        else:
            with st.spinner("Searching Wikipedia database & running NLI analysis..."):
                try:
                    response = requests.post(f"{API_URL}/fact-check", json={
                        "claim": claim_to_check,
                        "mock": offline_mode
                    })
                    
                    if response.status_code == 200:
                        data = response.json()
                        verdict = data.get("verdict", "Neutral")
                        confidence = data.get("confidence", 0.5) * 100
                        details = data.get("details", "")
                        wiki_title = data.get("wikipedia_title", "")
                        wiki_summary = data.get("wikipedia_summary", "")
                        wiki_url = data.get("wikipedia_url", "")
                        
                        # Set color based on verdict
                        badge_class = "status-neutral"
                        icon = "⚠️"
                        if verdict == "Supported":
                            badge_class = "status-supported"
                            icon = "✅"
                        elif verdict == "Refuted":
                            badge_class = "status-refuted"
                            icon = "❌"
                            
                        # Show result
                        st.markdown(f'<div class="status-badge {badge_class}">{icon} Claim {verdict} ({confidence:.1f}% Confidence)</div>', unsafe_allow_html=True)
                        st.info(f"**NLI Assessment:** {details}")
                        
                        # Show Wikipedia Details
                        st.markdown("### Wikipedia Reference Source")
                        st.markdown(f"**Article:** [{wiki_title}]({wiki_url})")
                        st.markdown(f"**Wikipedia Summary Extract:**\n> {wiki_summary}")
                    else:
                        st.error(f"Error from API: {response.text}")
                except Exception as e:
                    st.error(f"Communication error: {e}")

# --- TAB 3: HISTORY & ANALYTICS ---
with tab_history:
    if backend_online:
        try:
            history = requests.get(f"{API_URL}/history").json()
            feedback = requests.get(f"{API_URL}/feedback/stats").json()
            
            if not history:
                st.info("No generation history found. Generate some prompts first!")
            else:
                # Stats Header
                st.subheader("Feedback and Activity Metrics")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Prompts Generated", len(history) * 3)
                with col2:
                    st.metric("Likes Recieved", feedback.get("likes", 0))
                with col3:
                    st.metric("Dislikes Recieved", feedback.get("dislikes", 0))
                    
                st.markdown("---")
                st.subheader("Historical Log")
                
                # Format into table
                table_data = []
                for entry in history:
                    ts = entry.get("timestamp", "")
                    # Convert timestamp to human readable
                    try:
                        dt = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
                        time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                    except Exception:
                        time_str = ts
                        
                    table_data.append({
                        "Generation ID": entry.get("generation_id", ""),
                        "Time": time_str,
                        "Event Description": entry.get("event_description", ""),
                        "User Interests": entry.get("user_interests", ""),
                        "Extracted Themes": ", ".join(entry.get("themes", [])),
                        "Prompt 1": entry.get("conversation_starters", ["", "", ""])[0],
                        "Prompt 2": entry.get("conversation_starters", ["", "", ""])[1],
                        "Prompt 3": entry.get("conversation_starters", ["", "", ""])[2],
                    })
                    
                df = pd.DataFrame(table_data)
                st.dataframe(df, use_container_width=True)
                
        except Exception as e:
            st.error(f"Error fetching history logs: {e}")
    else:
        st.error("FastAPI Backend is Offline. History cannot be retrieved.")
