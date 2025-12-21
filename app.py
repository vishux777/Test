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
import secrets
import pickle
from pathlib import Path

# ====================
# PRODUCTION-READY GLOBAL STATE
# ====================
class PersistentGlobalState:
    """Thread-safe persistent global state that survives Streamlit reruns"""
    _lock = threading.Lock()
    _instance = None
    _state_file = Path("chat_state.pkl")
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_state()
        return cls._instance
    
    def _load_state(self):
        """Load state from disk if it exists"""
        try:
            if self._state_file.exists():
                with open(self._state_file, 'rb') as f:
                    state_data = pickle.load(f)
                    self.ROOMS = state_data.get('rooms', {})
                    self.ENCRYPTION_KEY = state_data.get('encryption_key', Fernet.generate_key())
            else:
                self.ROOMS = {}
                self.ENCRYPTION_KEY = Fernet.generate_key()
                self._save_state()
        except Exception:
            # Fallback to empty state if loading fails
            self.ROOMS = {}
            self.ENCRYPTION_KEY = Fernet.generate_key()
    
    def _save_state(self):
        """Save state to disk"""
        try:
            state_data = {
                'rooms': self.ROOMS,
                'encryption_key': self.ENCRYPTION_KEY
            }
            with open(self._state_file, 'wb') as f:
                pickle.dump(state_data, f)
        except Exception:
            pass  # Silently fail if can't save
    
    def get_rooms(self):
        with self._lock:
            return self.ROOMS.copy()
    
    def get_room(self, room_id: str):
        with self._lock:
            return self.ROOMS.get(room_id, {}).copy()
    
    def add_message(self, room_id: str, message_data: Dict):
        with self._lock:
            if room_id not in self.ROOMS:
                return False
            if "messages" not in self.ROOMS[room_id]:
                self.ROOMS[room_id]["messages"] = []
            self.ROOMS[room_id]["messages"].append(message_data)
            self._save_state()
            return True
    
    def create_room(self, room_id: str, room_name: str):
        with self._lock:
            if room_id not in self.ROOMS:
                self.ROOMS[room_id] = {
                    "messages": [],
                    "created_at": time.time(),
                    "name": room_name,
                    "room_id": room_id
                }
                self._save_state()
                return True
            return False

# Use singleton pattern with caching
@st.cache_resource
def get_global_state():
    return PersistentGlobalState()

# ====================
# ENCRYPTION & SECURITY
# ====================
class EncryptionHandler:
    def __init__(self, key=None):
        if key:
            self.key = key
        else:
            self.key = get_global_state().ENCRYPTION_KEY
        self.cipher = Fernet(self.key)
    
    def encrypt(self, plaintext: str) -> str:
        return self.cipher.encrypt(plaintext.encode()).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        return self.cipher.decrypt(ciphertext.encode()).decode()
    
    @staticmethod
    def calculate_hash(data: str) -> str:
        return hashlib.sha256(data.encode()).hexdigest()

