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
#           BACKEND HELPER FUNCTIONS
# ==========================================

def load_local_knowledge():
    """Reads all PDF/TXT files from the local 'knowledge' folder automatically"""
    knowledge_text = ""
    if os.path.exists("knowledge"):
        for filename in os.listdir("knowledge"):
            file_path = os.path.join("knowledge", filename)
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
#           AGENT: LYNN INTERFACE
# ==========================================

st.markdown("### ⭐ Lynn: Productivity Coach")
st.caption("I help you complete the 5-4-3-2-1 Daily System. Discipline equals freedom.")

# 1. State Management
if "lynn_user_name" not in st.session_state:
    st.session_state.lynn_user_name = None
if "lynn_messages" not in st.session_state:
    st.session_state.lynn_messages = []

# 2. Automatically Load Brain (No UI upload needed)
lynn_knowledge = load_local_knowledge()

# 3. User Name Check (Onboarding)
if not st.session_state.lynn_user_name:
    st.markdown("👋 **Welcome to the 5-4-3-2-1 System.**")
    st.markdown("I'm Lynn. Before we begin, what is your name so I can coach you properly?")
    name_input = st.text_input("Your Name", placeholder="Enter your name here...")
    
    if name_input:
        st.session_state.lynn_user_name = name_input
        
        # Prepare the first silent prompt for Gemini to trigger the correct greeting
        current_day = datetime.now().strftime("%A")
        initial_prompt = f"The user's name is {name_input}. Start the session by saying: 'Hello {name_input}, for today {current_day}, we'll start with...' and follow the 5-4-3-2-1 system."
        
        with st.spinner("Lynn is preparing your session..."):
            model = genai.GenerativeModel('gemini-2.0-flash')
            # Custom system instructions for the very first response
            response = model.generate_content(f"SYSTEM: {initial_prompt}\nKNOWLEDGE: {lynn_knowledge}")
            
            # Store only the assistant's response to keep the chat clean
            st.session_state.lynn_messages.append({"role": "assistant", "content": response.text})
            st.rerun()

# 4. Chat Interface
else:
    # Sidebar status
    st.sidebar.title("🏢 Status")
    st.sidebar.success(f"Coaching: {st.session_state.lynn_user_name}")
    st.sidebar.info(f"System: 5-4-3-2-1 Active")

    # Display Chat History
    for msg in st.session_state.lynn_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 5. Continuous Coaching Logic
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
                
                MISSION: Guide the user through the 5-4-3-2-1 System.
                KNOWLEDGE BASE: {lynn_knowledge}
                
                RULES:
                - Always address the user as {st.session_state.lynn_user_name}.
                - Maintain the daily theme for {current_day}.
                - Provide specific scripts from the knowledge base.
                - Be disciplined and motivational.
                """
                
                history_lynn = []
                for m in st.session_state.lynn_messages:
                    role = "user" if m["role"] == "user" else "model"
                    history_lynn.append({"role": role, "parts": [m["content"]]})

                try:
                    model = genai.GenerativeModel('gemini-2.0-flash', system_instruction=LYNN_CORE_PROMPT)
                    response = model.generate_content(history_lynn)
                    st.markdown(response.text)
                    st.session_state.lynn_messages.append({"role": "assistant", "content": response.text})
                except Exception as e:
                    st.error(f"Lynn encountered an error: {str(e)}")
