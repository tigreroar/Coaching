import streamlit as st
import os
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv
from pypdf import PdfReader

# Load environment variables
load_dotenv()

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Super Agent - Coaching", layout="wide", page_icon="⭐")

# --- API KEY CONFIGURATION ---
api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    st.error("⚠️ GOOGLE_API_KEY missing in environment variables.")
    st.stop()

genai.configure(api_key=api_key)

# ==========================================
#           FRONTEND INTERFACE
# ==========================================

st.markdown("### ⭐ Lynn: Productivity Coach")
st.caption("I help you complete the 5-4-3-2-1 Daily System. Discipline equals freedom.")

# 1. State Management
if "lynn_user_name" not in st.session_state:
    st.session_state.lynn_user_name = None
if "lynn_messages" not in st.session_state:
    st.session_state.lynn_messages = []

# 2. Knowledge Loader
st.sidebar.title("🧠 Lynn's Brain")
lynn_files = st.sidebar.file_uploader("Upload Instructions/Scripts (Optional)", type=['pdf'], accept_multiple_files=True)

lynn_knowledge_context = ""
if lynn_files:
    for f in lynn_files:
        try:
            reader = PdfReader(f)
            for page in reader.pages:
                lynn_knowledge_context += page.extract_text() + "\n"
        except: pass

# 3. User Name Check
if not st.session_state.lynn_user_name:
    st.markdown("👋 **Welcome to the 5-4-3-2-1 System.**")
    st.markdown("I'm Lynn. Before we begin, what is your name so I can coach you properly?")
    name_input = st.text_input("Your Name")
    if name_input:
        st.session_state.lynn_user_name = name_input
        st.session_state.lynn_messages.append({
            "role": "user", 
            "content": f"My name is {name_input}. Start the coaching session for today."
        })
        st.rerun()

# 4. Chat Interface
else:
    # Display History
    for msg in st.session_state.lynn_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 5. The "Brain" Logic
    if prompt := st.chat_input("Reply to Lynn..."):
        st.session_state.lynn_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Lynn is thinking..."):
                current_day = datetime.now().strftime("%A")
                current_date = datetime.now().strftime("%B %d, %Y")
                
                LYNN_CORE_PROMPT = f"""
                You are Lynn, the Real Estate Productivity Coach.
                User Name: {st.session_state.lynn_user_name}
                Current Date: {current_day}, {current_date}
                YOUR GOAL: Guide the user through the 5-4-3-2-1 System.
                DAILY THEMES:
                - Monday: Foundation & Pipeline Reset
                - Tuesday: Contact Refresh & Market Awareness
                - Wednesday: Video & Visibility
                - Thursday: Relationships & Gratitude
                - Friday: Weekly Review & Score Submission
                KNOWLEDGE BASE: {lynn_knowledge_context}
                TONE: Disciplined, Structured, Motivational.
                """
                
                history_lynn = []
                for m in st.session_state.lynn_messages:
                    history_lynn.append({"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]})

                try:
                    model = genai.GenerativeModel('gemini-2.0-flash', system_instruction=LYNN_CORE_PROMPT)
                    response = model.generate_content(history_lynn)
                    response_text = response.text
                    
                    st.markdown(response_text)
                    st.session_state.lynn_messages.append({"role": "assistant", "content": response_text})
                except Exception as e:
                    st.error(f"Lynn Error: {str(e)}")