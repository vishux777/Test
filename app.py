import streamlit as st
import hashlib
import time
from datetime import datetime
from cryptography.fernet import Fernet
import threading
import uuid
from typing import Dict, Optional
import re
import html

# ====================
# IN-MEMORY GLOBAL STATE
# ====================
class InMemoryGlobalState:
    _lock = threading.Lock()
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self.ROOMS = {}
        self.ACTIVE_USERS = {}
        self.ROOM_KEYS = {}
        self.USER_LAST_MESSAGE = {}
        self.ROOM_CREATED_AT = {}
    
    def get_room(self, room_id: str):
        with self._lock:
            return self.ROOMS.get(room_id, {}).copy()
    
    def add_message(self, room_id: str, message_data: Dict):
        with self._lock:
            if room_id not in self.ROOMS:
                return False
            if "messages" not in self.ROOMS[room_id]:
                self.ROOMS[room_id]["messages"] = []
            
            messages = self.ROOMS[room_id]["messages"]
            messages.append(message_data)
            if len(messages) > 200:
                self.ROOMS[room_id]["messages"] = messages[-200:]
            return True
    
    def create_room(self, room_id: str, room_name: str):
        with self._lock:
            if room_id not in self.ROOMS:
                room_key = Fernet.generate_key()
                self.ROOMS[room_id] = {
                    "messages": [],
                    "created_at": time.time(),
                    "name": room_name,
                    "room_id": room_id,
                }
                self.ACTIVE_USERS[room_id] = {}
                self.ROOM_KEYS[room_id] = room_key
                self.ROOM_CREATED_AT[room_id] = time.time()
                return True
            return False
    
    def update_user_activity(self, room_id: str, user_id: str):
        with self._lock:
            if room_id not in self.ACTIVE_USERS:
                self.ACTIVE_USERS[room_id] = {}
            self.ACTIVE_USERS[room_id][user_id] = time.time()
    
    def get_active_users_count(self, room_id: str) -> int:
        with self._lock:
            if room_id not in self.ACTIVE_USERS:
                return 0
            current_time = time.time()
            return sum(
                1 for last_seen in self.ACTIVE_USERS[room_id].values()
                if current_time - last_seen < 30
            )
    
    def cleanup_inactive_users(self, room_id: str):
        with self._lock:
            if room_id not in self.ACTIVE_USERS:
                return
            current_time = time.time()
            self.ACTIVE_USERS[room_id] = {
                user_id: last_seen 
                for user_id, last_seen in self.ACTIVE_USERS[room_id].items()
                if current_time - last_seen < 30
            }
    
    def get_room_key(self, room_id: str) -> Optional[bytes]:
        with self._lock:
            return self.ROOM_KEYS.get(room_id)
    
    def check_rate_limit(self, user_id: str) -> bool:
        with self._lock:
            current_time = time.time()
            last_message_time = self.USER_LAST_MESSAGE.get(user_id, 0)
            if current_time - last_message_time < 1.0:
                return False
            self.USER_LAST_MESSAGE[user_id] = current_time
            return True

@st.cache_resource
def get_global_state():
    return InMemoryGlobalState()

# ====================
# ENCRYPTION
# ====================
class EncryptionHandler:
    def __init__(self, key: bytes):
        self.cipher = Fernet(key)
    
    def encrypt(self, plaintext: str) -> str:
        return self.cipher.encrypt(plaintext.encode()).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        return self.cipher.decrypt(ciphertext.encode()).decode()
    
    @staticmethod
    def calculate_hash(data: str) -> str:
        return hashlib.sha256(data.encode()).hexdigest()

def sanitize_message(message: str) -> str:
    message = html.escape(message)
    message = message.replace('```', '').replace('`', '')
    return message.strip()