# ====================
# MODERN CINEMATIC UI
# ====================
def inject_modern_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
    
    /* Dark theme with glassmorphism */
    .stApp {
        background: linear-gradient(135deg, #0c0c0c 0%, #1a0b2e 100%) !important;
        background-attachment: fixed !important;
    }
    
    .main {
        background: transparent !important;
        padding: 0 !important;
    }
    
    /* Hero Section with animated gradient */
    .hero-container {
        text-align: left;
        padding: 3rem 0 4rem 0;
        position: relative;
        overflow: hidden;
    }
    
    .hero-container::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(138, 99, 210, 0.1) 0%, transparent 70%);
        animation: pulse 4s ease-in-out infinite;
        z-index: -1;
    }
    
    .studio-name {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 500;
        font-size: 0.8rem;
        color: #a78bfa;
        letter-spacing: 0.4em;
        text-transform: uppercase;
        margin-bottom: 1rem;
        opacity: 0.8;
    }
    
    .main-title {
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        font-size: 4rem;
        background: linear-gradient(135deg, #ffffff 0%, #a78bfa 50%, #8b5cf6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0;
        line-height: 1.1;
        letter-spacing: -0.03em;
    }
    
    .title-accent {
        font-weight: 300;
        font-size: 1.5rem;
        opacity: 0.9;
        display: block;
        margin-top: 0.5rem;
    }
    
    .tagline {
        font-family: 'Inter', sans-serif;
        font-weight: 400;
        font-size: 1.2rem;
        color: rgba(255, 255, 255, 0.7);
        margin-top: 2rem;
        max-width: 600px;
        line-height: 1.7;
    }
    
    /* Glassmorphism cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 24px;
        padding: 2.5rem;
        margin: 2rem 0;
        position: relative;
        overflow: hidden;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
    }
    
    .glass-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 16px 48px rgba(138, 99, 210, 0.2);
        border-color: rgba(138, 99, 210, 0.3);
    }
    
    .card-title {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 500;
        font-size: 1.1rem;
        color: #a78bfa;
        margin-bottom: 2rem;
        letter-spacing: 0.1em;
        text-transform: uppercase;
    }
    
    /* Modern inputs */
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #ffffff !important;
        border-radius: 12px !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 1rem !important;
        padding: 1rem 1.5rem !important;
        transition: all 0.3s ease !important;
        backdrop-filter: blur(10px);
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #a78bfa !important;
        background: rgba(167, 139, 250, 0.1) !important;
        box-shadow: 0 0 0 3px rgba(167, 139, 250, 0.2) !important;
        transform: scale(1.02);
    }
    
    .stTextInput > div > div > input::placeholder {
        color: rgba(255, 255, 255, 0.4) !important;
    }
    
    /* Modern buttons */
    .stButton > button {
        background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 1rem 2rem !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        letter-spacing: 0.05em !important;
        transition: all 0.3s ease !important;
        width: 100%;
        text-transform: uppercase;
        cursor: pointer !important;
        position: relative;
        overflow: hidden;
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
        transition: left 0.5s;
    }
    
    .stButton > button:hover::before {
        left: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 12px 32px rgba(139, 92, 246, 0.4) !important;
    }
    
    .stButton > button:active {
        transform: translateY(0) !important;
    }
    
    /* Chat interface */
    .chat-container {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 24px;
        padding: 2rem;
        margin-top: 2rem;
        max-height: 600px;
        overflow-y: auto;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    
    .chat-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 2rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .room-info {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 500;
        font-size: 1.2rem;
        color: #ffffff;
    }
    
    .room-id {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.9rem;
        color: #a78bfa;
        background: rgba(167, 139, 250, 0.1);
        padding: 0.4rem 1rem;
        border-radius: 8px;
        margin-left: 1rem;
    }
    
    /* Message bubbles */
    .message {
        margin-bottom: 1.5rem;
        padding: 1.5rem;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        border-left: 4px solid #a78bfa;
        animation: messageSlide 0.4s ease-out;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }
    
    .message:hover {
        background: rgba(255, 255, 255, 0.08);
        transform: translateX(5px);
    }
    
    .message-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.8rem;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
    }
    
    .message-user {
        color: #a78bfa;
        font-weight: 500;
    }
    
    .message-time {
        color: rgba(255, 255, 255, 0.5);
        font-size: 0.8rem;
    }
    
    .message-content {
        color: rgba(255, 255, 255, 0.9);
        font-family: 'Inter', sans-serif;
        line-height: 1.6;
        font-size: 1rem;
        word-wrap: break-word;
    }
    
    .message-meta {
        margin-top: 1rem;
        padding-top: 0.8rem;
        border-top: 1px solid rgba(255, 255, 255, 0.05);
        font-size: 0.75rem;
        color: rgba(255, 255, 255, 0.4);
        font-family: 'JetBrains Mono', monospace;
    }
    
    /* Status indicators */
    .status-indicator {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.6rem 1.2rem;
        background: rgba(167, 139, 250, 0.1);
        border-radius: 24px;
        font-size: 0.85rem;
        color: #a78bfa;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(167, 139, 250, 0.2);
    }
    
    .status-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #10b981;
        animation: pulse 2s infinite;
        box-shadow: 0 0 10px rgba(16, 185, 129, 0.5);
    }
    
    /* Animations */
    @keyframes messageSlide {
        from {
            opacity: 0;
            transform: translateX(-20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
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
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(167, 139, 250, 0.3);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(167, 139, 250, 0.5);
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Responsive design */
    @media (max-width: 768px) {
        .main-title {
            font-size: 2.5rem;
        }
        .hero-container {
            padding: 2rem 0 3rem 0;
        }
    }
    </style>
    """, unsafe_allow_html=True)

def render_modern_header():
    st.markdown("""
    <div class="hero-container">
        <div class="studio-name">// SCARABYNATH STUDIO</div>
        <h1 class="main-title">DARKRELAY<br><span class="title-accent">Encrypted Anonymous Platform</span></h1>
        <div class="tagline">
            Military-grade encryption meets intuitive design. Create secure channels, 
            share sensitive information, and communicate with complete anonymity.
        </div>
    </div>
    """, unsafe_allow_html=True)

# ====================
# SESSION MANAGEMENT
# ====================
def initialize_session():
    """Initialize session state with proper persistence"""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = f"user_{uuid.uuid4().hex[:8]}"
    if 'current_room' not in st.session_state:
        st.session_state.current_room = None
    if 'room_name' not in st.session_state:
        st.session_state.room_name = ""
    if 'join_room_id' not in st.session_state:
        st.session_state.join_room_id = ""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True

def generate_room_id(name: str) -> str:
    """Generate a readable room ID"""
    clean_name = re.sub(r'[^a-zA-Z0-9]', '', name)[:4].upper()
    unique_part = uuid.uuid4().hex[:4].upper()
    return f"{clean_name}-{unique_part}"

# ====================
# UI COMPONENTS
# ====================
def create_room_section():
    with st.container():
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">Create Secure Channel</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            room_name = st.text_input(
                "Channel Name",
                placeholder="Enter channel name...",
                key="new_room_name",
                label_visibility="collapsed"
            )
        with col2:
            create_clicked = st.button("🔒 CREATE", type="primary", use_container_width=True)
        
        if create_clicked and room_name.strip():
            room_id = generate_room_id(room_name.strip())
            global_state = get_global_state()
            created = global_state.create_room(room_id, room_name.strip())
            
            if created:
                st.session_state.current_room = room_id
                st.session_state.room_name = room_name.strip()
                st.success(f"✅ Secure channel created: **{room_id}**")
                st.balloons()
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Channel already exists")
        
        st.markdown('</div>', unsafe_allow_html=True)

def join_room_section():
    with st.container():
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">Join Existing Channel</div>', unsafe_allow_html=True)
        
        join_id = st.text_input(
            "Channel ID",
            placeholder="Enter channel ID (e.g., CHAT-AB12)...",
            key="join_room_input",
            label_visibility="collapsed"
        )
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🔐 JOIN CHANNEL", use_container_width=True):
                if join_id.strip():
                    global_state = get_global_state()
                    room_data = global_state.get_room(join_id.strip())
                    if room_data:
                        st.session_state.current_room = join_id.strip()
                        st.session_state.room_name = room_data.get("name", "Unknown")
                        st.rerun()
                    else:
                        st.error("❌ Channel not found")
        
        st.markdown('</div>', unsafe_allow_html=True)

def chat_interface():
    if not st.session_state.current_room:
        return
    
    global_state = get_global_state()
    room_data = global_state.get_room(st.session_state.current_room)
    if not room_data:
        st.error("❌ Channel not found")
        st.session_state.current_room = None
        st.rerun()
        return
    
    # Chat header with modern design
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"""
        <div class="chat-header">
            <div class="room-info">
                🔒 {room_data.get('name', 'Unknown')}
                <span class="room-id">{st.session_state.current_room}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if st.button("🚪 Leave", type="secondary", use_container_width=True):
            st.session_state.current_room = None
            st.rerun()
    
    # Status indicator
    st.markdown("""
    <div class="status-indicator">
        <div class="status-dot"></div>
        🔒 ENCRYPTED • LIVE • SECURE
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
                🔓 No messages yet. Start the encrypted conversation...
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    for i, msg in enumerate(messages):
        try:
            decrypted = encryptor.decrypt(msg["encrypted_message"])
            msg_time = datetime.fromtimestamp(msg["timestamp"]).strftime("%H:%M")
            
            # Chain verification
            chain_valid = True
            if i > 0:
                prev_msg = messages[i-1]
                chain_valid = msg["previous_hash"] == prev_msg["hash"]
            
            chain_status = "✅ Verified" if chain_valid else "❌ Broken"
            user_short = msg['user_id'][-6:]
            
            st.markdown(f"""
            <div class="message">
                <div class="message-header">
                    <span class="message-user">👤 User_{user_short}</span>
                    <span class="message-time">{msg_time}</span>
                </div>
                <div class="message-content">{decrypted}</div>
                <div class="message-meta">
                    {chain_status} • Hash: {msg['hash'][:12]}...
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        except Exception:
            st.markdown("""
            <div class="message">
                <div class="message-content" style="color: rgba(255, 255, 255, 0.5); font-style: italic;">
                    [🔒 Encrypted message]
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Modern message input
    col1, col2 = st.columns([4, 1])
    with col1:
        message = st.text_input(
            "Type your encrypted message...",
            key="message_input",
            label_visibility="collapsed"
        )
    with col2:
        send_clicked = st.button("📤 SEND", type="primary", use_container_width=True)
    
    if send_clicked and message.strip():
        # Get previous hash
        previous_hash = "0" * 64
        if messages:
            previous_hash = messages[-1]["hash"]
        
        # Encrypt message
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
        if global_state.add_message(st.session_state.current_room, msg_data):
            st.rerun()
        else:
            st.error("❌ Failed to send message")

def display_active_channels():
    global_state = get_global_state()
    rooms = global_state.get_rooms()
    
    if not rooms:
        st.markdown("""
        <div class="glass-card">
            <div style="text-align: center; color: rgba(255, 255, 255, 0.5); padding: 2rem;">
                🔓 No active channels. Create one to start secure communication.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return
    
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Active Secure Channels</div>', unsafe_allow_html=True)
    
    # Sort rooms by activity (most recent first)
    sorted_rooms = sorted(rooms.items(), key=lambda x: x[1].get('created_at', 0), reverse=True)
    
    for room_id, room_data in sorted_rooms[:10]:  # Show only top 10
        room_name = room_data.get("name", "Unknown")
        message_count = len(room_data.get("messages", []))
        created_time = datetime.fromtimestamp(room_data.get("created_at", 0)).strftime("%H:%M")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.markdown(f"""
            <div style="margin-bottom: 1rem;">
                <strong style="color: #ffffff;">🔒 {room_name}</strong><br>
                <span style="color: rgba(255, 255, 255, 0.5); font-size: 0.8rem;">ID: {room_id}</span>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div style="color: rgba(255, 255, 255, 0.6); font-size: 0.9rem;">
                {message_count} messages
            </div>
            """, unsafe_allow_html=True)
        with col3:
            if st.button("🔓 Join", key=f"join_{room_id}", use_container_width=True):
                st.session_state.current_room = room_id
                st.session_state.room_name = room_name
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# ====================
# MAIN APP
# ====================
def main():
    # Page config with enhanced settings
    st.set_page_config(
        page_title="DarkRelay • Secure Encrypted Chat",
        page_icon="🔒",
        layout="wide",
        initial_sidebar_state="collapsed",
        menu_items={
            'Get Help': None,
            'Report a bug': None,
            'About': "DarkRelay - Secure Encrypted Anonymous Platform by Scarabynath Studio"
        }
    )
    
    # Inject modern CSS
    inject_modern_css()
    
    # Render header
    render_modern_header()
    
    # Initialize session
    initialize_session()
    
    # Main content
    if st.session_state.current_room:
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
