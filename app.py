import streamlit as st
import os
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv
from pypdf import PdfReader

# Load environment variables
load_dotenv()

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Your Agent Coach: Productivity", layout="wide", page_icon="⭐")

# --- API KEY CONFIGURATION ---
api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    st.error("⚠️ GOOGLE_API_KEY missing in environment variables.")
    st.stop()

genai.configure(api_key=api_key)

# ==========================================
#           BACKEND HELPER FUNCTIONS
# ==========================================

def load_local_knowledge():
    """Reads all PDF/TXT files from the local 'knowledge' folder automatically"""
    knowledge_text = ""
    knowledge_path = "knowledge"
    
    if os.path.exists(knowledge_path):
        for filename in os.listdir(knowledge_path):
            file_path = os.path.join(knowledge_path, filename)
            try:
                if filename.endswith(".pdf"):
                    reader = PdfReader(file_path)
                    for page in reader.pages:
                        knowledge_text += page.extract_text() + "\n"
                elif filename.endswith(".txt") or filename.endswith(".md"):
                    with open(file_path, "r", encoding="utf-8") as f:
                        knowledge_text += f.read() + "\n"
            except Exception as e:
                print(f"Error reading {filename}: {e}")
    return knowledge_text

# ==========================================
#           AGENT: LYNN LOGIC
# ==========================================

st.markdown("### ⭐ Your Agent Coach: Productivity")
st.caption("I help you complete the 5-4-3-2-1 Daily System. Discipline equals freedom.")

# 1. State Management (Memory for Name and Chat)
if "lynn_user_name" not in st.session_state:
    st.session_state.lynn_user_name = None
if "lynn_messages" not in st.session_state:
    st.session_state.lynn_messages = []

# 2. Automatically Load Brain (No UI upload needed)
lynn_knowledge = load_local_knowledge()

# 3. User Name Check (First Interaction)
if not st.session_state.lynn_user_name:
    st.markdown("👋 **Welcome to the 5-4-3-2-1 System.**")
    st.markdown("I'm your Agent Coach. Before we begin, what is your name so I can coach you properly?")
    name_input = st.text_input("Your Name")
    if name_input:
        st.session_state.lynn_user_name = name_input
        # Initial Greeting Trigger - Custom format requested
        current_day = datetime.now().strftime("%A")
        initial_greeting = f"Hello {name_input}, for today {current_day}, we'll start with the coaching session."
        
        st.session_state.lynn_messages.append({
            "role": "assistant", 
            "content": initial_greeting
        })
        st.rerun()

# 4. Chat Interface (Main Interaction)
else:
    # Sidebar status
    st.sidebar.title("🏢 Status")
    st.sidebar.success(f"Coaching: {st.session_state.lynn_user_name}")
    st.sidebar.info(f"System: 5-4-3-2-1 Active")

    # Display Chat History
    for msg in st.session_state.lynn_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 5. Coaching Logic & Prompting
    if prompt := st.chat_input("Reply to Agent Coach..."):
        st.session_state.lynn_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Coach is thinking..."):
                # Get Today's context
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
                
                KNOWLEDGE BASE (Instructions & Scripts from your knowledge folder):
                {lynn_knowledge}
                
                STRUCTURE:
                1. Affirmation (3x)
                2. 5 Calls (Scripts)
                3. 4 Texts (Scripts)
                4. 3 Emails (Templates)
                5. 2 Social Actions
                6. 1 CMA
                7. MLS Check
                8. Extra Task ({current_day} specific)
                9. End: Accountability Check
                
                TONE: Disciplined, Structured, Motivational.
                """
                
                # Format history for Gemini
                history_lynn = []
                for m in st.session_state.lynn_messages:
                    role = "user" if m["role"] == "user" else "model"
                    history_lynn.append({"role": role, "parts": [m["content"]]})

                try:
                    model = genai.GenerativeModel('gemini-2.0-flash', system_instruction=LYNN_CORE_PROMPT)
                    response = model.generate_content(history_lynn)
                    response_text = response.text
                    
                    st.markdown(response_text)
                    st.session_state.lynn_messages.append({"role": "assistant", "content": response_text})
                except Exception as e:
                    st.error(f"Lynn Error: {str(e)}")

