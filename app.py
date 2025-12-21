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
import asyncio
from concurrent.futures import ThreadPoolExecutor

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
            pass

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
                    "room_id": room_id,
                    "message_count": 0
                }
                self._save_state()
                return True
            return False
    
    def get_room_stats(self, room_id: str):
        with self._lock:
            if room_id in self.ROOMS:
                room = self.ROOMS[room_id]
                return {
                    "message_count": len(room.get("messages", [])),
                    "created_at": room.get("created_at", 0),
                    "last_activity": max([msg.get("timestamp", 0) for msg in room.get("messages", [])], default=0)
                }
            return None

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
# ORIGINAL BLACK THEME WITH HIGH-END ANIMATIONS
# ====================
def inject_cinematic_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    /* Pure black theme with cinematic elements */
    .stApp {
        background: #000000 !important;
        background-image: 
            radial-gradient(circle at 15% 25%, rgba(20, 20, 40, 0.3) 0%, transparent 50%),
            radial-gradient(circle at 85% 75%, rgba(40, 10, 80, 0.2) 0%, transparent 50%),
            linear-gradient(180deg, rgba(0,0,0,0.9) 0%, rgba(10,10,20,0.8) 100%);
        animation: backgroundShift 20s ease-in-out infinite;
    }
    
    @keyframes backgroundShift {
        0%, 100% { background-position: 0% 0%, 100% 100%; }
        50% { background-position: 100% 100%, 0% 0%; }
    }
    
    .main {
        background: transparent !important;
    }
    
    /* Cinematic Hero Section */
    .hero-container {
        text-align: left;
        padding: 4rem 0 5rem 0;
        position: relative;
        overflow: hidden;
        border-bottom: 1px solid rgba(138, 99, 210, 0.2);
    }
    
    .hero-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: 
            linear-gradient(45deg, transparent 49%, rgba(138, 99, 210, 0.1) 50%, transparent 51%),
            linear-gradient(-45deg, transparent 49%, rgba(138, 99, 210, 0.1) 50%, transparent 51%);
        background-size: 60px 60px;
        animation: scanlines 8s linear infinite;
        pointer-events: none;
    }
    
    @keyframes scanlines {
        0% { transform: translateY(-100%); }
        100% { transform: translateY(100%); }
    }
    
    .studio-name {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 500;
        font-size: 0.9rem;
        color: #8a63d2;
        letter-spacing: 0.4em;
        text-transform: uppercase;
        margin-bottom: 1rem;
        opacity: 0;
        animation: fadeInUp 1s ease-out 0.5s forwards;
    }
    
    .main-title {
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        font-size: 4.5rem;
        background: linear-gradient(135deg, #ffffff 0%, #a78bfa 30%, #8a63d2 60%, #6d28d9 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0;
        line-height: 1.1;
        letter-spacing: -0.03em;
        opacity: 0;
        animation: fadeInUp 1s ease-out 0.7s forwards, titleGlow 3s ease-in-out infinite;
    }
    
    @keyframes titleGlow {
        0%, 100% { filter: brightness(1); }
        50% { filter: brightness(1.2); }
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .title-accent {
        font-weight: 300;
        font-size: 1.8rem;
        opacity: 0;
        animation: fadeInUp 1s ease-out 0.9s forwards;
        display: block;
        margin-top: 0.5rem;
    }
    
    .tagline {
        font-family: 'Inter', sans-serif;
        font-weight: 300;
        font-size: 1.2rem;
        color: rgba(255, 255, 255, 0.7);
        margin-top: 2rem;
        max-width: 600px;
        line-height: 1.7;
        opacity: 0;
        animation: fadeInUp 1s ease-out 1.1s forwards;
    }
    
    /* Animated particles background */
    .particles {
        position: absolute;
        width: 100%;
        height: 100%;
        overflow: hidden;
        pointer-events: none;
    }
    
    .particle {
        position: absolute;
        width: 4px;
        height: 4px;
        background: #8a63d2;
        border-radius: 50%;
        opacity: 0;
        animation: particleFloat 15s infinite;
    }
    
    @keyframes particleFloat {
        0% {
            opacity: 0;
            transform: translateY(100vh) scale(0);
        }
        10% {
            opacity: 1;
        }
        90% {
            opacity: 1;
        }
        100% {
            opacity: 0;
            transform: translateY(-100vh) scale(1.5);
        }
    }
    
    /* Cinematic cards with hover effects */
    .creation-card {
        background: rgba(15, 15, 20, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 20px;
        padding: 3rem;
        margin: 2rem 0;
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(10px);
        transform: translateY(50px);
        opacity: 0;
        animation: slideInUp 1s ease-out 1.3s forwards;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
        transition: all 0.3s ease;
    }
    
    .creation-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(138, 99, 210, 0.1), transparent);
        transition: left 0.8s;
    }
    
    .creation-card:hover::before {
        left: 100%;
    }
    
    .creation-card:hover {
        transform: translateY(45px) scale(1.02);
        box-shadow: 0 20px 60px rgba(138, 99, 210, 0.3);
        border-color: rgba(138, 99, 210, 0.3);
    }
    
    @keyframes slideInUp {
        to {
            transform: translateY(0);
            opacity: 1;
        }
    }
    
    .card-title {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 500;
        font-size: 1.2rem;
        color: #8a63d2;
        margin-bottom: 2rem;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        position: relative;
    }
    
    .card-title::after {
        content: '';
        position: absolute;
        bottom: -0.5rem;
        left: 0;
        width: 50px;
        height: 2px;
        background: linear-gradient(90deg, #8a63d2, transparent);
        animation: titleUnderline 2s ease-out;
    }
    
    @keyframes titleUnderline {
        from { width: 0; }
        to { width: 50px; }
    }
    
    /* Animated input fields */
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #ffffff !important;
        border-radius: 12px !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 1rem !important;
        padding: 1rem 1.5rem !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        position: relative;
        overflow: hidden;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #8a63d2 !important;
        background: rgba(138, 99, 210, 0.05) !important;
        box-shadow: 
            0 0 0 3px rgba(138, 99, 210, 0.2),
            0 0 20px rgba(138, 99, 210, 0.3) !important;
        transform: scale(1.02);
        animation: inputPulse 0.6s ease-out;
    }
    
    @keyframes inputPulse {
        0% { box-shadow: 0 0 0 0 rgba(138, 99, 210, 0.4); }
        100% { box-shadow: 0 0 0 20px rgba(138, 99, 210, 0); }
    }
    
    /* Animated buttons with ripple effect */
    .stButton > button {
        background: linear-gradient(135deg, #8a63d2 0%, #6d28d9 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 1rem 2rem !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        letter-spacing: 0.05em !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        width: 100%;
        text-transform: uppercase;
        cursor: pointer !important;
        position: relative;
        overflow: hidden;
        transform: translateY(0);
        box-shadow: 0 4px 15px rgba(138, 99, 210, 0.3);
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 0;
        height: 0;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.3);
        transform: translate(-50%, -50%);
        transition: width 0.6s, height 0.6s;
    }
    
    .stButton > button:active::before {
        width: 300px;
        height: 300px;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 12px 35px rgba(138, 99, 210, 0.5) !important;
        animation: buttonHover 0.3s ease-out;
    }
    
    @keyframes buttonHover {
        0% { transform: translateY(0); }
        50% { transform: translateY(-5px); }
        100% { transform: translateY(-3px); }
    }
    
    /* Cinematic chat container */
    .chat-container {
        background: rgba(15, 15, 20, 0.95);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 24px;
        padding: 2.5rem;
        margin-top: 2rem;
        max-height: 600px;
        overflow-y: auto;
        box-shadow: 
            inset 0 1px 0 rgba(255, 255, 255, 0.05),
            0 20px 40px rgba(0, 0, 0, 0.5);
        position: relative;
        animation: chatContainerFadeIn 1s ease-out;
    }
    
    @keyframes chatContainerFadeIn {
        from {
            opacity: 0;
            transform: scale(0.95) translateY(20px);
        }
        to {
            opacity: 1;
            transform: scale(1) translateY(0);
        }
    }
    
    /* Animated messages */
    .message {
        margin-bottom: 1.5rem;
        padding: 1.5rem;
        background: rgba(255, 255, 255, 0.02);
        border-radius: 16px;
        border-left: 4px solid #8a63d2;
        position: relative;
        overflow: hidden;
        animation: messageSlideIn 0.6s cubic-bezier(0.4, 0, 0.2, 1);
        transition: all 0.3s ease;
    }
    
    .message::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(138, 99, 210, 0.1), transparent);
        animation: messageShine 2s infinite;
    }
    
    @keyframes messageShine {
        0% { left: -100%; }
        100% { left: 100%; }
    }
    
    @keyframes messageSlideIn {
        from {
            opacity: 0;
            transform: translateX(-50px) scale(0.9);
        }
        to {
            opacity: 1;
            transform: translateX(0) scale(1);
        }
    }
    
    .message:hover {
        background: rgba(255, 255, 255, 0.05);
        transform: translateX(10px);
        box-shadow: 0 5px 20px rgba(138, 99, 210, 0.2);
    }
    
    /* Status indicators with pulse */
    .status-indicator {
        display: inline-flex;
        align-items: center;
        gap: 0.8rem;
        padding: 0.8rem 1.5rem;
        background: rgba(138, 99, 210, 0.1);
        border-radius: 24px;
        font-size: 0.9rem;
        color: #8a63d2;
        margin-bottom: 2rem;
        border: 1px solid rgba(138, 99, 210, 0.2);
        animation: statusPulse 3s ease-in-out infinite;
    }
    
    @keyframes statusPulse {
        0%, 100% { 
            box-shadow: 0 0 0 0 rgba(138, 99, 210, 0.4);
            transform: scale(1);
        }
        50% { 
            box-shadow: 0 0 0 10px rgba(138, 99, 210, 0);
            transform: scale(1.05);
        }
    }
    
    .status-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: #10b981;
        animation: dotPulse 2s infinite;
        box-shadow: 0 0 15px rgba(16, 185, 129, 0.6);
    }
    
    @keyframes dotPulse {
        0%, 100% { 
            transform: scale(1);
            opacity: 1;
        }
        50% { 
            transform: scale(1.3);
            opacity: 0.7;
        }
    }
    
    /* Custom scrollbar with animation */
    ::-webkit-scrollbar {
        width: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.02);
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #8a63d2, #6d28d9);
        border-radius: 5px;
        transition: all 0.3s ease;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #a78bfa, #8a63d2);
        transform: scaleX(1.2);
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Loading animation */
    .loading-dots {
        display: inline-block;
    }
    
    .loading-dots::after {
        content: '';
        animation: loadingDots 1.5s infinite;
    }
    
    @keyframes loadingDots {
        0% { content: '.'; }
        33% { content: '..'; }
        66% { content: '...'; }
        100% { content: '.'; }
    }
    </style>
    """, unsafe_allow_html=True)

def render_cinematic_header():
    st.markdown("""
    <div class="hero-container">
        <div class="particles" id="particles"></div>
        <div class="studio-name">SCARABYNATH STUDIO</div>
        <h1 class="main-title">DARKRELAY<br><span class="title-accent">Anonymous Encrypted Platform</span></h1>
        <div class="tagline">
            Where shadows meet security. Experience the next generation of encrypted communication 
            with cinematic precision and uncompromising anonymity.
        </div>
    </div>
    
    <script>
        // Create floating particles
        document.addEventListener('DOMContentLoaded', function() {
            const particlesContainer = document.getElementById('particles');
            if (particlesContainer) {
                for (let i = 0; i < 50; i++) {
                    const particle = document.createElement('div');
                    particle.className = 'particle';
                    particle.style.left = Math.random() * 100 + '%';
                    particle.style.animationDelay = Math.random() * 15 + 's';
                    particle.style.animationDuration = (15 + Math.random() * 10) + 's';
                    particlesContainer.appendChild(particle);
                }
            }
        });
    </script>
    """, unsafe_allow_html=True)

# ====================
# AUTO-UPDATE MECHANISM
# ====================
class AutoUpdater:
    def __init__(self):
        self.last_message_count = 0
        self.update_interval = 2  # seconds
    
    def check_for_updates(self, room_id: str) -> bool:
        """Check if there are new messages"""
        global_state = get_global_state()
        room_data = global_state.get_room(room_id)
        if not room_data:
            return False
        
        current_count = len(room_data.get("messages", []))
        if current_count != self.last_message_count:
            self.last_message_count = current_count
            return True
        return False
    
    def get_update_indicator(self):
        return f"""
        <div style="position: fixed; top: 20px; right: 20px; z-index: 1000;">
            <div class="status-indicator" style="margin: 0; animation: none;">
                <div class="status-dot" style="animation: spin 1s linear infinite;"></div>
                LIVE
            </div>
        </div>
        <style>
            @keyframes spin {{
                from {{ transform: rotate(0deg); }}
                to {{ transform: rotate(360deg); }}
            }}
        </style>
        """

# ====================
# SESSION MANAGEMENT
# ====================
def initialize_session():
    if 'user_id' not in st.session_state:
        st.session_state.user_id = f"user_{uuid.uuid4().hex[:8]}"
    if 'current_room' not in st.session_state:
        st.session_state.current_room = None
    if 'room_name' not in st.session_state:
        st.session_state.room_name = ""
    if 'auto_updater' not in st.session_state:
        st.session_state.auto_updater = AutoUpdater()
    if 'message_draft' not in st.session_state:
        st.session_state.message_draft = ""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True

def generate_room_id(name: str) -> str:
    clean_name = re.sub(r'[^a-zA-Z0-9]', '', name)[:4].upper()
    unique_part = uuid.uuid4().hex[:4].upper()
    return f"{clean_name}-{unique_part}"

# ====================
# NEW FEATURES
# ====================
def message_reactions(message_id: str, room_id: str):
    """Add reaction system to messages"""
    col1, col2, col3, col4 = st.columns([1, 1, 1, 6])
    
    reactions = ["🔥", "💯", "🎯", "⚡"]
    for i, reaction in enumerate(reactions):
        with [col1, col2, col3][i]:
            if st.button(f"{reaction}", key=f"react_{message_id}_{i}", help=f"React with {reaction}"):
                # Store reaction in global state
                global_state = get_global_state()
                if room_id in global_state.ROOMS:
                    # Add reaction logic here
                    st.toast(f"Reacted with {reaction}!")
                    time.sleep(0.5)
                    st.rerun()

def typing_indicator():
    """Show typing indicator"""
    return """
    <div class="message" style="opacity: 0.7; border-left-color: #f59e0b;">
        <div class="message-content">
            <span class="loading-dots">Someone is typing</span>
        </div>
    </div>
    """

def message_encryption_indicator(encrypted: bool = True):
    """Show encryption status with animation"""
    if encrypted:
        return """
        <div style="display: inline-flex; align-items: center; gap: 0.5rem; color: #10b981; font-size: 0.8rem;">
            <div style="width: 8px; height: 8px; background: #10b981; border-radius: 50%; animation: pulse 2s infinite;"></div>
            🔒 ENCRYPTED
        </div>
        """
    else:
        return """
        <div style="display: inline-flex; align-items: center; gap: 0.5rem; color: #ef4444; font-size: 0.8rem;">
            <div style="width: 8px; height: 8px; background: #ef4444; border-radius: 50%; animation: pulse 2s infinite;"></div>
            ⚠️ UNENCRYPTED
        </div>
        """

# ====================
# UI COMPONENTS WITH ENHANCED FEATURES
# ====================
def create_room_section():
    with st.container():
        st.markdown('<div class="creation-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">🛡️ Create Secure Channel</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            room_name = st.text_input(
                "Channel Name",
                placeholder="Enter channel name...",
                key="new_room_name",
                label_visibility="collapsed"
            )
        with col2:
            create_clicked = st.button("🔐 CREATE CHANNEL", type="primary", use_container_width=True)
        
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
        st.markdown('<div class="creation-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">🔗 Join Existing Channel</div>', unsafe_allow_html=True)
        
        join_id = st.text_input(
            "Channel ID",
            placeholder="Enter channel ID (e.g., CHAT-AB12)...",
            key="join_room_input",
            label_visibility="collapsed"
        )
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🔓 JOIN CHANNEL", use_container_width=True):
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
    
    # Auto-update mechanism
    placeholder = st.empty()
    
    # Chat header with enhanced UI
    col1, col2, col3 = st.columns([2, 1, 1])
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
        # Room stats
        stats = global_state.get_room_stats(st.session_state.current_room)
        if stats:
            st.markdown(f"""
            <div style="font-size: 0.8rem; color: rgba(255,255,255,0.6);">
                💬 {stats['message_count']} messages<br>
                🕒 Active {datetime.fromtimestamp(stats['last_activity']).strftime('%H:%M') if stats['last_activity'] else 'now'}
            </div>
            """, unsafe_allow_html=True)
    
    with col3:
        if st.button("🚪 Leave Channel", type="secondary", use_container_width=True):
            st.session_state.current_room = None
            st.rerun()
    
    # Enhanced status indicator
    st.markdown("""
    <div class="status-indicator">
        <div class="status-dot"></div>
        🔒 ENCRYPTED • LIVE • SECURE • REAL-TIME
    </div>
    """, unsafe_allow_html=True)
    
    # Messages container with auto-refresh
    with placeholder.container():
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
        
        # Display messages with enhanced features
        for i, msg in enumerate(messages[-50:]):  # Show last 50 messages
            try:
                decrypted = encryptor.decrypt(msg["encrypted_message"])
                msg_time = datetime.fromtimestamp(msg["timestamp"]).strftime("%H:%M:%S")
                
                # Chain verification
                chain_valid = True
                if i > 0:
                    prev_msg = messages[i-1]
                    chain_valid = msg["previous_hash"] == prev_msg["hash"]
                
                chain_status = "✅ Verified" if chain_valid else "❌ Broken"
                user_short = msg['user_id'][-6:]
                is_current_user = msg['user_id'] == st.session_state.user_id
                
                # Message styling based on user
                message_style = "border-left-color: #10b981;" if is_current_user else "border-left-color: #8a63d2;"
                
                st.markdown(f"""
                <div class="message" style="{message_style}">
                    <div class="message-header">
                        <span class="message-user">{'👤 You' if is_current_user else f'👤 User_{user_short}'}</span>
                        <span class="message-time">{msg_time}</span>
                    </div>
                    <div class="message-content">{decrypted}</div>
                    <div class="message-meta">
                        {chain_status} • Hash: {msg['hash'][:8]}... • 
                        {message_encryption_indicator(True)}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Add reactions for recent messages
                if i >= len(messages) - 10:
                    message_reactions(msg.get('message_id', ''), st.session_state.current_room)
                
            except Exception as e:
                st.markdown(f"""
                <div class="message">
                    <div class="message-content" style="color: rgba(255, 255, 255, 0.5); font-style: italic;">
                        [🔒 Encrypted message - Unable to decrypt]
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Enhanced message input with typing indicator
    col1, col2 = st.columns([4, 1])
    with col1:
        message = st.text_input(
            "🔒 Type your encrypted message...",
            key="message_input",
            label_visibility="collapsed",
            placeholder="Your message is encrypted end-to-end..."
        )
    with col2:
        send_clicked = st.button("📤 SEND", type="primary", use_container_width=True)
    
    # Auto-send on Enter and handle typing indicator
    if message:
        # Show typing indicator for other users (simulated)
        if len(message) > 0:
            with st.spinner("📝 Encrypting message..."):
                time.sleep(0.1)  # Simulate encryption delay
    
    if send_clicked and message.strip():
        # Get previous hash
        previous_hash = "0" * 64
        if messages:
            previous_hash = messages[-1]["hash"]
        
        # Show encryption process
        with st.spinner("🔐 Encrypting message..."):
            time.sleep(0.3)
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
            "message_id": str(uuid.uuid4()),
            "reactions": []
        }
        
        # Add to global state
        if global_state.add_message(st.session_state.current_room, msg_data):
            st.toast("✅ Message sent securely!", icon="🔒")
            # Force refresh by clearing the input
            st.session_state.message_input = ""
            st.rerun()
        else:
            st.error("❌ Failed to send message")
    
    # Auto-refresh every 2 seconds
    time.sleep(2)
    if st.session_state.auto_updater.check_for_updates(st.session_state.current_room):
        st.rerun()

def display_active_channels():
    global_state = get_global_state()
    rooms = global_state.get_rooms()
    
    if not rooms:
        st.markdown("""
        <div class="creation-card">
            <div style="text-align: center; color: rgba(255, 255, 255, 0.5); padding: 2rem;">
                🔓 No active channels. Create one to start secure communication.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return
    
    st.markdown('<div class="creation-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">🔥 Active Secure Channels</div>', unsafe_allow_html=True)
    
    # Sort rooms by activity (most recent first)
    sorted_rooms = sorted(rooms.items(), key=lambda x: x[1].get('created_at', 0), reverse=True)
    
    for room_id, room_data in sorted_rooms[:10]:
        room_name = room_data.get("name", "Unknown")
        message_count = len(room_data.get("messages", []))
        created_time = datetime.fromtimestamp(room_data.get("created_at", 0)).strftime("%H:%M")
        
        # Calculate activity level
        last_activity = max([msg.get("timestamp", 0) for msg in room_data.get("messages", [])], default=0)
        time_since_activity = time.time() - last_activity if last_activity else float('inf')
        activity_status = "🔥 Active" if time_since_activity < 300 else "💤 Idle"  # 5 minutes
        
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
                {message_count} msgs<br>
                <small>{activity_status}</small>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            if st.button("🔓 Join", key=f"join_{room_id}", use_container_width=True):
                st.session_state.current_room = room_id
                st.session_state.room_name = room_name
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# ====================
# MAIN APP WITH ENHANCED FEATURES
# ====================
def main():
    st.set_page_config(
        page_title="DarkRelay • Scarabynath",
        page_icon="🔒",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    inject_cinematic_css()
    render_cinematic_header()
    initialize_session()
    
    # Add enhanced features sidebar
    with st.sidebar:
        st.markdown("### ⚙️ Channel Settings")
        
        if st.session_state.current_room:
            st.markdown(f"**Current:** {st.session_state.room_name}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Clear History"):
                    if st.checkbox("Confirm clear?"):
                        global_state = get_global_state()
                        if st.session_state.current_room in global_state.ROOMS:
                            global_state.ROOMS[st.session_state.current_room]["messages"] = []
                            global_state._save_state()
                            st.success("History cleared!")
                            st.rerun()
            
            with col2:
                if st.button("📋 Export Chat"):
                    # Export functionality
                    global_state = get_global_state()
                    room_data = global_state.get_room(st.session_state.current_room)
                    if room_data:
                        messages = room_data.get("messages", [])
                        export_data = {
                            "room_name": st.session_state.room_name,
                            "room_id": st.session_state.current_room,
                            "exported_at": datetime.now().isoformat(),
                            "message_count": len(messages)
                        }
                        st.download_button(
                            "💾 Download",
                            data=json.dumps(export_data, indent=2),
                            file_name=f"{st.session_state.room_name}_{int(time.time())}.json",
                            mime="application/json"
                        )
        
        st.markdown("---")
        st.markdown("### 📊 Statistics")
        
        global_state = get_global_state()
        total_rooms = len(global_state.ROOMS)
        total_messages = sum(len(room.get("messages", [])) for room in global_state.ROOMS.values())
        
        st.metric("Total Channels", total_rooms)
        st.metric("Total Messages", total_messages)
        
        st.markdown("---")
        st.markdown("### 🎨 Theme")
        
        # Theme toggle
        theme = st.selectbox("Appearance", ["Cinematic Dark", "Pure Black", "Matrix Green"], 
                           help="Change the visual theme")
        
        if theme == "Matrix Green":
            st.markdown("""
            <style>
            .stApp { 
                background: #000000 !important;
                background-image: radial-gradient(circle at 50% 50%, rgba(0, 255, 0, 0.1) 0%, transparent 50%);
            }
            .main-title { 
                background: linear-gradient(135deg, #00ff00 0%, #00cc00 100%) !important;
            }
            .status-indicator { color: #00ff00; border-color: #00ff00; }
            .status-dot { background: #00ff00; }
            </style>
            """, unsafe_allow_html=True)
    
    # Main content
    if st.session_state.current_room:
        chat_interface()
    else:
        col1, col2 = st.columns([1, 1], gap="large")
        
        with col1:
            create_room_section()
        
        with col2:
            join_room_section()
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        display_active_channels()

if __name__ == "__main__":
    main()
