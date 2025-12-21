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
# PRODUCTION-READY GLOBAL STATE WITH ACTIVE USER TRACKING
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
                    self.ACTIVE_USERS = state_data.get('active_users', {})  # Track active users
            else:
                self.ROOMS = {}
                self.ENCRYPTION_KEY = Fernet.generate_key()
                self.ACTIVE_USERS = {}  # room_id -> {user_id: last_seen_timestamp}
                self._save_state()
        except Exception as e:
            print(f"Error loading state: {e}")
            self.ROOMS = {}
            self.ENCRYPTION_KEY = Fernet.generate_key()
            self.ACTIVE_USERS = {}
    
    def _save_state(self):
        """Save state to disk"""
        try:
            state_data = {
                'rooms': self.ROOMS,
                'encryption_key': self.ENCRYPTION_KEY,
                'active_users': self.ACTIVE_USERS
            }
            with open(self._state_file, 'wb') as f:
                pickle.dump(state_data, f)
        except Exception as e:
            print(f"Error saving state: {e}")

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
                self.ACTIVE_USERS[room_id] = {}  # Initialize active users tracking
                self._save_state()
                return True
            return False
    
    def update_user_activity(self, room_id: str, user_id: str):
        """Update user activity timestamp"""
        with self._lock:
            if room_id not in self.ACTIVE_USERS:
                self.ACTIVE_USERS[room_id] = {}
            self.ACTIVE_USERS[room_id][user_id] = time.time()
            self._save_state()
    
    def get_active_users(self, room_id: str) -> Dict[str, float]:
        """Get active users for a room (users active in last 30 seconds)"""
        with self._lock:
            if room_id not in self.ACTIVE_USERS:
                return {}
            
            current_time = time.time()
            active_users = {}
            
            for user_id, last_seen in self.ACTIVE_USERS[room_id].items():
                if current_time - last_seen < 30:  # Active within last 30 seconds
                    active_users[user_id] = last_seen
            
            return active_users
    
    def cleanup_inactive_users(self, room_id: str):
        """Remove inactive users and return count of removed users"""
        with self._lock:
            if room_id not in self.ACTIVE_USERS:
                return 0
            
            current_time = time.time()
            original_count = len(self.ACTIVE_USERS[room_id])
            
            # Keep only users active in last 30 seconds
            self.ACTIVE_USERS[room_id] = {
                user_id: last_seen 
                for user_id, last_seen in self.ACTIVE_USERS[room_id].items()
                if current_time - last_seen < 30
            }
            
            removed_count = original_count - len(self.ACTIVE_USERS[room_id])
            self._save_state()
            return removed_count
    
    def should_cleanup_messages(self, room_id: str) -> bool:
        """Check if messages should be cleaned up (no active users)"""
        with self._lock:
            active_users = self.get_active_users(room_id)
            return len(active_users) == 0  # No active users
    
    def get_room_stats(self, room_id: str) -> Optional[Dict]:
        """Safely get room statistics"""
        with self._lock:
            try:
                if room_id in self.ROOMS:
                    room = self.ROOMS[room_id]
                    messages = room.get("messages", [])
                    return {
                        "message_count": len(messages),
                        "created_at": room.get("created_at", 0),
                        "last_activity": max([msg.get("timestamp", 0) for msg in messages], default=0)
                    }
                return None
            except Exception as e:
                print(f"Error getting room stats: {e}")
                return None
    
    def clear_room_messages(self, room_id: str) -> bool:
        """Clear all messages from a room"""
        with self._lock:
            try:
                if room_id in self.ROOMS:
                    self.ROOMS[room_id]["messages"] = []
                    self._save_state()
                    return True
                return False
            except Exception as e:
                print(f"Error clearing room messages: {e}")
                return False

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
# ENHANCED ANIMATIONS WITH SOLID MOTIONS
# ====================
def inject_smooth_animations():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    /* Pure black theme with smooth animations */
    .stApp {
        background: #000000 !important;
        background-image: 
            radial-gradient(circle at 20% 30%, rgba(138, 99, 210, 0.15) 0%, transparent 60%),
            radial-gradient(circle at 80% 70%, rgba(40, 10, 80, 0.1) 0%, transparent 60%);
        animation: backgroundPulse 15s ease-in-out infinite;
    }
    
    @keyframes backgroundPulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.95; }
    }
    
    .main {
        background: transparent !important;
    }
    
    /* Smooth cinematic hero section */
    .hero-container {
        text-align: left;
        padding: 5rem 0 6rem 0;
        position: relative;
        overflow: hidden;
        border-bottom: 1px solid rgba(138, 99, 210, 0.15);
    }
    
    /* Floating particles animation */
    .particles {
        position: absolute;
        width: 100%;
        height: 100%;
        overflow: hidden;
        pointer-events: none;
    }
    
    .particle {
        position: absolute;
        border-radius: 50%;
        animation: float 20s infinite linear;
    }
    
    @keyframes float {
        0% {
            transform: translateY(100vh) translateX(0) scale(0);
            opacity: 0;
        }
        10% {
            opacity: 1;
        }
        90% {
            opacity: 1;
        }
        100% {
            transform: translateY(-100vh) translateX(100px) scale(1.5);
            opacity: 0;
        }
    }
    
    .de-studio {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 600;
        font-size: 1rem;
        color: #8a63d2;
        letter-spacing: 0.5em;
        text-transform: uppercase;
        margin-bottom: 1.5rem;
        opacity: 0;
        animation: smoothFadeInUp 1.2s ease-out 0.3s forwards;
        text-shadow: 0 0 20px rgba(138, 99, 210, 0.5);
    }
    
    .main-title {
        font-family: 'Inter', sans-serif;
        font-weight: 900;
        font-size: 5rem;
        background: linear-gradient(135deg, #ffffff 0%, #a78bfa 40%, #8a63d2 70%, #6d28d9 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0;
        line-height: 1.1;
        letter-spacing: -0.04em;
        opacity: 0;
        animation: smoothFadeInUp 1.2s ease-out 0.6s forwards, titleGlow 4s ease-in-out infinite;
        position: relative;
    }
    
    @keyframes smoothFadeInUp {
        from {
            opacity: 0;
            transform: translateY(40px) scale(0.9);
        }
        to {
            opacity: 1;
            transform: translateY(0) scale(1);
        }
    }
    
    @keyframes titleGlow {
        0%, 100% { 
            filter: brightness(1) drop-shadow(0 0 30px rgba(138, 99, 210, 0.3));
        }
        50% { 
            filter: brightness(1.2) drop-shadow(0 0 50px rgba(138, 99, 210, 0.6));
        }
    }
    
    .title-accent {
        font-weight: 300;
        font-size: 2rem;
        opacity: 0;
        animation: smoothFadeInUp 1.2s ease-out 0.9s forwards;
        display: block;
        margin-top: 1rem;
        letter-spacing: 0.05em;
    }
    
    .tagline {
        font-family: 'Inter', sans-serif;
        font-weight: 300;
        font-size: 1.3rem;
        color: rgba(255, 255, 255, 0.8);
        margin-top: 2.5rem;
        max-width: 600px;
        line-height: 1.8;
        opacity: 0;
        animation: smoothFadeInUp 1.2s ease-out 1.2s forwards;
    }
    
    /* Smooth glass cards */
    .creation-card {
        background: rgba(15, 15, 20, 0.95);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 24px;
        padding: 3.5rem;
        margin: 3rem 0;
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(15px);
        transform: translateY(60px) scale(0.95);
        opacity: 0;
        animation: smoothSlideInUp 1s ease-out 1.5s forwards;
        box-shadow: 0 15px 50px rgba(0, 0, 0, 0.6);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .creation-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(138, 99, 210, 0.15), transparent);
        transition: left 1s ease;
    }
    
    .creation-card:hover::before {
        left: 100%;
    }
    
    .creation-card:hover {
        transform: translateY(55px) scale(0.97);
        box-shadow: 0 25px 70px rgba(138, 99, 210, 0.4);
        border-color: rgba(138, 99, 210, 0.4);
    }
    
    @keyframes smoothSlideInUp {
        to {
            transform: translateY(0) scale(1);
            opacity: 1;
        }
    }
    
    .card-title {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 600;
        font-size: 1.3rem;
        color: #8a63d2;
        margin-bottom: 2.5rem;
        letter-spacing: 0.2em;
        text-transform: uppercase;
        position: relative;
        opacity: 0;
        animation: smoothFadeIn 0.8s ease-out 1.8s forwards;
    }
    
    .card-title::after {
        content: '';
        position: absolute;
        bottom: -0.8rem;
        left: 0;
        width: 60px;
        height: 3px;
        background: linear-gradient(90deg, #8a63d2, transparent);
        animation: smoothTitleUnderline 2.5s ease-out;
    }
    
    @keyframes smoothTitleUnderline {
        from { width: 0; }
        to { width: 60px; }
    }
    
    @keyframes smoothFadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    /* Smooth animated inputs */
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.04) !important;
        border: 2px solid rgba(255, 255, 255, 0.1) !important;
        color: #ffffff !important;
        border-radius: 16px !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 1.1rem !important;
        padding: 1.2rem 1.8rem !important;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(10px);
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #8a63d2 !important;
        background: rgba(138, 99, 210, 0.08) !important;
        box-shadow: 
            0 0 0 4px rgba(138, 99, 210, 0.2),
            0 0 25px rgba(138, 99, 210, 0.4) !important;
        transform: scale(1.03);
        animation: smoothInputPulse 0.8s ease-out;
    }
    
    @keyframes smoothInputPulse {
        0% { box-shadow: 0 0 0 0 rgba(138, 99, 210, 0.6); }
        100% { box-shadow: 0 0 0 30px rgba(138, 99, 210, 0); }
    }
    
    /* Smooth animated buttons with enhanced effects */
    .stButton > button {
        background: linear-gradient(135deg, #8a63d2 0%, #6d28d9 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 16px !important;
        padding: 1.2rem 2.5rem !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        letter-spacing: 0.1em !important;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
        width: 100%;
        text-transform: uppercase;
        cursor: pointer !important;
        position: relative;
        overflow: hidden;
        transform: translateY(0);
        box-shadow: 0 6px 20px rgba(138, 99, 210, 0.4);
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 0;
        height: 0;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.4);
        transform: translate(-50%, -50%);
        transition: width 0.8s, height 0.8s;
    }
    
    .stButton > button:active::before {
        width: 400px;
        height: 400px;
    }
    
    .stButton > button:hover {
        transform: translateY(-4px) !important;
        box-shadow: 0 15px 40px rgba(138, 99, 210, 0.6) !important;
        background: linear-gradient(135deg, #946be6 0%, #7c3aed 100%) !important;
    }
    
    /* Smooth chat container with enhanced styling */
    .chat-container {
        background: rgba(15, 15, 20, 0.98);
        border: 2px solid rgba(255, 255, 255, 0.1);
        border-radius: 28px;
        padding: 3rem;
        margin-top: 3rem;
        max-height: 650px;
        overflow-y: auto;
        box-shadow: 
            inset 0 2px 0 rgba(255, 255, 255, 0.05),
            0 25px 60px rgba(0, 0, 0, 0.7);
        position: relative;
        animation: smoothChatContainerFadeIn 1.2s ease-out;
        backdrop-filter: blur(20px);
    }
    
    @keyframes smoothChatContainerFadeIn {
        from {
            opacity: 0;
            transform: scale(0.92) translateY(30px);
        }
        to {
            opacity: 1;
            transform: scale(1) translateY(0);
        }
    }
    
    /* Smooth animated messages with enhanced effects */
    .message {
        margin-bottom: 2rem;
        padding: 1.8rem;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 20px;
        border-left: 5px solid #8a63d2;
        position: relative;
        overflow: hidden;
        animation: smoothMessageSlideIn 0.8s cubic-bezier(0.4, 0, 0.2, 1);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        backdrop-filter: blur(10px);
    }
    
    .message::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(138, 99, 210, 0.2), transparent);
        animation: smoothMessageShine 3s infinite;
    }
    
    @keyframes smoothMessageShine {
        0% { left: -100%; }
        100% { left: 100%; }
    }
    
    @keyframes smoothMessageSlideIn {
        from {
            opacity: 0;
            transform: translateX(-60px) scale(0.95);
        }
        to {
            opacity: 1;
            transform: translateX(0) scale(1);
        }
    }
    
    .message:hover {
        background: rgba(255, 255, 255, 0.05);
        transform: translateX(12px) scale(1.02);
        box-shadow: 0 8px 30px rgba(138, 99, 210, 0.3);
    }
    
    /* Smooth status indicators with enhanced pulse */
    .status-indicator {
        display: inline-flex;
        align-items: center;
        gap: 1rem;
        padding: 1rem 2rem;
        background: rgba(138, 99, 210, 0.15);
        border-radius: 30px;
        font-size: 1rem;
        color: #8a63d2;
        margin-bottom: 2.5rem;
        border: 2px solid rgba(138, 99, 210, 0.3);
        animation: smoothStatusPulse 4s ease-in-out infinite;
        backdrop-filter: blur(10px);
    }
    
    @keyframes smoothStatusPulse {
        0%, 100% { 
            box-shadow: 0 0 0 0 rgba(138, 99, 210, 0.5);
            transform: scale(1);
        }
        50% { 
            box-shadow: 0 0 0 15px rgba(138, 99, 210, 0);
            transform: scale(1.08);
        }
    }
    
    .status-dot {
        width: 14px;
        height: 14px;
        border-radius: 50%;
        background: #10b981;
        animation: smoothDotPulse 3s infinite;
        box-shadow: 0 0 20px rgba(16, 185, 129, 0.8);
    }
    
    @keyframes smoothDotPulse {
        0%, 100% { 
            transform: scale(1);
            opacity: 1;
        }
        50% { 
            transform: scale(1.4);
            opacity: 0.8;
        }
    }
    
    /* Smooth custom scrollbar */
    ::-webkit-scrollbar {
        width: 12px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 6px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #8a63d2, #6d28d9);
        border-radius: 6px;
        transition: all 0.3s ease;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #a78bfa, #8a63d2);
        transform: scaleX(1.3);
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Smooth loading animation */
    .loading-dots {
        display: inline-block;
        font-weight: 500;
    }
    
    .loading-dots::after {
        content: '';
        animation: smoothLoadingDots 2s infinite;
    }
    
    @keyframes smoothLoadingDots {
        0%, 20% { content: '.'; }
        40% { content: '..'; }
        60%, 100% { content: '...'; }
    }
    </style>
    """, unsafe_allow_html=True)

def render_smooth_header():
    st.markdown("""
    <div class="hero-container">
        <div class="particles" id="particles"></div>
        <div class="de-studio">DE STUDIO</div>
        <h1 class="main-title">DARKRELAY<br><span class="title-accent">Anonymous Encrypted Platform</span></h1>
        <div class="tagline">
            Complete anonymity. Military-grade encryption. Zero compromise.
        </div>
    </div>
    
    <script>
        // Create floating particles
        document.addEventListener('DOMContentLoaded', function() {
            const particlesContainer = document.getElementById('particles');
            if (particlesContainer) {
                for (let i = 0; i < 30; i++) {
                    const particle = document.createElement('div');
                    particle.className = 'particle';
                    particle.style.left = Math.random() * 100 + '%';
                    particle.style.animationDelay = Math.random() * 20 + 's';
                    particle.style.animationDuration = (20 + Math.random() * 10) + 's';
                    particle.style.width = (Math.random() * 6 + 2) + 'px';
                    particle.style.height = particle.style.width;
                    particle.style.background = `rgba(${138 + Math.random() * 20}, ${99 + Math.random() * 20}, ${210 + Math.random() * 20}, ${Math.random() * 0.5 + 0.5})`;
                    particlesContainer.appendChild(particle);
                }
            }
        });
    </script>
    """, unsafe_allow_html=True)

# ====================
# ULTRA-FAST AUTO-UPDATE MECHANISM (0.5 SECONDS)
# ====================
class UltraFastAutoUpdater:
    def __init__(self):
        self.last_message_count = 0
        self.last_check_time = 0
        self.update_interval = 0.5  # 0.5 seconds for ultra-fast updates
    
    def check_for_updates(self, room_id: str) -> bool:
        """Check if there are new messages with ultra-fast polling"""
        global_state = get_global_state()
        room_data = global_state.get_room(room_id)
        if not room_data:
            return False
        
        current_count = len(room_data.get("messages", []))
        current_time = time.time()
        
        # Check if enough time has passed since last update
        if current_time - self.last_check_time < self.update_interval:
            return False
            
        self.last_check_time = current_time
        
        if current_count != self.last_message_count:
            self.last_message_count = current_count
            return True
        return False

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
        st.session_state.auto_updater = UltraFastAutoUpdater()
    if 'message_key' not in st.session_state:
        st.session_state.message_key = 0
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
    if 'last_activity_update' not in st.session_state:
        st.session_state.last_activity_update = 0

def generate_room_id(name: str) -> str:
    clean_name = re.sub(r'[^a-zA-Z0-9]', '', name)[:4].upper()
    unique_part = uuid.uuid4().hex[:4].upper()
    return f"{clean_name}-{unique_part}"

# ====================
# ACTIVE USERS SIDEBAR
# ====================
def display_active_users_sidebar(room_id: str):
    """Display active users in the current room"""
    if not room_id:
        return
    
    global_state = get_global_state()
    
    with st.sidebar:
        st.markdown("### 👥 Active Users")
        
        # Update current user activity
        global_state.update_user_activity(room_id, st.session_state.user_id)
        
        # Cleanup inactive users
        removed_count = global_state.cleanup_inactive_users(room_id)
        
        # Get active users
        active_users = global_state.get_active_users(room_id)
        
        if active_users:
            st.markdown(f"**{len(active_users)}** users online")
            
            for user_id, last_seen in active_users.items():
                is_current_user = user_id == st.session_state.user_id
                user_display = "👤 You" if is_current_user else f"👤 User_{user_id[-6:]}"
                status_color = "#10b981" if is_current_user else "#8a63d2"
                
                st.markdown(f"""
                <div style="
                    padding: 0.5rem 1rem; 
                    margin: 0.25rem 0; 
                    background: rgba({status_color}, 0.1); 
                    border-radius: 8px; 
                    border-left: 3px solid {status_color};
                    font-size: 0.9rem;
                ">
                    {user_display}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("*No active users*")
        
        # Check if should cleanup messages (no active users)
        if global_state.should_cleanup_messages(room_id):
            st.warning("⚠️ No active users - messages will be cleaned up")
            
            if st.button("🗑️ Clear All Messages"):
                if global_state.clear_room_messages(room_id):
                    st.success("✅ Messages cleared")
                    st.rerun()

# ====================
# UI COMPONENTS FOR ANONYMOUS PLATFORM
# ====================
def create_room_section():
    with st.container():
        st.markdown('<div class="creation-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">🔐 CREATE SECURE CHANNEL</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            room_name = st.text_input(
                "Channel Name",
                placeholder="Enter channel name...",
                key="new_room_name",
                label_visibility="collapsed"
            )
        with col2:
            create_clicked = st.button("⚡ CREATE", type="primary", use_container_width=True)
        
        if create_clicked and room_name.strip():
            room_id = generate_room_id(room_name.strip())
            global_state = get_global_state()
            created = global_state.create_room(room_id, room_name.strip())
            
            if created:
                st.session_state.current_room = room_id
                st.session_state.room_name = room_name.strip()
                st.success(f"✅ Channel created: **{room_id}**")
                st.balloons()
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("❌ Channel exists")
        
        st.markdown('</div>', unsafe_allow_html=True)

def join_room_section():
    with st.container():
        st.markdown('<div class="creation-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">🔗 JOIN CHANNEL</div>', unsafe_allow_html=True)
        
        join_id = st.text_input(
            "Channel ID",
            placeholder="Enter channel ID...",
            key="join_room_input",
            label_visibility="collapsed"
        )
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("⚡ JOIN", use_container_width=True):
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

# ====================
# ULTRA-FAST CHAT INTERFACE WITH 0.5 SECOND UPDATES
# ====================
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
    
    # Show active users sidebar
    display_active_users_sidebar(st.session_state.current_room)
    
    # Create placeholder for ultra-fast auto-updating content
    chat_placeholder = st.empty()
    
    # Ultra-fast auto-update mechanism (0.5 seconds)
    current_time = time.time()
    if current_time - st.session_state.last_activity_update >= 0.5:
        st.session_state.last_activity_update = current_time
        
        # Check for new messages
        if st.session_state.auto_updater.check_for_updates(st.session_state.current_room):
            st.rerun()
    
    # Chat header with enhanced UI
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
        if st.button("🚪 LEAVE", type="secondary", use_container_width=True):
            st.session_state.current_room = None
            st.rerun()
    
    # Enhanced status indicator
    st.markdown("""
    <div class="status-indicator">
        <div class="status-dot"></div>
        🔒 ENCRYPTED • LIVE • ANONYMOUS
    </div>
    """, unsafe_allow_html=True)
    
    # Display messages with ultra-fast updates
    with chat_placeholder.container():
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        messages = room_data.get("messages", [])
        encryptor = EncryptionHandler()
        
        # Check if should cleanup messages (no active users)
        if global_state.should_cleanup_messages(st.session_state.current_room):
            if len(messages) > 0:
                st.warning("⚠️ No active users detected - messages will be cleared when all users leave")
        
        if not messages:
            st.markdown("""
            <div class="message">
                <div class="message-content" style="text-align: center; color: rgba(255, 255, 255, 0.6); font-style: italic;">
                    🔓 No messages yet. Start the encrypted conversation...
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Display messages with smooth animations (last 50 messages)
        for i, msg in enumerate(messages[-50:]):
            try:
                decrypted = encryptor.decrypt(msg["encrypted_message"])
                msg_time = datetime.fromtimestamp(msg["timestamp"]).strftime("%H:%M:%S")
                
                # Chain verification
                chain_valid = True
                if i > 0 and i < len(messages):
                    prev_msg = messages[max(0, i-1)]
                    chain_valid = msg.get("previous_hash", "") == prev_msg.get("hash", "")
                
                chain_status = "✅ Verified" if chain_valid else "❌ Broken"
                user_short = msg.get('user_id', 'unknown')[-6:]
                is_current_user = msg.get('user_id') == st.session_state.user_id
                
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
                        {chain_status} • Hash: {msg.get('hash', 'N/A')[:8]}...
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            except Exception as e:
                st.markdown(f"""
                <div class="message">
                    <div class="message-content" style="color: rgba(255, 255, 255, 0.5); font-style: italic;">
                        [🔒 Encrypted message]
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Message input with improved clearing mechanism
    col1, col2 = st.columns([4, 1])
    with col1:
        message_key = f"message_input_{st.session_state.get('message_key', 0)}"
        message = st.text_input(
            "🔒 Type your message...",
            key=message_key,
            label_visibility="collapsed",
            placeholder="Your message is encrypted..."
        )
    with col2:
        send_clicked = st.button("⚡ SEND", type="primary", use_container_width=True)
    
    # Handle message sending with improved flow
    if send_clicked and message and message.strip():
        # Get previous hash with error handling
        previous_hash = "0" * 64
        if messages:
            previous_hash = messages[-1].get("hash", "0" * 64)
        
        # Show encryption process
        with st.spinner("🔐 Encrypting..."):
            time.sleep(0.2)  # Reduced delay for better responsiveness
            try:
                encrypted_msg = encryptor.encrypt(message.strip())
            except Exception as e:
                st.error("❌ Encryption failed")
                return
        
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
            st.toast("✅ Sent!", icon="🔒")
            # Increment key to clear input
            st.session_state.message_key = st.session_state.get('message_key', 0) + 1
            st.rerun()
        else:
            st.error("❌ Failed to send")

# ====================
# MAIN APP WITH ULTRA-FAST UPDATES
# ====================
def main():
    st.set_page_config(
        page_title="DarkRelay • DE STUDIO",
        page_icon="🔒",
        layout="wide",
        initial_sidebar_state="expanded"  # Show sidebar for active users
    )
    
    inject_smooth_animations()
    render_smooth_header()
    initialize_session()
    
    # Main content area
    main_col, sidebar_col = st.columns([4, 1])
    
    with main_col:
        if st.session_state.current_room:
            chat_interface()
        else:
            col1, col2 = st.columns([1, 1], gap="large")
            
            with col1:
                create_room_section()
            
            with col2:
                join_room_section()
            
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.markdown("""
            <div style="text-align: center; color: rgba(255, 255, 255, 0.5); padding: 2rem; font-style: italic;">
                🔒 Channels are private and not displayed for maximum anonymity
            </div>
            """, unsafe_allow_html=True)
    
    with sidebar_col:
        # Always show active users sidebar when in a room
        if st.session_state.current_room:
            display_active_users_sidebar(st.session_state.current_room)
        else:
            st.markdown("### 🔒 DarkRelay")
            st.markdown("*Join a channel to see active users*")

if __name__ == "__main__":
    main()
