import streamlit as st
import requests
import time
import os

# Configuration
API_URL = os.getenv("API_URL", "http://backend:8000/api")

# Page Config
st.set_page_config(
    page_title="SQL AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS Styling (Premium Dark Theme) ---
st.markdown("""
<style>
    /* Global Settings */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main App Background */
    .stApp {
        background: radial-gradient(circle at top right, #1e1b4b, #0f172a);
        color: #f8fafc;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #1e293b;
        border-right: 1px solid #334155;
    }
    
    div[data-testid="stSidebarNav"] {
        padding-top: 1rem;
    }

    /* Input Fields (Start with transparent, then focus) */
    .stTextInput > div > div > input {
        background-color: #1e293b;
        color: #f8fafc;
        border: 1px solid #334155;
        border-radius: 8px;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #6366f1;
        box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
    }

    /* Chat Input Styling */
    .stChatInput {
        border-radius: 12px;
        background-color: #1e293b;
        border: 1px solid #334155;
    }
    
    .stChatInput:focus-within {
        border-color: #6366f1;
        box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
    }

    /* Chat Messages */
    .stChatMessage {
        background-color: rgba(30, 41, 59, 0.7); /* Glassmorphism */
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }

    /* User Message distinct style */
    div[data-testid="stChatMessage"]:nth-child(odd) {
        background-color: rgba(99, 102, 241, 0.1); 
        border: 1px solid rgba(99, 102, 241, 0.2);
    }
    
    /* Buttons */
    .stButton > button {
        background-color: #6366f1;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.2s;
        width: 100%;
    }
    
    .stButton > button:hover {
        background-color: #4f46e5;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
        transform: translateY(-1px);
    }

    /* Success/Error Messages */
    .stSuccess, .stError {
        border-radius: 8px;
    }

</style>
""", unsafe_allow_html=True)

# --- Session State Management ---
if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "page" not in st.session_state:
    st.session_state.page = "login"

# --- Functions ---

def login(username, password):
    try:
        response = requests.post(f"{API_URL}/auth/login", json={"username": username, "password": password})
        if response.status_code == 200:
            data = response.json()
            st.session_state.token = data["access_token"]
            st.session_state.user = username
            st.session_state.page = "chat"
            st.rerun()
        else:
            st.error("Invalid username or password")
    except Exception as e:
        st.error(f"Connection error: {e}")

def register(username, password):
    try:
        response = requests.post(f"{API_URL}/auth/register", json={"username": username, "password": password})
        if response.status_code == 200:
            st.success("Registration successful! Please login.")
            st.session_state.page = "login"
            time.sleep(1) # Give user a moment to see success
            st.rerun()
        else:
            st.error(f"Registration failed: {response.text}")
    except Exception as e:
        st.error(f"Connection error: {e}")

def logout():
    st.session_state.token = None
    st.session_state.user = None
    st.session_state.messages = []
    st.session_state.page = "login"
    st.rerun()

def get_history():
    # In a real app, fetch from backend if persistent
    pass 

def chat(prompt):
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    try:
        response = requests.post(
            f"{API_URL}/chat", 
            json={"message": prompt}, 
            headers=headers,
            timeout=300 # Wait up to 5 mins for LLM
        )
        if response.status_code == 200:
            return response.json()["response"]
        elif response.status_code == 401:
            st.error("Session expired. Please login again.")
            logout()
            return None
        else:
            return f"Error: {response.text}"
    except Exception as e:
        return f"Error connecting to backend: {e}"


# --- Application Layout ---

if st.session_state.page == "login":
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🔒 Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            login(username, password)
        
        st.markdown("---")
        if st.button("Create Account"):
            st.session_state.page = "register"
            st.rerun()

elif st.session_state.page == "register":
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("➕ Register")
        username = st.text_input("Choose Username")
        password = st.text_input("Choose Password", type="password")
        if st.button("Register"):
            register(username, password)
        
        st.markdown("---")
        if st.button("Back to Login"):
            st.session_state.page = "login"
            st.rerun()

elif st.session_state.page == "chat":
    # Sidebar
    with st.sidebar:
        st.title("⚙️ SQL AI Assistant")
        st.text(f"Logged in as: {st.session_state.user}")
        st.info("Strict Mode: ON (MSSQL Only)")
        
        if st.button("Logout"):
            logout()
    
    # Main Chat Interface
    st.title("💬 Enterprise SQL Assistant")
    st.caption("🚀 Production-Ready MSSQL Optimization Engine")

    # Display History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else "🤖"):
            st.markdown(msg["content"])

    # Chat Input
    if prompt := st.chat_input("Ask a question about SQL Server..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        # Generate response
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Thinking..."):
                response = chat(prompt)
                if response:
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
