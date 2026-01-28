import streamlit as st
import hashlib
import time
import random
from datetime import datetime
from cryptography.fernet import Fernet
import threading
import uuid
from typing import Dict, Optional
import re
import html

# ====================
# IN-MEMORY GLOBAL STATE (NO DISK PERSISTENCE)
# ====================
class InMemoryGlobalState:
    """Thread-safe in-memory global state - ephemeral by design"""
    _lock = threading.Lock()
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize state in memory"""
        self.ROOMS = {}
        self.ACTIVE_USERS = {}
        self.ROOM_KEYS = {}
        self.USER_LAST_MESSAGE = {}
        self.ROOM_CREATED_AT = {}
    
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
            
            # Hard limit: 200 messages per room
            messages = self.ROOMS[room_id]["messages"]
            messages.append(message_data)
            if len(messages) > 200:
                self.ROOMS[room_id]["messages"] = messages[-200:]
            
            return True
    
    def create_room(self, room_id: str, room_name: str):
        with self._lock:
            if room_id not in self.ROOMS:
                # Generate per-room encryption key
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
        """Update user activity timestamp"""
        with self._lock:
            if room_id not in self.ACTIVE_USERS:
                self.ACTIVE_USERS[room_id] = {}
            self.ACTIVE_USERS[room_id][user_id] = time.time()
    
    def get_active_users_count(self, room_id: str) -> int:
        """Get count of active users (active in last 30 seconds)"""
        with self._lock:
            if room_id not in self.ACTIVE_USERS:
                return 0
            
            current_time = time.time()
            active_count = sum(
                1 for last_seen in self.ACTIVE_USERS[room_id].values()
                if current_time - last_seen < 30
            )
            return active_count
    
    def cleanup_inactive_users(self, room_id: str):
        """Remove inactive users"""
        with self._lock:
            if room_id not in self.ACTIVE_USERS:
                return
            
            current_time = time.time()
            self.ACTIVE_USERS[room_id] = {
                user_id: last_seen 
                for user_id, last_seen in self.ACTIVE_USERS[room_id].items()
                if current_time - last_seen < 30
            }
    
    def cleanup_expired_rooms(self):
        """Remove rooms with no active users or expired TTL (30 minutes)"""
        with self._lock:
            current_time = time.time()
            rooms_to_delete = []
            
            for room_id in list(self.ROOMS.keys()):
                # Check TTL (30 minutes)
                room_age = current_time - self.ROOM_CREATED_AT.get(room_id, current_time)
                if room_age > 1800:  # 30 minutes
                    rooms_to_delete.append(room_id)
                    continue
                
                # Check active users
                active_users = {
                    user_id: last_seen 
                    for user_id, last_seen in self.ACTIVE_USERS.get(room_id, {}).items()
                    if current_time - last_seen < 30
                }
                
                if len(active_users) == 0 and room_age > 300:  # No users for 5 minutes
                    rooms_to_delete.append(room_id)
            
            # Delete expired rooms
            for room_id in rooms_to_delete:
                self.ROOMS.pop(room_id, None)
                self.ACTIVE_USERS.pop(room_id, None)
                self.ROOM_KEYS.pop(room_id, None)
                self.ROOM_CREATED_AT.pop(room_id, None)
    
    def get_room_key(self, room_id: str) -> Optional[bytes]:
        """Get encryption key for room"""
        with self._lock:
            return self.ROOM_KEYS.get(room_id)
    
    def check_rate_limit(self, user_id: str) -> bool:
        """Check if user can send message (1 second rate limit)"""
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
# ENCRYPTION & SECURITY
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
    """Strip HTML tags and prevent markdown injection"""
    message = html.escape(message)
    message = message.replace('```', '').replace('`', '')
    return message.strip()

# ====================
# COMPLETE STYLING SYSTEM WITH ADVANCED ANIMATIONS
# ====================
def inject_professional_styles():
    st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    
    <style>
    /* Core background - solid black base to prevent flash */
    .stApp {
        background-color: #000000 !important;
        background: linear-gradient(180deg, #050508 0%, #0a0a0f 50%, #000000 100%) !important;
        background-attachment: fixed !important;
        position: relative;
        overflow-x: hidden;
    }
    
    /* Floating particles animation */
    @keyframes floatUp {
        0% {
            transform: translateY(100vh) translateX(0) scale(0);
            opacity: 0;
        }
        10% {
            opacity: 0.5;
        }
        90% {
            opacity: 0.5;
        }
        100% {
            transform: translateY(-10vh) translateX(100px) scale(1);
            opacity: 0;
        }
    }
    
    @keyframes floatSide {
        0%, 100% { transform: translateX(0px); }
        50% { transform: translateX(20px); }
    }
    
    @keyframes glowPulse {
        0%, 100% {
            box-shadow: 0 0 5px rgba(138, 99, 210, 0.5),
                        0 0 10px rgba(138, 99, 210, 0.3),
                        0 0 15px rgba(138, 99, 210, 0.2);
        }
        50% {
            box-shadow: 0 0 20px rgba(138, 99, 210, 0.8),
                        0 0 30px rgba(138, 99, 210, 0.5),
                        0 0 40px rgba(138, 99, 210, 0.3);
        }
    }
    
    @keyframes neonFlicker {
        0%, 19%, 21%, 23%, 25%, 54%, 56%, 100% {
            text-shadow: 
                0 0 10px rgba(138, 99, 210, 0.8),
                0 0 20px rgba(138, 99, 210, 0.6),
                0 0 30px rgba(138, 99, 210, 0.4);
            opacity: 1;
        }
        20%, 24%, 55% {
            text-shadow: none;
            opacity: 0.8;
        }
    }
    
    @keyframes slideInUp {
        from {
            opacity: 0;
            transform: translate3d(0, 40px, 0);
        }
        to {
            opacity: 1;
            transform: translate3d(0, 0, 0);
        }
    }
    
    @keyframes fadeInScale {
        from {
            opacity: 0;
            transform: scale(0.95);
        }
        to {
            opacity: 1;
            transform: scale(1);
        }
    }
    
    @keyframes shimmer {
        0% { background-position: -200% 0; }
        100% { background-position: 200% 0; }
    }
    
    @keyframes borderRotate {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    @keyframes typingBounce {
        0%, 60%, 100% { transform: translateY(0); }
        30% { transform: translateY(-10px); }
    }
    
    /* Particle container */
    .particles {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 1;
        overflow: hidden;
    }
    
    .particle {
        position: absolute;
        width: 4px;
        height: 4px;
        background: rgba(138, 99, 210, 0.6);
        border-radius: 50%;
        box-shadow: 0 0 10px rgba(138, 99, 210, 0.8);
        animation: floatUp linear infinite;
    }
    
    /* Main content wrapper */
    .main {
        background: transparent !important;
        position: relative;
        z-index: 10;
    }
    
    block-container {
        padding-top: 2rem !important;
    }
    
    /* Hero section with entrance animation */
    .hero-container {
        text-align: left;
        padding: 3rem 0 4rem 0;
        position: relative;
        border-bottom: 1px solid rgba(138, 99, 210, 0.2);
        animation: slideInUp 0.8s ease-out;
    }
    
    .de-studio {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 600;
        font-size: 0.9rem;
        color: #8a63d2;
        letter-spacing: 0.5em;
        text-transform: uppercase;
        margin-bottom: 1.5rem;
        animation: neonFlicker 3s infinite alternate;
        display: inline-block;
    }
    
    .main-title {
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        font-size: 3.5rem;
        background: linear-gradient(135deg, #ffffff 0%, #a78bfa 40%, #8a63d2 70%, #6d28d9 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0;
        line-height: 1.1;
        letter-spacing: -0.04em;
        animation: fadeInScale 0.8s ease-out 0.2s both;
    }
    
    .title-accent {
        font-weight: 300;
        font-size: 1.5rem;
        display: block;
        margin-top: 0.5rem;
        letter-spacing: 0.05em;
        opacity: 0.9;
    }
    
    .tagline {
        font-family: 'Inter', sans-serif;
        font-weight: 300;
        font-size: 1.1rem;
        color: rgba(255, 255, 255, 0.8);
        margin-top: 1.5rem;
        max-width: 600px;
        line-height: 1.7;
        animation: slideInUp 0.8s ease-out 0.4s both;
    }
    
    /* Creation cards with hover effects */
    .creation-card {
        background: rgba(15, 15, 20, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 2rem;
        margin: 2rem 0;
        backdrop-filter: blur(20px);
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        animation: fadeInScale 0.6s ease-out;
        position: relative;
        overflow: hidden;
    }
    
    .creation-card::before {
        content: '';
        position: absolute;
        top: -2px;
        left: -2px;
        right: -2px;
        bottom: -2px;
        background: linear-gradient(45deg, #8a63d2, transparent, #8a63d2);
        border-radius: 20px;
        opacity: 0;
        z-index: -1;
        transition: opacity 0.3s;
    }
    
    .creation-card:hover::before {
        opacity: 0.5;
        animation: borderRotate 3s linear infinite;
    }
    
    .creation-card:hover {
        transform: translateY(-5px) scale(1.02);
        box-shadow: 0 15px 50px rgba(138, 99, 210, 0.3);
        border-color: rgba(138, 99, 210, 0.3);
    }
    
    .card-title {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 600;
        font-size: 1rem;
        color: #8a63d2;
        margin-bottom: 1.5rem;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        position: relative;
        display: inline-block;
    }
    
    .card-title::after {
        content: '';
        position: absolute;
        bottom: -0.5rem;
        left: 0;
        width: 50px;
        height: 2px;
        background: linear-gradient(90deg, #8a63d2, transparent);
        animation: shimmer 2s infinite;
        background-size: 200% 100%;
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        color: #ffffff !important;
        border-radius: 12px !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.95rem !important;
        padding: 0.75rem 1rem !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        backdrop-filter: blur(10px);
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #8a63d2 !important;
        background: rgba(138, 99, 210, 0.08) !important;
        box-shadow: 0 0 0 4px rgba(138, 99, 210, 0.2) !important;
        animation: glowPulse 2s infinite;
    }
    
    /* Button animations */
    .stButton > button {
        background: linear-gradient(135deg, #8a63d2 0%, #6d28d9 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.7rem 1.5rem !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        letter-spacing: 0.05em !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        width: 100%;
        text-transform: uppercase;
        cursor: pointer !important;
        position: relative;
        overflow: hidden;
        animation: fadeInScale 0.5s ease-out;
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 0;
        height: 0;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.2);
        transform: translate(-50%, -50%);
        transition: width 0.6s, height 0.6s;
    }
    
    .stButton > button:hover::before {
        width: 300px;
        height: 300px;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 10px 30px rgba(138, 99, 210, 0.5) !important;
        letter-spacing: 0.1em !important;
    }
    
    .stButton > button:active {
        transform: translateY(-1px) !important;
        transition: all 0.1s !important;
    }
    
    /* Chat container with animations */
    .chat-container {
        background: rgba(15, 15, 20, 0.95);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 1.5rem;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        max-height: 450px;
        overflow-y: auto;
        box-shadow: 0 15px 50px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        scroll-behavior: smooth;
        animation: fadeInScale 0.6s ease-out;
    }
    
    /* Message styling */
    .message {
        margin-bottom: 1.2rem;
        padding: 1rem;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 16px;
        border-left: 4px solid #8a63d2;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        backdrop-filter: blur(10px);
        animation: slideInUp 0.4s ease-out;
        position: relative;
        overflow: hidden;
    }
    
    .message::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(138, 99, 210, 0.1), transparent);
        transform: translateX(-100%);
        transition: transform 0.5s;
    }
    
    .message:hover::after {
        transform: translateX(100%);
    }
    
    .message:hover {
        background: rgba(255, 255, 255, 0.06);
        transform: translateX(8px);
        box-shadow: 0 5px 20px rgba(138, 99, 210, 0.2);
    }
    
    .message-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.7rem;
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.8rem;
    }
    
    .message-user {
        color: #8a63d2;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .message-time {
        color: rgba(255, 255, 255, 0.5);
        font-size: 0.7rem;
        font-family: 'Inter', sans-serif;
    }
    
    .message-content {
        color: rgba(255, 255, 255, 0.95);
        font-family: 'Inter', sans-serif;
        line-height: 1.6;
        margin-bottom: 0.7rem;
        word-wrap: break-word;
        font-size: 0.95rem;
    }
    
    .message-meta {
        font-size: 0.65rem;
        color: rgba(255, 255, 255, 0.4);
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-family: 'Space Grotesk', sans-serif;
    }
    
    .verify-icon {
        display: inline-block;
        animation: glowPulse 2s ease-in-out infinite;
    }
    
    /* Status indicators */
    .status-indicator {
        display: inline-flex;
        align-items: center;
        gap: 0.8rem;
        padding: 0.6rem 1.2rem;
        background: rgba(138, 99, 210, 0.1);
        border-radius: 25px;
        font-size: 0.8rem;
        color: #8a63d2;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(138, 99, 210, 0.2);
        backdrop-filter: blur(5px);
        animation: fadeInScale 0.5s ease-out;
        font-family: 'Space Grotesk', sans-serif;
        letter-spacing: 0.05em;
    }
    
    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #10b981;
        box-shadow: 0 0 10px rgba(16, 185, 129, 0.8);
        animation: glowPulse 2s infinite;
    }
    
    /* Typing indicator */
    .typing-indicator {
        display: flex;
        gap: 6px;
        padding: 1rem;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        width: fit-content;
        margin: 1rem 0;
    }
    
    .typing-dot {
        width: 8px;
        height: 8px;
        background: #8a63d2;
        border-radius: 50%;
        animation: typingBounce 1.4s infinite;
    }
    
    .typing-dot:nth-child(2) { animation-delay: 0.2s; }
    .typing-dot:nth-child(3) { animation-delay: 0.4s; }
    
    /* Room header */
    .room-header {
        background: rgba(15, 15, 20, 0.95);
        border: 1px solid rgba(138, 99, 210, 0.3);
        border-radius: 16px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        backdrop-filter: blur(20px);
        animation: slideInUp 0.5s ease-out;
        box-shadow: 0 10px 30px rgba(138, 99, 210, 0.1);
    }
    
    .room-info {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.2rem;
        color: #ffffff;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 0.8rem;
    }
    
    .room-id {
        font-size: 0.85rem;
        color: #8a63d2;
        font-weight: 400;
        margin-left: 0.5rem;
        background: rgba(138, 99, 210, 0.1);
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        border: 1px solid rgba(138, 99, 210, 0.2);
    }
    
    .user-count {
        font-size: 0.8rem;
        color: rgba(255, 255, 255, 0.6);
        margin-top: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .user-count::before {
        content: '';
        width: 6px;
        height: 6px;
        background: #10b981;
        border-radius: 50%;
        display: inline-block;
    }
    
    /* Message input area */
    .message-input-container {
        position: sticky;
        bottom: 0;
        background: rgba(5, 5, 8, 0.98);
        padding: 1rem;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(20px);
        z-index: 100;
        margin-top: 1rem;
        border-radius: 16px;
        box-shadow: 0 -10px 40px rgba(0, 0, 0, 0.5);
    }
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.02);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #8a63d2, #6d28d9);
        border-radius: 4px;
        border: 2px solid rgba(15, 15, 20, 0.95);
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #946be6, #7c3aed);
    }
    
    /* Mobile responsive */
    @media (max-width: 768px) {
        .main-title {
            font-size: 2.2rem;
        }
        
        .title-accent {
            font-size: 1.1rem;
        }
        
        .chat-container {
            max-height: 350px;
        }
        
        .creation-card {
            padding: 1.5rem;
        }
        
        .hero-container {
            padding: 2rem 0 3rem 0;
        }
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Success/Error message animations */
    .stAlert {
        animation: slideInUp 0.4s ease-out;
        border-radius: 12px !important;
        backdrop-filter: blur(10px) !important;
    }
    
    /* Expanding effect for new messages */
    @keyframes highlightNew {
        0% {
            background: rgba(138, 99, 210, 0.3);
            transform: scale(1.02);
        }
        100% {
            background: rgba(255, 255, 255, 0.03);
            transform: scale(1);
        }
    }
    
    .new-message {
        animation: highlightNew 1s ease-out;
    }
    </style>
    
    <!-- Floating particles -->
    <div class="particles" id="particles"></div>
    
    <script>
        // Generate floating particles
        const particleContainer = document.getElementById('particles');
        const particleCount = 20;
        
        for (let i = 0; i < particleCount; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';
            particle.style.left = Math.random() * 100 + '%';
            particle.style.animationDuration = (Math.random() * 10 + 10) + 's';
            particle.style.animationDelay = Math.random() * 10 + 's';
            particle.style.opacity = Math.random() * 0.5;
            particleContainer.appendChild(particle);
        }
    </script>
    """, unsafe_allow_html=True)

