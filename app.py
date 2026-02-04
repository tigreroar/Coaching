import streamlit as st
import os
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv
from pypdf import PdfReader

# Load environment variables
load_dotenv()

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Lynn: Productivity Coach", layout="wide", page_icon="⭐")

# --- API KEY CONFIGURATION ---
api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    st.error("⚠️ GOOGLE_API_KEY missing in environment variables.")
    st.stop()

genai.configure(api_key=api_key)

# ==========================================
#           AGENT: LYNN LOGIC
# ==========================================

st.markdown("### ⭐ Lynn: Productivity Coach")
st.caption("I help you complete the 5-4-3-2-1 Daily System. Discipline equals freedom.")

# 1. State Management (Memory for Name and Chat)
if "lynn_user_name" not in st.session_state:
    st.session_state.lynn_user_name = None
if "lynn_messages" not in st.session_state:
    st.session_state.lynn_messages = []

# 2. Knowledge Loader (Brains of the Agent)
st.sidebar.title("🧠 Lynn's Brain")
lynn_files = st.sidebar.file_uploader("Upload Instructions/Scripts (Optional)", type=['pdf'], accept_multiple_files=True, key="lynn_uploader")

# Function to extract text from uploaded PDFs
lynn_knowledge_context = ""
if lynn_files:
    for f in lynn_files:
        try:
            reader = PdfReader(f)
            for page in reader.pages:
                lynn_knowledge_context += page.extract_text() + "\n"
        except Exception as e:
            st.sidebar.error(f"Error reading {f.name}: {e}")

# 3. User Name Check (First Interaction)
if not st.session_state.lynn_user_name:
    st.markdown("👋 **Welcome to the 5-4-3-2-1 System.**")
    st.markdown("I'm Lynn. Before we begin, what is your name so I can coach you properly?")
    name_input = st.text_input("Your Name")
    if name_input:
        st.session_state.lynn_user_name = name_input
        # Initial Greeting Trigger
        st.session_state.lynn_messages.append({
            "role": "user", 
            "content": f"Hello {name_input}. Start the coaching session for today."
        })
        st.rerun()

# 4. Chat Interface (Main Interaction)
else:
    # Display Chat History
    for msg in st.session_state.lynn_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 5. Coaching Logic & Prompting
    if prompt := st.chat_input("Reply to Lynn..."):
        st.session_state.lynn_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Lynn is thinking..."):
                # Get Today's context
                current_day = datetime.now().strftime("%A")
                current_date = datetime.now().strftime("%B %d, %Y")
                
                # The System Instruction (Prompts from your original code)
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
                
                MEMORY RULE:
                If the chat history shows you already greeted them today, DO NOT repeat the intro.
                Just continue the coaching conversation.
                
                KNOWLEDGE BASE (Instructions & Scripts from PDFs):
                {lynn_knowledge_context}
                
                STRUCTURE:
                1. Greeting (Only if first msg of day)
                2. Affirmation (3x)
                3. 5 Calls (Scripts)
                4. 4 Texts (Scripts)
                5. 3 Emails (Templates)
                6. 2 Social Actions
                7. 1 CMA
                8. MLS Check
                9. Extra Task ({current_day} specific)
                10. End: Accountability Check
                
                TONE: Disciplined, Structured, Motivational.
                """
                
                # Format history for Gemini
                history_lynn = []
                for m in st.session_state.lynn_messages:
                    role = "user" if m["role"] == "user" else "model"
                    history_lynn.append({"role": role, "parts": [m["content"]]})

                try:
                    model = genai.GenerativeModel('gemini-2.0-flash', system_instruction=LYNN_CORE_PROMPT)
                    # We pass the full history so she "remembers"
                    response = model.generate_content(history_lynn)
                    response_text = response.text
                    
                    st.markdown(response_text)
                    st.session_state.lynn_messages.append({"role": "assistant", "content": response_text})
                except Exception as e:
                    st.error(f"Lynn Error: {str(e)}")
