import streamlit as st
import time
from chatbot import SQLChatbot

# Page Config
st.set_page_config(
    page_title="SQL AI Assistant",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS for "Production Level" look - Premium Dark/Modern Theme
st.markdown("""
<style>
    /* Global Settings */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #1e1e2f 0%, #2a2a40 100%);
        color: #e0e0e0;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #161625;
        border-right: 1px solid #2a2a40;
    }
    
    div[data-testid="stSidebarNav"] {
        padding-top: 1rem;
    }

    /* Chat Input Styling */
    .stChatInput {
        border-radius: 12px;
        background-color: #2a2a40;
        border: 1px solid #3f3f5a;
        color: #ffffff;
    }
    
    .stChatInput:focus-within {
        border-color: #6366f1;
        box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
    }

    /* Chat Messages */
    .stChatMessage {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }

    .stChatMessage[data-testid="stChatMessage"]:nth-child(odd) {
        background-color: rgba(99, 102, 241, 0.05); 
        border-color: rgba(99, 102, 241, 0.1);
    }
    
    /* Code Blocks */
    code {
        color: #e0e7ff !important;
        background-color: #282c34 !important;
        padding: 0.2rem 0.4rem;
        border-radius: 4px;
    }
    
    /* Buttons */
    .stButton > button {
        background-color: #4f46e5;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.2s;
    }
    
    .stButton > button:hover {
        background-color: #4338ca;
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
        transform: translateY(-1px);
    }

</style>
""", unsafe_allow_html=True)

# Main Title & Header
col1, col2 = st.columns([1, 5])
with col1:
    st.image("https://img.icons8.com/3d-fluency/94/database.png", width=80) 
with col2:
    st.title("Enterprise SQL Logic Assistant")
    st.caption("🚀 Production-Ready MSSQL Optimization & Logic Engine")

# Initialize Chatbot
@st.cache_resource
def get_chatbot():
    try:
        # Use a consistent session key for Redis history mapping
        return SQLChatbot(session_id="user_session_v1")
    except Exception as e:
        st.error(f"Failed to initialize chatbot: {e}")
        return None

bot = get_chatbot()

# Sidebar content
with st.sidebar:
    st.title("⚙️ Control Panel")
    st.markdown("---")
    
    with st.expander("ℹ️ System Status", expanded=True):
        st.success("🟢 System Online")
        st.info("🧠 Brain: Llama 3 (Ollama)")
        st.info("🗄️ Knowledge: FAISS Vector DB")
        st.info("💾 Memory: Redis Persistent")

    st.markdown("### Settings")
    
    # Assistant Mode Selection
    mode = st.radio("Assistant Mode", ["SQL Expert (Local)", "General (Local AI)"])
    
    if mode == "SQL Expert (Local)":
        temperature = st.slider("Creativity (Temperature)", 0.0, 1.0, 0.1, 0.1, help="Lower is better for strict SQL generation.")
    
    if st.button("🗑️ Clear Context & History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    st.markdown("🔒 **Enterprise Private Environment**\n\nData never leaves your local infrastructure.")

# Initialize message history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! I am your AI Assistant. Select a mode in the sidebar to get started."}]

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else "🤖"):
        st.markdown(msg["content"])

# Chat Input
if prompt := st.chat_input("Type your message here..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant", avatar="🤖"):
        message_placeholder = st.empty()
        full_response = ""
        
        if bot:
            with st.spinner("Thinking..."):
                try:
                    if mode == "General (Local AI)":
                        response = bot.get_general_response(prompt)
                    else:
                        # Use a consistent session key for Redis history mapping
                        # (Ideally this should be handled inside the class or via session state, 
                        # but for now we keep the existing pattern)
                        response = bot.get_response(prompt)
                    
                    # Direct Markdown render is best for the new formatted output
                    message_placeholder.markdown(response)
                    full_response = response
                    
                except Exception as e:
                    st.error(f"Error: {e}")
                    full_response = f"I encountered an error: {e}"
        else:
            st.error("Chatbot is not initialized. Check Docker logs.")
            
    st.session_state.messages.append({"role": "assistant", "content": full_response})