def render_header():
    st.markdown("""
    <div class="hero-container">
        <div class="de-studio">DE STUDIO</div>
        <h1 class="main-title">DARKRELAY<br><span class="title-accent">Anonymous Encrypted Platform</span></h1>
        <div class="tagline">
            Complete anonymity. Military-grade encryption. Zero compromise. 
            <span style="color: #8a63d2; font-weight: 500;">Ephemeral by design.</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ====================
# OPTIMIZED AUTO-UPDATE (2 SECOND POLLING)
# ====================
class OptimizedAutoUpdater:
    def __init__(self):
        self.last_message_count = 0
        self.last_check_time = 0
        self.update_interval = 2.0  # 2 seconds for optimized polling
    
    def should_update(self, room_id: str) -> bool:
        """Check if UI should update based on message count change"""
        try:
            global_state = get_global_state()
            room_data = global_state.get_room(room_id)
            if not room_data:
                return False
            
            current_count = len(room_data.get("messages", []))
            current_time = time.time()
            
            # Only check at intervals
            if current_time - self.last_check_time < self.update_interval:
                return False
                
            self.last_check_time = current_time
            
            # Update only if message count changed
            if current_count != self.last_message_count:
                self.last_message_count = current_count
                return True
            return False
        except Exception:
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
        st.session_state.auto_updater = OptimizedAutoUpdater()
    if 'message_key' not in st.session_state:
        st.session_state.message_key = 0
    if 'page_refresh' not in st.session_state:
        st.session_state.page_refresh = 0

def generate_room_id(name: str) -> str:
    clean_name = re.sub(r'[^a-zA-Z0-9]', '', name)[:4].upper()
    if not clean_name:
        clean_name = "ROOM"
    unique_part = uuid.uuid4().hex[:4].upper()
    return f"{clean_name}-{unique_part}"

# ====================
# UI COMPONENTS
# ====================
def create_room_section():
    with st.container():
        st.markdown('<div class="creation-card">', unsafe_for_html=True)
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
            create_clicked = st.button("⚡ CREATE", type="primary", use_container_width=True, key="create_btn")
        
        if create_clicked and room_name.strip():
            room_id = generate_room_id(room_name.strip())
            global_state = get_global_state()
            created = global_state.create_room(room_id, room_name.strip())
            
            if created:
                st.session_state.current_room = room_id
                st.session_state.room_name = room_name.strip()
                st.success(f"✅ Channel created: **{room_id}**")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("❌ Channel ID collision. Try again.")
        
        st.markdown('</div>', unsafe_allow_html=True)

def join_room_section():
    with st.container():
        st.markdown('<div class="creation-card">', unsafe_for_html=True)
        st.markdown('<div class="card-title">🔗 JOIN CHANNEL</div>', unsafe_allow_html=True)
        
        join_id = st.text_input(
            "Channel ID",
            placeholder="Enter channel ID...",
            key="join_room_input",
            label_visibility="collapsed"
        )
        
        if st.button("⚡ JOIN", use_container_width=True, key="join_btn"):
            if join_id.strip():
                global_state = get_global_state()
                room_data = global_state.get_room(join_id.strip())
                if room_data:
                    st.session_state.current_room = join_id.strip()
                    st.session_state.room_name = room_data.get("name", "Unknown")
                    st.rerun()
                else:
                    st.error("❌ Channel not found or expired")
        
        st.markdown('</div>', unsafe_for_html=True)

# ====================
# OPTIMIZED CHAT INTERFACE
# ====================
def chat_interface():
    if not st.session_state.current_room:
        return
    
    try:
        global_state = get_global_state()
        room_data = global_state.get_room(st.session_state.current_room)
        if not room_data:
            st.error("❌ Channel not found or expired")
            st.session_state.current_room = None
            time.sleep(0.5)
            st.rerun()
            return
        
        # Update user activity
        global_state.update_user_activity(st.session_state.current_room, st.session_state.user_id)
        
        # Cleanup inactive users and expired rooms periodically
        global_state.cleanup_inactive_users(st.session_state.current_room)
        global_state.cleanup_expired_rooms()
        
        # Optimized auto-update (2 seconds)
        if st.session_state.auto_updater.should_update(st.session_state.current_room):
            st.rerun()
        
        # Chat header with room info
        col1, col2 = st.columns([3, 1])
        with col1:
            active_count = global_state.get_active_users_count(st.session_state.current_room)
            st.markdown(f"""
            <div class="room-header">
                <div class="room-info">
                    🔒 {room_data.get('name', 'Unknown')}
                    <span class="room-id">{st.session_state.current_room}</span>
                </div>
                <div class="user-count">{active_count} active user{'s' if active_count != 1 else ''}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            if st.button("🚪 LEAVE", type="secondary", use_container_width=True, key="leave_btn"):
                st.session_state.current_room = None
                st.rerun()
        
        # Status indicator
        st.markdown("""
        <div class="status-indicator">
            <div class="status-dot"></div>
            🔒 ENCRYPTED • LIVE • ANONYMOUS
        </div>
        """, unsafe_allow_html=True)
        
        # Chat messages container
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        messages = room_data.get("messages", [])
        room_key = global_state.get_room_key(st.session_state.current_room)
        
        if not room_key:
            st.error("❌ Encryption key not found")
            st.markdown('</div>', unsafe_allow_html=True)
            return
        
        encryptor = EncryptionHandler(room_key)
        
        if not messages:
            st.markdown("""
            <div class="message">
                <div class="message-content" style="text-align: center; color: rgba(255, 255, 255, 0.6); font-style: italic; padding: 2rem 0;">
                    🔓 No messages yet. Start the encrypted conversation...
                    <div style="margin-top: 1rem; font-size: 0.8rem; color: rgba(255,255,255,0.4);">
                        Messages auto-delete after 30 minutes of inactivity
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Display last 50 messages with chain verification
        for i, msg in enumerate(messages[-50:]):
            try:
                decrypted = encryptor.decrypt(msg["encrypted_message"])
                msg_time = datetime.fromtimestamp(msg["timestamp"]).strftime("%H:%M")
                
                # Chain verification
                chain_valid = True
                if i > 0:
                    prev_msg = messages[-50:][i-1]
                    chain_valid = msg.get("previous_hash", "") == prev_msg.get("hash", "")
                
                verify_icon = '<span class="verify-icon">✓</span>' if chain_valid else '⚠'
                user_short = msg.get('user_id', 'unknown')[-4:]
                is_current_user = msg.get('user_id') == st.session_state.user_id
                
                # Different styling for own messages
                border_color = "#10b981" if is_current_user else "#8a63d2"
                user_label = "👤 You" if is_current_user else f"👤 User_{user_short}"
                
                st.markdown(f"""
                <div class="message" style="border-left-color: {border_color};">
                    <div class="message-header">
                        <span class="message-user">{user_label}</span>
                        <span class="message-time">{msg_time}</span>
                    </div>
                    <div class="message-content">{decrypted}</div>
                    <div class="message-meta">
                        {verify_icon} Verified • Chain: {msg.get('hash', 'N/A')[:6]}...
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            except Exception:
                st.markdown(f"""
                <div class="message" style="border-left-color: #ef4444;">
                    <div class="message-content" style="color: rgba(255, 255, 255, 0.5); font-style: italic;">
                        [🔒 Unable to decrypt message]
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Sticky message input
        st.markdown('<div class="message-input-container">', unsafe_allow_html=True)
        col1, col2 = st.columns([5, 1])
        with col1:
            message_key = f"message_input_{st.session_state.get('message_key', 0)}"
            message = st.text_input(
                "🔒 Type your message...",
                key=message_key,
                label_visibility="collapsed",
                placeholder="Type your encrypted message here...",
                on_change=None
            )
        with col2:
            send_clicked = st.button("⚡ SEND", type="primary", use_container_width=True, key="send_btn")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Handle message sending with rate limiting
        if send_clicked and message and message.strip():
            # Check rate limit
            if not global_state.check_rate_limit(st.session_state.user_id):
                st.warning("⚠️ Please wait before sending another message (1 second cooldown)")
                st.stop()
            
            # Sanitize message
            sanitized_message = sanitize_message(message.strip())
            
            if len(sanitized_message) > 500:
                st.warning("⚠️ Message too long (max 500 characters)")
                st.stop()
            
            # Get previous hash for blockchain effect
            previous_hash = "0" * 64
            if messages:
                previous_hash = messages[-1].get("hash", "0" * 64)
            
            try:
                encrypted_msg = encryptor.encrypt(sanitized_message)
            except Exception:
                st.error("❌ Encryption failed")
                st.stop()
            
            # Create hash chain
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
            }
            
            # Add to global state
            if global_state.add_message(st.session_state.current_room, msg_data):
                st.session_state.message_key = st.session_state.get('message_key', 0) + 1
                st.rerun()
            else:
                st.error("❌ Failed to send message")
    
    except Exception as e:
        st.error(f"❌ Error in chat interface: {str(e)}")
        if st.button("🔄 Reset Application", key="reset_error"):
            st.session_state.current_room = None
            st.rerun()

# ====================
# MAIN APP
# ====================
def main():
    try:
        st.set_page_config(
            page_title="DarkRelay • DE STUDIO",
            page_icon="🔒",
            layout="wide",
            initial_sidebar_state="collapsed"
        )
        
        inject_professional_styles()
        render_header()
        initialize_session()
        
        if st.session_state.current_room:
            chat_interface()
        else:
            # Landing page layout
            col1, col2 = st.columns([1, 1], gap="large")
            
            with col1:
                create_room_section()
            
            with col2:
                join_room_section()
            
            # Security notice
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("""
            <div style="text-align: center; padding: 3rem 0; animation: fadeInScale 1s ease-out 0.6s both;">
                <div style="display: inline-flex; gap: 2rem; flex-wrap: wrap; justify-content: center; color: rgba(255, 255, 255, 0.6); font-size: 0.85rem; font-family: 'Space Grotesk', sans-serif;">
                    <span style="display: flex; align-items: center; gap: 0.5rem;">
                        <span style="width: 8px; height: 8px; background: #8a63d2; border-radius: 50%; box-shadow: 0 0 10px rgba(138, 99, 210, 0.8);"></span>
                        Ephemeral Channels
                    </span>
                    <span style="display: flex; align-items: center; gap: 0.5rem;">
                        <span style="width: 8px; height: 8px; background: #10b981; border-radius: 50%; box-shadow: 0 0 10px rgba(16, 185, 129, 0.8);"></span>
                        30 Min TTL
                    </span>
                    <span style="display: flex; align-items: center; gap: 0.5rem;">
                        <span style="width: 8px; height: 8px; background: #f59e0b; border-radius: 50%; box-shadow: 0 0 10px rgba(245, 158, 11, 0.8);"></span>
                        Max 200 Messages
                    </span>
                    <span style="display: flex; align-items: center; gap: 0.5rem;">
                        <span style="width: 8px; height: 8px; background: #ef4444; border-radius: 50%; box-shadow: 0 0 10px rgba(239, 68, 68, 0.8);"></span>
                        In-Memory Only
                    </span>
                </div>
                <div style="margin-top: 1.5rem; color: rgba(255, 255, 255, 0.4); font-size: 0.75rem; font-style: italic;">
                    No logs. No traces. Zero persistence.
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"Application Error: {str(e)}")
        st.info("Please refresh the page or contact support if the issue persists.")
        if st.button("🔄 Reload Application"):
            st.session_state.clear()
            st.rerun()

if __name__ == "__main__":
    main()