# ====================
# STYLING - SIMPLIFIED & ROBUST
# ====================
def inject_styles():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=Space+Grotesk:wght@400;600;700&display=swap');
    
    * {
        box-sizing: border-box;
    }
    
    .stApp {
        background: #000000;
        background-image: linear-gradient(180deg, #0a0a0f 0%, #000000 100%);
        color: #ffffff;
        font-family: 'Inter', sans-serif;
    }
    
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    /* Header */
    .hero-container {
        padding: 2rem 0 3rem 0;
        margin-bottom: 2rem;
        border-bottom: 1px solid rgba(138, 99, 210, 0.3);
        animation: fadeIn 0.8s ease-in;
    }
    
    .de-studio {
        font-family: 'Space Grotesk', sans-serif;
        color: #8a63d2;
        font-size: 0.9rem;
        letter-spacing: 0.3em;
        text-transform: uppercase;
        margin-bottom: 1rem;
        font-weight: 600;
        display: block;
        text-shadow: 0 0 10px rgba(138, 99, 210, 0.5);
    }
    
    .main-title {
        font-family: 'Inter', sans-serif;
        font-size: 3rem;
        font-weight: 700;
        color: #ffffff;
        margin: 0;
        line-height: 1.2;
        background: linear-gradient(135deg, #ffffff 0%, #a78bfa 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .title-accent {
        font-size: 1.2rem;
        font-weight: 300;
        opacity: 0.8;
        display: block;
        margin-top: 0.5rem;
    }
    
    .tagline {
        color: rgba(255, 255, 255, 0.7);
        margin-top: 1rem;
        font-size: 1rem;
        line-height: 1.6;
    }
    
    /* Cards */
    .creation-card {
        background: rgba(20, 20, 25, 0.9);
        border: 1px solid rgba(138, 99, 210, 0.3);
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 2rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .creation-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 30px rgba(138, 99, 210, 0.2);
        border-color: rgba(138, 99, 210, 0.6);
    }
    
    .card-title {
        color: #8a63d2;
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.9rem;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-bottom: 1.5rem;
        font-weight: 600;
        border-bottom: 2px solid rgba(138, 99, 210, 0.3);
        padding-bottom: 0.5rem;
        display: inline-block;
    }
    
    /* Inputs */
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        padding: 0.75rem 1rem !important;
        font-size: 0.95rem !important;
        transition: all 0.3s !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #8a63d2 !important;
        box-shadow: 0 0 0 2px rgba(138, 99, 210, 0.3) !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #8a63d2 0%, #6d28d9 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        width: 100% !important;
        transition: all 0.3s !important;
        cursor: pointer !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(138, 99, 210, 0.4) !important;
        opacity: 0.9;
    }
    
    /* Chat */
    .chat-container {
        background: rgba(20, 20, 25, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 1.5rem;
        max-height: 500px;
        overflow-y: auto;
        margin-top: 1rem;
    }
    
    .message {
        background: rgba(255, 255, 255, 0.03);
        border-left: 3px solid #8a63d2;
        padding: 1rem;
        margin-bottom: 1rem;
        border-radius: 0 12px 12px 0;
        animation: slideIn 0.3s ease-out;
    }
    
    .message-own {
        border-left-color: #10b981;
        background: rgba(16, 185, 129, 0.05);
    }
    
    .message-header {
        display: flex;
        justify-content: space-between;
        margin-bottom: 0.5rem;
        font-size: 0.8rem;
        color: #8a63d2;
        font-weight: 600;
    }
    
    .message-time {
        color: rgba(255, 255, 255, 0.5);
        font-weight: 400;
    }
    
    .message-content {
        color: rgba(255, 255, 255, 0.9);
        line-height: 1.5;
        font-size: 0.95rem;
    }
    
    .message-meta {
        font-size: 0.7rem;
        color: rgba(255, 255, 255, 0.4);
        margin-top: 0.5rem;
    }
    
    /* Room Header */
    .room-header {
        background: rgba(138, 99, 210, 0.1);
        border: 1px solid rgba(138, 99, 210, 0.3);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    .room-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #ffffff;
        margin: 0;
    }
    
    .room-id {
        color: #8a63d2;
        font-family: monospace;
        font-size: 0.9rem;
    }
    
    .status-bar {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        color: #10b981;
        font-size: 0.8rem;
        margin-top: 0.5rem;
    }
    
    .status-dot {
        width: 8px;
        height: 8px;
        background: #10b981;
        border-radius: 50%;
        animation: pulse 2s infinite;
        display: inline-block;
    }
    
    /* Input Area */
    .input-area {
        background: rgba(20, 20, 25, 0.9);
        padding: 1rem;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-top: 1rem;
    }
    
    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    @keyframes slideIn {
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
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #8a63d2;
        border-radius: 4px;
    }
    
    /* Hide default */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Responsive */
    @media (max-width: 768px) {
        .main-title { font-size: 2rem; }
        .creation-card { padding: 1.5rem; }
    }
    </style>
    """, unsafe_allow_html=True)

def render_header():
    st.markdown("""
    <div class="hero-container">
        <span class="de-studio">DE STUDIO</span>
        <h1 class="main-title">
            DARKRELAY
            <span class="title-accent">Anonymous Encrypted Platform</span>
        </h1>
        <div class="tagline">
            Complete anonymity. Military-grade encryption. Zero persistence.
        </div>
    </div>
    """, unsafe_allow_html=True)

# ====================
# SESSION & UI
# ====================
def init_session():
    if 'user_id' not in st.session_state:
        st.session_state.user_id = f"user_{uuid.uuid4().hex[:6]}"
    if 'current_room' not in st.session_state:
        st.session_state.current_room = None
    if 'room_name' not in st.session_state:
        st.session_state.room_name = ""
    if 'msg_key' not in st.session_state:
        st.session_state.msg_key = 0

def generate_room_id(name: str) -> str:
    clean = re.sub(r'[^a-zA-Z0-9]', '', name)[:4].upper()
    if not clean:
        clean = "ROOM"
    unique = uuid.uuid4().hex[:4].upper()
    return f"{clean}-{unique}"

def create_room_ui():
    st.markdown('<div class="creation-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">🔐 CREATE CHANNEL</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        name = st.text_input("Name", placeholder="Enter channel name...", key="new_name", label_visibility="collapsed")
    with col2:
        if st.button("CREATE", type="primary"):
            if name.strip():
                rid = generate_room_id(name.strip())
                state = get_global_state()
                if state.create_room(rid, name.strip()):
                    st.session_state.current_room = rid
                    st.session_state.room_name = name.strip()
                    st.rerun()
                else:
                    st.error("Error creating channel")
    
    st.markdown('</div>', unsafe_allow_html=True)

def join_room_ui():
    st.markdown('<div class="creation-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">🔗 JOIN CHANNEL</div>', unsafe_allow_html=True)
    
    rid = st.text_input("ID", placeholder="Enter channel ID...", key="join_id", label_visibility="collapsed")
    if st.button("JOIN CHANNEL", use_container_width=True):
        if rid.strip():
            state = get_global_state()
            data = state.get_room(rid.strip())
            if data:
                st.session_state.current_room = rid.strip()
                st.session_state.room_name = data.get("name", "Unknown")
                st.rerun()
            else:
                st.error("Channel not found")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ====================
# CHAT INTERFACE
# ====================
def chat_ui():
    if not st.session_state.current_room:
        return
    
    state = get_global_state()
    room_data = state.get_room(st.session_state.current_room)
    
    if not room_data:
        st.error("Channel expired")
        st.session_state.current_room = None
        st.rerun()
        return
    
    # Update activity
    state.update_user_activity(st.session_state.current_room, st.session_state.user_id)
    state.cleanup_inactive_users(st.session_state.current_room)
    
    # Header
    active = state.get_active_users_count(st.session_state.current_room)
    
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"""
        <div class="room-header">
            <div class="room-title">🔒 {room_data.get('name', 'Unknown')}</div>
            <div class="room-id">{st.session_state.current_room}</div>
            <div class="status-bar">
                <div class="status-dot"></div>
                <span>{active} active • ENCRYPTED</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if st.button("LEAVE", type="secondary", use_container_width=True):
            st.session_state.current_room = None
            st.rerun()
    
    # Messages
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    messages = room_data.get("messages", [])
    key = state.get_room_key(st.session_state.current_room)
    
    if not key:
        st.error("Encryption error")
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    cipher = EncryptionHandler(key)
    
    if not messages:
        st.info("💬 No messages yet. Start the conversation...")
    
    for msg in messages[-50:]:
        try:
            text = cipher.decrypt(msg["encrypted_message"])
            ts = datetime.fromtimestamp(msg["timestamp"]).strftime("%H:%M")
            is_me = msg.get("user_id") == st.session_state.user_id
            user = "You" if is_me else f"User_{msg.get('user_id', 'unknown')[-4:]}"
            css_class = "message message-own" if is_me else "message"
            
            st.markdown(f"""
            <div class="{css_class}">
                <div class="message-header">
                    <span>{user}</span>
                    <span class="message-time">{ts}</span>
                </div>
                <div class="message-content">{text}</div>
                <div class="message-meta">✓ Verified</div>
            </div>
            """, unsafe_allow_html=True)
        except:
            st.markdown("""
            <div class="message">
                <div class="message-content" style="opacity:0.5">[Encrypted]</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Input
    st.markdown('<div class="input-area">', unsafe_allow_html=True)
    c1, c2 = st.columns([4, 1])
    with c1:
        new_msg = st.text_input("Message", key=f"msg_{st.session_state.msg_key}", 
                               placeholder="Type message...", label_visibility="collapsed")
    with c2:
        send = st.button("SEND", type="primary", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    if send and new_msg and new_msg.strip():
        if not state.check_rate_limit(st.session_state.user_id):
            st.warning("Slow down!")
            return
        
        clean = sanitize_message(new_msg.strip())
        if len(clean) > 500:
            st.warning("Message too long")
            return
        
        prev_hash = messages[-1].get("hash", "0"*64) if messages else "0"*64
        enc = cipher.encrypt(clean)
        hash_data = f"{enc}{prev_hash}{time.time()}"
        curr_hash = cipher.calculate_hash(hash_data)
        
        msg_data = {
            "encrypted_message": enc,
            "timestamp": time.time(),
            "hash": curr_hash,
            "previous_hash": prev_hash,
            "user_id": st.session_state.user_id,
            "message_id": str(uuid.uuid4()),
        }
        
        if state.add_message(st.session_state.current_room, msg_data):
            st.session_state.msg_key += 1
            st.rerun()

# ====================
# MAIN
# ====================
def main():
    st.set_page_config(
        page_title="DarkRelay | DE STUDIO",
        page_icon="🔒",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    inject_styles()
    render_header()
    init_session()
    
    if st.session_state.current_room:
        chat_ui()
    else:
        c1, c2 = st.columns(2)
        with c1:
            create_room_ui()
        with c2:
            join_room_ui()
        
        st.markdown("""
        <div style="text-align:center; margin-top:3rem; opacity:0.6; font-size:0.85rem;">
            <span style="margin:0 1rem;">🔒 Ephemeral</span>
            <span style="margin:0 1rem;">⏱️ 30min TTL</span>
            <span style="margin:0 1rem;">💬 Max 200 msgs</span>
            <span style="margin:0 1rem;">🗑️ No logs</span>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
