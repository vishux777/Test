import streamlit as st
import hashlib
import json
import time
from datetime import datetime
from cryptography.fernet import Fernet
import threading
import uuid
import base64
from typing import Dict, List, Optional
import re

# ====================
# GLOBAL SHARED STATE
# ====================
class GlobalState:
    _lock = threading.Lock()
    ROOMS: Dict[str, Dict] = {}
    ENCRYPTION_KEY = Fernet.generate_key()
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_rooms(cls):
        with cls._lock:
            return cls.ROOMS.copy()
    
    @classmethod
    def get_room(cls, room_id: str):
        with cls._lock:
            return cls.ROOMS.get(room_id, {}).copy()
    
    @classmethod
    def add_message(cls, room_id: str, message_data: Dict):
        with cls._lock:
            if room_id not in cls.ROOMS:
                return
            if "messages" not in cls.ROOMS[room_id]:
                cls.ROOMS[room_id]["messages"] = []
            cls.ROOMS[room_id]["messages"].append(message_data)
    
    @classmethod
    def create_room(cls, room_id: str, room_name: str):
        with cls._lock:
            if room_id not in cls.ROOMS:
                cls.ROOMS[room_id] = {
                    "messages": [],
                    "created_at": time.time(),
                    "name": room_name,
                    "room_id": room_id
                }
                return True
            return False
    
    @classmethod
    def get_encryption_key(cls):
        return cls.ENCRYPTION_KEY

# Initialize global state
GLOBAL_STATE = GlobalState()

# ====================
# ENCRYPTION & HASHING
# ====================
class EncryptionHandler:
    def __init__(self):
        self.key = GLOBAL_STATE.get_encryption_key()
        self.cipher = Fernet(self.key)
    
    def encrypt(self, plaintext: str) -> str:
        return self.cipher.encrypt(plaintext.encode()).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        return self.cipher.decrypt(ciphertext.encode()).decode()
    
    @staticmethod
    def calculate_hash(data: str) -> str:
        return hashlib.sha256(data.encode()).hexdigest()

