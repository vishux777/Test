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
                cls.ROOMS[room_id] = {
                    "messages": [],
                    "created_at": time.time(),
                    "name": room_id
                }
            cls.ROOMS[room_id]["messages"].append(message_data)
    
    @classmethod
    def create_room(cls, room_id: str, room_name: str):
        with cls._lock:
            if room_id not in cls.ROOMS:
                cls.ROOMS[room_id] = {
                    "messages": [],
                    "created_at": time.time(),
                    "name": room_name
                }
    
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
# CINEMATIC UI
# ====================
def inject_cinematic_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;600&display=swap');
    
    .stApp {
        background: #000000 !important;
        background-image: 
            radial-gradient(circle at 20% 50%, rgba(92, 0, 153, 0.15) 0%, transparent 50%),
            radial-gradient(circle at 80% 20%, rgba(138, 43, 226, 0.1) 0%, transparent 50%),
            radial-gradient(circle at 40% 80%, rgba(75, 0, 130, 0.1) 0%, transparent 50%);
        background-attachment: fixed;
    }
    
    .main {
        background: transparent !important;
    }
    
    /* Cinematic header */
    .cinematic-header {
        text-align: center;
        padding: 2rem 1rem;
        position: relative;
        overflow: hidden;
    }
    
    .cinematic-header::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 300px;
        height: 300px;
        background: radial-gradient(circle, rgba(138, 43, 226, 0.3) 0%, transparent 70%);
        filter: blur(40px);
        z-index: 0;
    }
    
    .cinematic-title {
        font-family: 'Orbitron', sans-serif;
        font-weight: 900;
        font-size: 4rem;
        background: linear-gradient(45deg, #8a2be2, #9400d3, #4b0082);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0;
        position: relative;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        text-shadow: 0 0 30px rgba(138, 43, 226, 0.5);
        animation: glow 3s ease-in-out infinite alternate;
    }
    
    .cinematic-subtitle {
        font-family: 'Rajdhani', sans-serif;
        font-weight: 300;
        font-size: 1.2rem;
        color: #a855f7;
        margin-top: 1rem;
        letter-spacing: 0.3em;
        text-transform: uppercase;
    }
    
    .tagline {
        font-family: 'Rajdhani', sans-serif;
        font-size: 1rem;
        color: #c084fc;
        margin-top: 0.5rem;
        opacity: 0.8;
        font-style: italic;
    }
    
    /* Core animation */
    .core-container {
        display: flex;
        justify-content: center;
        margin: 3rem 0;
        position: relative;
        height: 200px;
    }
    
    .energy-core {
        width: 150px;
        height: 150px;
        border-radius: 50%;
        position: relative;
        background: radial-gradient(circle, rgba(138, 43, 226, 0.2) 0%, transparent 70%);
        animation: pulse 4s ease-in-out infinite;
    }
    
    .energy-core::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 100%;
        height: 100%;
        border-radius: 50%;
        background: conic-gradient(from 0deg, transparent, #8a2be2, #4b0082, #8a2be2, transparent);
        animation: rotate 8s linear infinite;
        filter: blur(10px);
    }
    
    .core-inner {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: radial-gradient(circle, #ffffff, #e9d5ff);
        box-shadow: 0 0 40px 20px rgba(138, 43, 226, 0.6);
        animation: innerPulse 2s ease-in-out infinite alternate;
    }
    
    /* Room containers */
    .room-card {
        background: rgba(10, 10, 20, 0.7) !important;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(138, 43, 226, 0.3);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .room-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 2px;
        background: linear-gradient(90deg, transparent, #8a2be2, transparent);
        animation: scan 3s linear infinite;
    }
    
    .room-card:hover {
        border-color: #8a2be2;
        box-shadow: 0 0 30px rgba(138, 43, 226, 0.3);
        transform: translateY(-2px);
    }
    
    .room-title {
        font-family: 'Orbitron', sans-serif;
        color: #8a2be2;
        font-size: 1.3rem;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .room-title::before {
        content: '⟡';
        color: #a855f7;
    }
    
    /* Messages */
    .message-container {
        background: rgba(20, 20, 30, 0.8);
        border-left: 3px solid #8a2be2;
        padding: 1rem;
        margin: 0.8rem 0;
        border-radius: 0 8px 8px 0;
        animation: fadeIn 0.5s ease-out;
    }
    
    .message-header {
        display: flex;
        justify-content: space-between;
        margin-bottom: 0.5rem;
        font-family: 'Rajdhani', sans-serif;
        font-size: 0.9rem;
    }
    
    .message-user {
        color: #c084fc;
        font-weight: 600;
    }
    
    .message-time {
        color: #a78bfa;
        opacity: 0.8;
    }
    
    .message-content {
        color: #e9d5ff;
        font-family: 'Rajdhani', sans-serif;
        line-height: 1.5;
    }
    
    .hash-chain {
        font-size: 0.7rem;
        color: #8b5cf6;
        font-family: monospace;
        word-break: break-all;
        margin-top: 0.5rem;
        opacity: 0.6;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(45deg, #4b0082, #8a2be2) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 1.5rem !important;
        font-family: 'Rajdhani', sans-serif !important;
        font-weight: 600 !important;
        letter-spacing: 0.1em !important;
        transition: all 0.3s ease !important;
        text-transform: uppercase !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 5px 20px rgba(138, 43, 226, 0.4) !important;
    }
    
    .stTextInput > div > div > input {
        background: rgba(20, 20, 30, 0.8) !important;
        border: 1px solid rgba(138, 43, 226, 0.5) !important;
        color: #e9d5ff !important;
        border-radius: 8px !important;
        font-family: 'Rajdhani', sans-serif !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #8a2be2 !important;
        box-shadow: 0 0 10px rgba(138, 43, 226, 0.5) !important;
    }
    
    /* Animations */
    @keyframes glow {
        from {
            text-shadow: 0 0 20px rgba(138, 43, 226, 0.5);
        }
        to {
            text-shadow: 0 0 30px rgba(138, 43, 226, 0.8), 0 0 40px rgba(138, 43, 226, 0.4);
        }
    }
    
    @keyframes pulse {
        0%, 100% {
            transform: scale(1);
            opacity: 0.7;
        }
        50% {
            transform: scale(1.05);
            opacity: 1;
        }
    }
    
    @keyframes rotate {
        from {
            transform: translate(-50%, -50%) rotate(0deg);
        }
        to {
            transform: translate(-50%, -50%) rotate(360deg);
        }
    }
    
    @keyframes innerPulse {
        from {
            box-shadow: 0 0 40px 20px rgba(138, 43, 226, 0.6);
        }
        to {
            box-shadow: 0 0 60px 30px rgba(138, 43, 226, 0.8);
        }
    }
    
    @keyframes scan {
        0% {
            left: -100%;
        }
        100% {
            left: 100%;
        }
    }
    
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateX(-10px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        background: transparent !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        color: #a78bfa !important;
        font-family: 'Rajdhani', sans-serif !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.1em !important;
        padding: 0.5rem 1rem !important;
        border-radius: 8px !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(45deg, rgba(75, 0, 130, 0.3), rgba(138, 43, 226, 0.3)) !important;
        color: #ffffff !important;
        border-bottom: 2px solid #8a2be2 !important;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(20, 20, 30, 0.5);
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(45deg, #4b0082, #8a2be2);
        border-radius: 4px;
    }
    
    </style>
    """, unsafe_allow_html=True)

def render_cinematic_header():
    st.markdown("""
    <div class="cinematic-header">
        <h1 class="cinematic-title">DARKRELAY</h1>
        <div class="cinematic-subtitle">ANONYMOUS ENCRYPTED MESSAGING</div>
        <div class="tagline">WE TRANSCEND DIMENSIONS • BORN FOR THE FUTURE</div>
    </div>
    """, unsafe_allow_html=True)

def render_energy_core():
    st.markdown("""
    <div class="core-container">
        <div class="energy-core">
            <div class="core-inner"></div>
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

def create_or_join_room():
    col1, col2 = st.columns([3, 1])
    with col1:
        room_name = st.text_input(
            "ROOM NAME",
            value=st.session_state.room_name,
            placeholder="Enter secure room name...",
            key="room_input"
        )
    with col2:
        if st.button("ENTER", use_container_width=True):
            if room_name.strip():
                room_id = hashlib.sha256(room_name.strip().encode()).hexdigest()[:16]
                GLOBAL_STATE.create_room(room_id, room_name.strip())
                st.session_state.current_room = room_id
                st.session_state.room_name = room_name.strip()
                st.rerun()

def send_message():
    if not st.session_state.current_room:
        return
    
    col1, col2 = st.columns([4, 1])
    with col1:
        message = st.text_input(
            "MESSAGE",
            placeholder="Type encrypted message...",
            key="message_input",
            label_visibility="collapsed"
        )
    with col2:
        if st.button("SEND", use_container_width=True):
            if message.strip():
                room_data = GLOBAL_STATE.get_room(st.session_state.current_room)
                messages = room_data.get("messages", [])
                
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

def display_messages():
    if not st.session_state.current_room:
        return
    
    room_data = GLOBAL_STATE.get_room(st.session_state.current_room)
    if not room_data:
        return
    
    messages = room_data.get("messages", [])
    encryptor = EncryptionHandler()
    
    st.markdown(f"""
    <div class="room-card">
        <div class="room-title">ACTIVE TRANSMISSION • {room_data.get('name', 'Unknown').upper()}</div>
    </div>
    """, unsafe_allow_html=True)
    
    if not messages:
        st.markdown("""
        <div class="message-container">
            <div class="message-content" style="text-align: center; color: #8b5cf6; font-style: italic;">
                No messages yet. Be the first to transmit.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Display messages with chain verification
    for i, msg in enumerate(messages):
        try:
            # Decrypt message
            decrypted = encryptor.decrypt(msg["encrypted_message"])
            
            # Format time
            msg_time = datetime.fromtimestamp(msg["timestamp"]).strftime("%H:%M:%S")
            
            # Chain verification
            chain_valid = True
            if i > 0:
                prev_msg = messages[i-1]
                chain_valid = msg["previous_hash"] == prev_msg["hash"]
            
            # Display message
            chain_status = "✓" if chain_valid else "✗"
            chain_color = "#10b981" if chain_valid else "#ef4444"
            
            st.markdown(f"""
            <div class="message-container">
                <div class="message-header">
                    <span class="message-user">ANON_{msg['user_id'][-6:]}</span>
                    <span class="message-time">{msg_time}</span>
                </div>
                <div class="message-content">{decrypted}</div>
                <div class="hash-chain">
                    <span style="color: {chain_color};">CHAIN {chain_status}</span> | 
                    HASH: {msg['hash'][:16]}... | 
                    PREV: {msg['previous_hash'][:16]}...
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        except Exception as e:
            st.markdown(f"""
            <div class="message-container">
                <div class="message-content" style="color: #ef4444;">
                    [ENCRYPTED TRANSMISSION ERROR]
                </div>
            </div>
            """, unsafe_allow_html=True)

def leave_room():
    if st.session_state.current_room:
        if st.button("LEAVE TRANSMISSION", use_container_width=True, type="primary"):
            st.session_state.current_room = None
            st.rerun()

def list_rooms():
    rooms = GLOBAL_STATE.get_rooms()
    
    st.markdown("""
    <div class="room-card">
        <div class="room-title">ACTIVE TRANSMISSION CHANNELS</div>
    </div>
    """, unsafe_allow_html=True)
    
    if not rooms:
        st.markdown("""
        <div class="message-container">
            <div class="message-content" style="text-align: center; color: #8b5cf6; font-style: italic;">
                No active channels. Create one to begin.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return
    
    for room_id, room_data in rooms.items():
        room_name = room_data.get("name", "Unknown")
        message_count = len(room_data.get("messages", []))
        created_time = datetime.fromtimestamp(room_data.get("created_at", 0)).strftime("%H:%M")
        
        if st.button(
            f"JOIN: {room_name} • {message_count} MSGS • SINCE {created_time}",
            key=f"join_{room_id}",
            use_container_width=True
        ):
            st.session_state.current_room = room_id
            st.session_state.room_name = room_name
            st.rerun()

# ====================
# MAIN APP
# ====================
def main():
    # Page config
    st.set_page_config(
        page_title="DarkRelay",
        page_icon="🔒",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Inject cinematic CSS
    inject_cinematic_css()
    
    # Render header
    render_cinematic_header()
    render_energy_core()
    
    # Initialize session
    initialize_session()
    
    # Create tabs
    tab1, tab2 = st.tabs(["TRANSMIT", "CHANNELS"])
    
    with tab1:
        if st.session_state.current_room:
            # Display current room
            display_messages()
            
            # Send message
            send_message()
            
            # Leave room
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                leave_room()
        else:
            # Create or join room
            st.markdown("""
            <div class="message-container" style="text-align: center;">
                <div class="message-content">
                    INITIATE SECURE TRANSMISSION
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            create_or_join_room()
            
            # List existing rooms
            st.markdown("<br>", unsafe_allow_html=True)
            list_rooms()
    
    with tab2:
        # Channel management
        st.markdown("""
        <div class="message-container">
            <div class="message-content">
                <div style="text-align: center; margin-bottom: 1rem;">
                    <span style="color: #8a2be2; font-size: 1.2rem;">GLOBAL TRANSMISSION NETWORK</span>
                </div>
                All channels are end-to-end encrypted. Messages persist until server restart.
                Chain verification ensures message integrity across all users.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Show all rooms
        list_rooms()
        
        # Stats
        rooms = GLOBAL_STATE.get_rooms()
        total_messages = sum(len(r.get("messages", [])) for r in rooms.values())
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class="room-card" style="text-align: center;">
                <div style="color: #8a2be2; font-size: 2rem; font-family: 'Orbitron';">{len(rooms)}</div>
                <div style="color: #a855f7;">ACTIVE CHANNELS</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="room-card" style="text-align: center;">
                <div style="color: #8a2be2; font-size: 2rem; font-family: 'Orbitron';">{total_messages}</div>
                <div style="color: #a855f7;">ENCRYPTED MESSAGES</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="room-card" style="text-align: center;">
                <div style="color: #8a2be2; font-size: 2rem; font-family: 'Orbitron';">64</div>
                <div style="color: #a855f7;">BIT ENCRYPTION</div>
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