# ====================
# SCARABYATH-INSPIRED CINEMATIC UI
# ====================
def inject_scarabynath_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
    
    .stApp {
        background: #0a0a0a !important;
        background-image: 
            radial-gradient(circle at 10% 20%, rgba(20, 20, 60, 0.1) 0%, transparent 40%),
            radial-gradient(circle at 90% 80%, rgba(40, 10, 80, 0.1) 0%, transparent 40%);
    }
    
    .main {
        background: transparent !important;
    }
    
    /* Minimalist Hero Section */
    .hero-container {
        text-align: left;
        padding: 2rem 0 3rem 0;
        position: relative;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        margin-bottom: 3rem;
    }
    
    .studio-name {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 500;
        font-size: 0.9rem;
        color: #8a63d2;
        letter-spacing: 0.3em;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
        opacity: 0.7;
    }
    
    .main-title {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        font-size: 3.5rem;
        background: linear-gradient(135deg, #ffffff 0%, #a78bfa 50%, #8a63d2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0;
        line-height: 1.1;
        letter-spacing: -0.02em;
    }
    
    .title-accent {
        font-weight: 300;
        opacity: 0.9;
    }
    
    .tagline {
        font-family: 'Inter', sans-serif;
        font-weight: 300;
        font-size: 1.1rem;
        color: rgba(255, 255, 255, 0.6);
        margin-top: 1.5rem;
        max-width: 600px;
        line-height: 1.6;
    }
    
    /* Room Creation Card - Minimal */
    .creation-card {
        background: rgba(15, 15, 20, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 16px;
        padding: 2.5rem;
        margin: 2rem 0;
        position: relative;
        overflow: hidden;
    }
    
    .creation-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, #8a63d2, transparent);
    }
    
    .card-title {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 500;
        font-size: 1.1rem;
        color: #8a63d2;
        margin-bottom: 2rem;
        letter-spacing: 0.1em;
        text-transform: uppercase;
    }
    
    /* Input Fields */
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 1rem !important;
        padding: 0.75rem 1rem !important;
        transition: all 0.2s ease !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #8a63d2 !important;
        background: rgba(138, 99, 210, 0.05) !important;
        box-shadow: none !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: rgba(255, 255, 255, 0.3) !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #8a63d2 0%, #6d28d9 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.8rem 2rem !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        letter-spacing: 0.05em !important;
        transition: all 0.2s ease !important;
        width: 100%;
        text-transform: uppercase;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(138, 99, 210, 0.3) !important;
        background: linear-gradient(135deg, #946be6 0%, #7c3aed 100%) !important;
    }
    
    /* Chat Container */
    .chat-container {
        background: rgba(15, 15, 20, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 16px;
        padding: 2rem;
        margin-top: 2rem;
        max-height: 500px;
        overflow-y: auto;
    }
    
    .chat-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 2rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    .room-info {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 500;
        font-size: 1.1rem;
        color: #ffffff;
    }
    
    .room-id {
        font-family: 'Inter', monospace;
        font-size: 0.9rem;
        color: #8a63d2;
        background: rgba(138, 99, 210, 0.1);
        padding: 0.3rem 0.8rem;
        border-radius: 4px;
        margin-left: 1rem;
    }
    
    .leave-btn {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: rgba(255, 255, 255, 0.7) !important;
    }
    
    .leave-btn:hover {
        background: rgba(255, 255, 255, 0.1) !important;
    }
    
    /* Messages */
    .message {
        margin-bottom: 1.5rem;
        padding: 1.2rem;
        background: rgba(255, 255, 255, 0.02);
        border-radius: 12px;
        border-left: 3px solid #8a63d2;
        animation: fadeIn 0.3s ease-out;
    }
    
    .message-header {
        display: flex;
        justify-content: space-between;
        margin-bottom: 0.5rem;
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
    }
    
    .message-user {
        color: #8a63d2;
        font-weight: 500;
    }
    
    .message-time {
        color: rgba(255, 255, 255, 0.4);
    }
    
    .message-content {
        color: rgba(255, 255, 255, 0.9);
        font-family: 'Inter', sans-serif;
        line-height: 1.5;
        font-size: 0.95rem;
    }
    
    .message-meta {
        margin-top: 0.8rem;
        padding-top: 0.8rem;
        border-top: 1px solid rgba(255, 255, 255, 0.05);
        font-size: 0.75rem;
        color: rgba(255, 255, 255, 0.4);
        font-family: 'Inter', monospace;
    }
    
    /* Status Indicator */
    .status-indicator {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.4rem 0.8rem;
        background: rgba(138, 99, 210, 0.1);
        border-radius: 20px;
        font-size: 0.85rem;
        color: #8a63d2;
        margin-bottom: 1rem;
    }
    
    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #10b981;
        animation: pulse 2s infinite;
    }
    
    /* Join Section */
    .join-section {
        margin-top: 3rem;
    }
    
    .join-card {
        background: rgba(15, 15, 20, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 16px;
        padding: 2rem;
        margin-top: 1rem;
    }
    
    .join-id-display {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.9rem;
        color: rgba(255, 255, 255, 0.7);
        margin-bottom: 1rem;
        padding: 1rem;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 8px;
        border: 1px dashed rgba(255, 255, 255, 0.1);
    }
    
    .join-id-display strong {
        color: #8a63d2;
        font-family: 'Inter', monospace;
        font-size: 1.1rem;
        margin-left: 0.5rem;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        background: transparent !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        color: rgba(255, 255, 255, 0.5) !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        padding: 0.5rem 0 !important;
        border-radius: 0 !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: transparent !important;
        color: #ffffff !important;
        border-bottom: 2px solid #8a63d2 !important;
    }
    
    /* Animations */
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes pulse {
        0%, 100% {
            opacity: 1;
        }
        50% {
            opacity: 0.5;
        }
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(138, 99, 210, 0.3);
        border-radius: 3px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(138, 99, 210, 0.5);
    }
    
    </style>
    """, unsafe_allow_html=True)

def render_scarabynath_header():
    st.markdown("""
    <div class="hero-container">
        <div class="studio-name">SCARABYNATH STUDIO</div>
        <h1 class="main-title">DARKRELAY<br><span class="title-accent">Anonymous Encrypted Platform</span></h1>
        <div class="tagline">
            At the intersection of security and technology, we design encrypted experiences 
            that protect, innovate and transform digital communication.
        </div>
    </div>
    """, unsafe_allow_html=True)

# ====================
# CHAT FUNCTIONALITY
# ====================
def initialize_session():
    if 'user_id' not in st.session_state:
        st.session_state.user_id = f"user_{uuid.uuid4().hex[:8]}"
    if 'current_room' not in st.session_state:
        st.session_state.current_room = None
    if 'room_name' not in st.session_state:
        st.session_state.room_name = ""
    if 'join_room_id' not in st.session_state:
        st.session_state.join_room_id = ""

def generate_room_id(name: str) -> str:
    """Generate a readable room ID"""
    clean_name = re.sub(r'[^a-zA-Z0-9]', '', name)[:4].upper()
    unique_part = uuid.uuid4().hex[:4].upper()
    return f"{clean_name}-{unique_part}"

def create_room_section():
    st.markdown("""
    <div class="creation-card">
        <div class="card-title">Create New Channel</div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        room_name = st.text_input(
            "Channel Name",
            placeholder="Enter channel name...",
            key="new_room_name",
            label_visibility="collapsed"
        )
    with col2:
        create_clicked = st.button("CREATE", type="primary", use_container_width=True)
    
    if create_clicked and room_name.strip():
        room_id = generate_room_id(room_name.strip())
        created = GLOBAL_STATE.create_room(room_id, room_name.strip())
        
        if created:
            st.session_state.current_room = room_id
            st.session_state.room_name = room_name.strip()
            st.success(f"Channel created with ID: **{room_id}**")
            time.sleep(0.5)
            st.rerun()
        else:
            st.error("Channel already exists")
    
    st.markdown("</div>", unsafe_allow_html=True)

def join_room_section():
    st.markdown("""
    <div class="join-section">
        <div class="card-title">Join Existing Channel</div>
        <div class="join-card">
    """, unsafe_allow_html=True)
    
    join_id = st.text_input(
        "Channel ID",
        placeholder="Enter channel ID (e.g., CHAT-AB12)...",
        key="join_room_input",
        label_visibility="collapsed"
    )
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("JOIN CHANNEL", use_container_width=True):
            if join_id.strip():
                room_data = GLOBAL_STATE.get_room(join_id.strip())
                if room_data:
                    st.session_state.current_room = join_id.strip()
                    st.session_state.room_name = room_data.get("name", "Unknown")
                    st.rerun()
                else:
                    st.error("Channel not found")
    
    st.markdown("</div></div>", unsafe_allow_html=True)

def chat_interface():
    if not st.session_state.current_room:
        return
    
    room_data = GLOBAL_STATE.get_room(st.session_state.current_room)
    if not room_data:
        st.error("Channel not found")
        st.session_state.current_room = None
        st.rerun()
        return
    
    # Chat header
    st.markdown(f"""
    <div class="chat-header">
        <div class="room-info">
            {room_data.get('name', 'Unknown')}
            <span class="room-id">{st.session_state.current_room}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Status indicator
    st.markdown("""
    <div class="status-indicator">
        <div class="status-dot"></div>
        ENCRYPTED • LIVE
    </div>
    """, unsafe_allow_html=True)
    
    # Messages container
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    messages = room_data.get("messages", [])
    encryptor = EncryptionHandler()
    
    if not messages:
        st.markdown("""
        <div class="message">
            <div class="message-content" style="text-align: center; color: rgba(255, 255, 255, 0.5); font-style: italic;">
                No messages yet. Start the conversation...
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    for i, msg in enumerate(messages):
        try:
            # Decrypt message
            decrypted = encryptor.decrypt(msg["encrypted_message"])
            
            # Format time
            msg_time = datetime.fromtimestamp(msg["timestamp"]).strftime("%H:%M")
            
            # Chain verification
            chain_valid = True
            if i > 0:
                prev_msg = messages[i-1]
                chain_valid = msg["previous_hash"] == prev_msg["hash"]
            
            chain_status = "✓ Chain Verified" if chain_valid else "✗ Chain Broken"
            
            st.markdown(f"""
            <div class="message">
                <div class="message-header">
                    <span class="message-user">User_{msg['user_id'][-6:]}</span>
                    <span class="message-time">{msg_time}</span>
                </div>
                <div class="message-content">{decrypted}</div>
                <div class="message-meta">
                    {chain_status} • Hash: {msg['hash'][:12]}...
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        except Exception:
            st.markdown(f"""
            <div class="message">
                <div class="message-content" style="color: rgba(255, 255, 255, 0.5); font-style: italic;">
                    [Encrypted message]
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Message input
    col1, col2 = st.columns([4, 1])
    with col1:
        message = st.text_input(
            "Type your message...",
            key="message_input",
            label_visibility="collapsed"
        )
    with col2:
        send_clicked = st.button("SEND", type="primary", use_container_width=True)
    
    if send_clicked and message.strip():
        # Get previous hash
        previous_hash = "0" * 64
        if messages:
            previous_hash = messages[-1]["hash"]
        
        # Encrypt message
        encryptor = EncryptionHandler()
        encrypted_msg = encryptor.encrypt(message.strip())
        
        # Create data for hashing
        data_to_hash = f"{encrypted_msg}{previous_hash}{time.time()}"
        current_hash = encryptor.calculate_hash(data_to_hash)
        
        # Create message object
        msg_data = {
            "encrypted_message": encrypted_msg,
            "timestamp": time.time(),
            "hash": current_hash,
            "previous_hash": previous_hash,
            "user_id": st.session_state.user_id,
            "message_id": str(uuid.uuid4())
        }
        
        # Add to global state
        GLOBAL_STATE.add_message(st.session_state.current_room, msg_data)
        st.rerun()
    
    # Leave button
    if st.button("Leave Channel", type="secondary", use_container_width=True):
        st.session_state.current_room = None
        st.rerun()

def display_active_channels():
    rooms = GLOBAL_STATE.get_rooms()
    
    if not rooms:
        st.markdown("""
        <div class="join-card">
            <div style="text-align: center; color: rgba(255, 255, 255, 0.5); padding: 2rem;">
                No active channels. Create one to start.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return
    
    st.markdown('<div class="join-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title" style="margin-bottom: 1.5rem;">Active Channels</div>', unsafe_allow_html=True)
    
    for room_id, room_data in rooms.items():
        room_name = room_data.get("name", "Unknown")
        message_count = len(room_data.get("messages", []))
        created_time = datetime.fromtimestamp(room_data.get("created_at", 0)).strftime("%H:%M")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"""
            <div style="margin-bottom: 0.5rem;">
                <strong style="color: #ffffff;">{room_name}</strong><br>
                <span style="color: rgba(255, 255, 255, 0.5); font-size: 0.9rem;">ID: {room_id}</span>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            if st.button(f"Join ({message_count})", key=f"join_{room_id}"):
                st.session_state.current_room = room_id
                st.session_state.room_name = room_name
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# ====================
# MAIN APP
# ====================
def main():
    # Page config
    st.set_page_config(
        page_title="DarkRelay • Scarabynath",
        page_icon="🔒",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Inject CSS
    inject_scarabynath_css()
    
    # Render header
    render_scarabynath_header()
    
    # Initialize session
    initialize_session()
    
    # Main content
    if st.session_state.current_room:
        # Chat interface
        chat_interface()
    else:
        # Two-column layout for creation and joining
        col1, col2 = st.columns([1, 1], gap="large")
        
        with col1:
            create_room_section()
        
        with col2:
            join_room_section()
        
        # Active channels below
        st.markdown("<br><br>", unsafe_allow_html=True)
        display_active_channels()

if __name__ == "__main__":
    main()
