"""
DarkRelay - Anonymous Encrypted Messaging Platform
Enhanced Version - Educational Purposes Only
"""

import streamlit as st
import hashlib
import secrets
import time
from datetime import datetime
from cryptography.fernet import Fernet
import base64

st.set_page_config(page_title="DarkRelay", page_icon="🔒", layout="wide", initial_sidebar_state="collapsed")

# ============================================================================
# CRYPTO & BLOCKCHAIN
# ============================================================================

class CryptoEngine:
    @staticmethod
    def generate_key(room_id: str) -> bytes:
        return base64.urlsafe_b64encode(hashlib.sha256(room_id.encode()).digest())
    
    @staticmethod
    def encrypt(message: str, key: bytes) -> str:
        try:
            return Fernet(key).encrypt(message.encode()).decode()
        except Exception as e:
            return "[ENCRYPTION ERROR]"
    
    @staticmethod
    def decrypt(encrypted: str, key: bytes) -> str:
        try:
            return Fernet(key).decrypt(encrypted.encode()).decode()
        except Exception as e:
            return "[DECRYPTION FAILED]"

class BlockchainVerifier:
    @staticmethod
    def compute_hash(msg: str, ts: float, prev: str, uid: str) -> str:
        return hashlib.sha256(f"{msg}{ts}{prev}{uid}".encode()).hexdigest()
    
    @staticmethod
    def verify_chain(messages: list) -> bool:
        if not messages or len(messages) <= 1:
            return True
        for i in range(1, len(messages)):
            if messages[i-1]['hash'] != messages[i]['prev_hash']:
                return False
        return True

# ============================================================================
# STATE MANAGEMENT - FIXED FOR DEPLOYMENT
# ============================================================================

def init_state():
    # Use st.session_state consistently
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.user_id = secrets.token_hex(16)
        st.session_state.username = f"Anon_{secrets.token_hex(3)}"
        st.session_state.rooms = {}
        st.session_state.current_room = None
        st.session_state.page = 'landing'
        st.session_state.msg_count = 0

# ============================================================================
# FUTURISTIC UI STYLING - INSPIRED BY SCARABYNTH
# ============================================================================

def load_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;600;700&family=Space+Grotesk:wght@300;400;600;700&display=swap');
    
    /* ========== ANIMATIONS ========== */
    
    @keyframes particleFloat {
        0%, 100% { transform: translate(0, 0) scale(1); opacity: 0.3; }
        50% { transform: translate(20px, -20px) scale(1.2); opacity: 0.6; }
    }
    
    @keyframes crystalShatter {
        0% { transform: scale(1) rotate(0deg); opacity: 1; }
        100% { transform: scale(1.5) rotate(180deg); opacity: 0; }
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    @keyframes glow {
        0%, 100% { filter: drop-shadow(0 0 20px rgba(168, 85, 247, 0.4)); }
        50% { filter: drop-shadow(0 0 40px rgba(168, 85, 247, 0.8)); }
    }
    
    @keyframes slideIn {
        from { opacity: 0; transform: translateY(30px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0px) rotate(0deg); }
        50% { transform: translateY(-20px) rotate(5deg); }
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.8; transform: scale(0.98); }
    }
    
    @keyframes scanline {
        0% { transform: translateY(-100%); }
        100% { transform: translateY(100vh); }
    }
    
    @keyframes shimmer {
        0% { background-position: -1000px 0; }
        100% { background-position: 1000px 0; }
    }
    
    /* ========== GLOBAL STYLES ========== */
    
    .stApp {
        background: #000000;
        background-image: 
            radial-gradient(circle at 20% 50%, rgba(168, 85, 247, 0.1) 0%, transparent 50%),
            radial-gradient(circle at 80% 80%, rgba(59, 130, 246, 0.1) 0%, transparent 50%),
            radial-gradient(circle at 40% 20%, rgba(139, 92, 246, 0.08) 0%, transparent 50%);
        color: #ffffff;
        font-family: 'Space Grotesk', sans-serif;
        position: relative;
        overflow-x: hidden;
    }
    
    /* Animated particles background */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: 
            radial-gradient(2px 2px at 20% 30%, rgba(168, 85, 247, 0.3), transparent),
            radial-gradient(2px 2px at 60% 70%, rgba(59, 130, 246, 0.3), transparent),
            radial-gradient(1px 1px at 50% 50%, rgba(139, 92, 246, 0.3), transparent),
            radial-gradient(1px 1px at 80% 10%, rgba(168, 85, 247, 0.3), transparent);
        background-size: 200% 200%, 200% 200%, 300% 300%, 250% 250%;
        background-position: 0% 0%, 100% 100%, 50% 50%, 0% 100%;
        animation: particleFloat 20s ease-in-out infinite;
        pointer-events: none;
        z-index: 1;
    }
    
    /* Scanline effect */
    .stApp::after {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 3px;
        background: linear-gradient(90deg, transparent, rgba(168, 85, 247, 0.8), transparent);
        animation: scanline 8s linear infinite;
        pointer-events: none;
        z-index: 9999;
    }
    
    /* ========== TYPOGRAPHY ========== */
    
    h1 {
        font-family: 'Orbitron', sans-serif;
        font-size: 5rem;
        font-weight: 900;
        background: linear-gradient(135deg, #a855f7, #3b82f6, #8b5cf6, #ec4899);
        background-size: 300% 300%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: gradientShift 8s ease infinite, glow 3s ease-in-out infinite;
        text-align: center;
        letter-spacing: 0.1em;
        margin: 3rem 0;
        position: relative;
        z-index: 10;
        text-transform: uppercase;
    }
    
    h2, h3 {
        font-family: 'Orbitron', sans-serif;
        color: #a855f7;
        font-weight: 700;
        text-shadow: 0 0 30px rgba(168, 85, 247, 0.5);
        position: relative;
        z-index: 10;
    }
    
    p, label {
        font-family: 'Space Grotesk', sans-serif;
        color: #cbd5e1;
        position: relative;
        z-index: 10;
    }
    
    /* ========== INPUT FIELDS ========== */
    
    .stTextInput input, .stTextArea textarea {
        background: rgba(15, 15, 35, 0.8) !important;
        border: 2px solid rgba(168, 85, 247, 0.3) !important;
        color: #ffffff !important;
        font-family: 'Space Grotesk', sans-serif;
        font-size: 16px;
        border-radius: 16px;
        padding: 16px 20px;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 
            0 0 20px rgba(168, 85, 247, 0.1),
            inset 0 0 20px rgba(0, 0, 0, 0.5);
        backdrop-filter: blur(10px);
    }
    
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #a855f7 !important;
        box-shadow: 
            0 0 40px rgba(168, 85, 247, 0.4),
            0 0 60px rgba(139, 92, 246, 0.2),
            inset 0 0 30px rgba(168, 85, 247, 0.1) !important;
        transform: translateY(-2px);
        background: rgba(20, 20, 45, 0.9) !important;
    }
    
    .stTextInput input::placeholder, .stTextArea textarea::placeholder {
        color: rgba(168, 85, 247, 0.4);
    }
    
    /* ========== BUTTONS - FUTURISTIC GRADIENT ========== */
    
    .stButton button {
        background: linear-gradient(135deg, #a855f7, #3b82f6, #8b5cf6) !important;
        background-size: 200% 200% !important;
        color: #ffffff !important;
        font-family: 'Orbitron', sans-serif;
        font-weight: 700;
        font-size: 16px;
        border: none !important;
        border-radius: 16px;
        padding: 20px 50px;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        text-transform: uppercase;
        letter-spacing: 0.15em;
        position: relative;
        overflow: hidden;
        box-shadow: 
            0 10px 40px rgba(168, 85, 247, 0.3),
            0 0 60px rgba(59, 130, 246, 0.2),
            inset 0 -2px 10px rgba(0, 0, 0, 0.2);
        animation: gradientShift 6s ease infinite;
    }
    
    .stButton button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
        transition: left 0.5s;
    }
    
    .stButton button:hover::before {
        left: 100%;
    }
    
    .stButton button:hover {
        transform: translateY(-4px) scale(1.05);
        box-shadow: 
            0 15px 60px rgba(168, 85, 247, 0.5),
            0 0 80px rgba(59, 130, 246, 0.3),
            inset 0 -2px 20px rgba(0, 0, 0, 0.3) !important;
    }
    
    .stButton button:active {
        transform: translateY(-2px) scale(1.02);
    }
    
    /* ========== GLASS CARDS ========== */
    
    .glass-card {
        background: rgba(15, 15, 35, 0.6);
        border: 2px solid rgba(168, 85, 247, 0.2);
        border-radius: 24px;
        padding: 40px;
        margin: 30px 0;
        backdrop-filter: blur(20px);
        box-shadow: 
            0 8px 32px rgba(168, 85, 247, 0.15),
            inset 0 0 40px rgba(0, 0, 0, 0.3);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
        animation: slideIn 0.8s ease-out;
    }
    
    .glass-card::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(45deg, transparent 30%, rgba(168, 85, 247, 0.05) 50%, transparent 70%);
        animation: float 10s ease-in-out infinite;
        pointer-events: none;
    }
    
    .glass-card:hover {
        transform: translateY(-8px);
        border-color: rgba(168, 85, 247, 0.5);
        box-shadow: 
            0 20px 60px rgba(168, 85, 247, 0.3),
            0 0 80px rgba(139, 92, 246, 0.2),
            inset 0 0 60px rgba(168, 85, 247, 0.05);
    }
    
    /* ========== FEATURE CARDS ========== */
    
    .feature-card {
        background: linear-gradient(135deg, rgba(15, 15, 35, 0.8), rgba(30, 20, 60, 0.6));
        border: 2px solid rgba(168, 85, 247, 0.3);
        border-radius: 20px;
        padding: 35px;
        margin: 25px 0;
        backdrop-filter: blur(15px);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
        box-shadow: 0 8px 32px rgba(168, 85, 247, 0.15);
        animation: slideIn 1s ease-out, float 6s ease-in-out infinite;
    }
    
    .feature-card::after {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(168, 85, 247, 0.1), transparent);
        animation: shimmer 3s infinite;
    }
    
    .feature-card:hover {
        transform: translateY(-12px) scale(1.03);
        border-color: rgba(168, 85, 247, 0.6);
        box-shadow: 
            0 20px 60px rgba(168, 85, 247, 0.3),
            0 0 80px rgba(59, 130, 246, 0.2);
    }
    
    .feature-icon {
        font-size: 3rem;
        margin-bottom: 20px;
        display: block;
        filter: drop-shadow(0 0 20px rgba(168, 85, 247, 0.6));
        animation: float 4s ease-in-out infinite;
    }
    
    .feature-title {
        font-family: 'Orbitron', sans-serif;
        font-size: 22px;
        font-weight: 700;
        color: #a855f7;
        margin: 20px 0 15px 0;
        letter-spacing: 0.05em;
        text-shadow: 0 0 20px rgba(168, 85, 247, 0.5);
    }
    
    .feature-desc {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 16px;
        color: #cbd5e1;
        line-height: 1.7;
    }
    
    /* ========== MESSAGE BUBBLES ========== */
    
    .message-bubble {
        background: linear-gradient(135deg, rgba(15, 15, 35, 0.9), rgba(30, 20, 60, 0.7));
        border-left: 4px solid #a855f7;
        border-radius: 16px;
        padding: 24px;
        margin: 20px 0;
        backdrop-filter: blur(10px);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 24px rgba(168, 85, 247, 0.15);
        animation: slideIn 0.5s ease-out;
        position: relative;
        overflow: hidden;
    }
    
    .message-bubble::before {
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        height: 100%;
        width: 4px;
        background: linear-gradient(180deg, #a855f7, #3b82f6);
        box-shadow: 0 0 20px rgba(168, 85, 247, 0.8);
    }
    
    .message-bubble:hover {
        transform: translateX(8px);
        box-shadow: 0 8px 40px rgba(168, 85, 247, 0.25);
        border-left-width: 6px;
    }
    
    .message-user {
        color: #3b82f6;
        font-weight: 700;
        font-size: 15px;
        font-family: 'Orbitron', sans-serif;
        text-shadow: 0 0 15px rgba(59, 130, 246, 0.6);
        letter-spacing: 0.05em;
        margin-bottom: 8px;
    }
    
    .message-text {
        color: #ffffff;
        font-size: 17px;
        margin: 12px 0;
        line-height: 1.6;
    }
    
    .verified-badge {
        display: inline-block;
        background: linear-gradient(135deg, #10b981, #059669);
        color: #ffffff;
        padding: 6px 14px;
        border-radius: 8px;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        box-shadow: 0 0 20px rgba(16, 185, 129, 0.5);
        animation: pulse 2s infinite;
    }
    
    /* ========== CHAT CONTAINER ========== */
    
    .chat-container {
        background: rgba(10, 10, 25, 0.8);
        border: 2px solid rgba(168, 85, 247, 0.3);
        border-radius: 20px;
        padding: 30px;
        height: 550px;
        overflow-y: auto;
        backdrop-filter: blur(20px);
        box-shadow: 
            inset 0 0 40px rgba(0, 0, 0, 0.5),
            0 0 40px rgba(168, 85, 247, 0.1);
    }
    
    .chat-container::-webkit-scrollbar {
        width: 10px;
    }
    
    .chat-container::-webkit-scrollbar-track {
        background: rgba(0, 0, 0, 0.3);
        border-radius: 10px;
    }
    
    .chat-container::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #a855f7, #3b82f6);
        border-radius: 10px;
        box-shadow: 0 0 20px rgba(168, 85, 247, 0.5);
    }
    
    /* ========== ROOM INFO ========== */
    
    .room-info {
        background: linear-gradient(135deg, rgba(15, 15, 35, 0.9), rgba(30, 20, 60, 0.8));
        border: 2px solid rgba(168, 85, 247, 0.4);
        border-radius: 20px;
        padding: 30px;
        margin: 30px 0;
        backdrop-filter: blur(20px);
        box-shadow: 0 8px 40px rgba(168, 85, 247, 0.2);
        font-family: 'Space Grotesk', sans-serif;
    }
    
    .room-info strong {
        color: #a855f7;
        text-shadow: 0 0 15px rgba(168, 85, 247, 0.6);
        font-weight: 700;
        letter-spacing: 0.05em;
    }
    
    code {
        background: rgba(168, 85, 247, 0.1);
        color: #3b82f6;
        padding: 6px 12px;
        border-radius: 8px;
        border: 1px solid rgba(168, 85, 247, 0.3);
        font-family: 'Courier New', monospace;
        font-size: 14px;
    }
    
    /* ========== WARNING & SUCCESS BOXES ========== */
    
    .warning-box {
        background: rgba(15, 5, 5, 0.9);
        border: 2px solid #ef4444;
        border-radius: 16px;
        padding: 25px;
        margin: 30px 0;
        color: #fca5a5;
        backdrop-filter: blur(10px);
        box-shadow: 0 0 40px rgba(239, 68, 68, 0.3);
        animation: pulse 3s infinite;
    }
    
    .success-box {
        background: rgba(5, 15, 5, 0.9);
        border: 2px solid #10b981;
        border-radius: 16px;
        padding: 25px;
        margin: 25px 0;
        color: #6ee7b7;
        backdrop-filter: blur(10px);
        box-shadow: 0 0 40px rgba(16, 185, 129, 0.3);
    }
    
    /* ========== SUBTITLE ========== */
    
    .subtitle {
        text-align: center;
        font-size: 1.4rem;
        color: #cbd5e1;
        margin: -20px 0 60px 0;
        font-weight: 300;
        letter-spacing: 0.2em;
        text-transform: uppercase;
        opacity: 0.8;
        animation: slideIn 1.5s ease-out;
    }
    
    /* ========== HIDE STREAMLIT ELEMENTS ========== */
    
    #MainMenu, footer, header {
        visibility: hidden;
    }
    
    .stDeployButton {
        display: none;
    }
    
    /* ========== SCROLLBAR GLOBAL ========== */
    
    ::-webkit-scrollbar {
        width: 12px;
    }
    
    ::-webkit-scrollbar-track {
        background: #000000;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #a855f7, #3b82f6);
        border-radius: 10px;
        box-shadow: 0 0 20px rgba(168, 85, 247, 0.5);
    }
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# PAGES
# ============================================================================

def landing_page():
    st.markdown('<h1>DARKRELAY</h1>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">We Transcend Dimensions</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    features = [
        ("⚡", "Zero Registration", "No email, no password, no tracking. Pure anonymity from the start."),
        ("🔒", "End-to-End Encryption", "Military-grade AES-256 encryption. Messages encrypted before storage."),
        ("⛓️", "Hash Chain Verification", "Cryptographic integrity ensures tamper-proof communication."),
        ("👤", "Complete Anonymity", "Random user IDs. No personal data collected. Zero digital footprint."),
        ("🚀", "Real-time Messaging", "Instant message delivery with live updates. Seamless experience."),
        ("🌐", "Persistent Storage", "Messages persist across sessions. Your conversations never disappear.")
    ]
    
    for i, (col, (icon, title, desc)) in enumerate(zip([col1, col2, col3] * 2, features)):
        with col:
            st.markdown(f"""
            <div class="feature-card" style="animation-delay: {i*0.15}s;">
                <span class="feature-icon">{icon}</span>
                <div class="feature-title">{title}</div>
                <div class="feature-desc">{desc}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        if st.button("🚀 CREATE ROOM", use_container_width=True, key="create_landing"):
            st.session_state.page = 'create'
            st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🔗 JOIN ROOM", use_container_width=True, key="join_landing"):
            st.session_state.page = 'join'
            st.rerun()
    
    st.markdown("""
    <div class="warning-box">
        <strong>⚠️ PROOF OF CONCEPT - EDUCATIONAL USE ONLY</strong><br><br>
        This application demonstrates advanced cryptographic concepts and secure messaging principles.
        Not intended for production use. Messages are stored in server memory only.
    </div>
    """, unsafe_allow_html=True)

def create_room_page():
    st.markdown('<h1>CREATE SECURE ROOM</h1>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Build for the Future</div>', unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="glass-card">
        <strong>Your Anonymous ID:</strong><br>
        <code>{st.session_state.user_id[:16]}...</code>
        <br><br>
        <div style="color: #94a3b8; font-size: 14px; margin-top: 15px;">
            This ID is temporary and anonymous. Share your Room ID with others to enable secure communication.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        room_name = st.text_input("Room Name (Optional)", placeholder="e.g., Project Phoenix", key="room_name_create")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("✨ GENERATE ROOM", use_container_width=True, key="gen_room"):
            room_id = secrets.token_hex(8)
            key = CryptoEngine.generate_key(room_id)
            
            genesis_hash = BlockchainVerifier.compute_hash("Room Created", time.time(), "0" * 64, "SYSTEM")
            
            st.session_state.rooms[room_id] = {
                'name': room_name if room_name.strip() else f"Room-{room_id[:8]}",
                'messages': [{
                    'user_id': 'SYSTEM',
                    'message': 'Room Created',
                    'encrypted': CryptoEngine.encrypt('Room Created', key),
                    'timestamp': time.time(),
                    'hash': genesis_hash,
                    'prev_hash': "0" * 64
                }],
                'participants': {st.session_state.user_id}
            }
            
            st.session_state.current_room = room_id
            st.session_state.page = 'chat'
            st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("← BACK TO HOME", use_container_width=True, key="back_create"):
            st.session_state.page = 'landing'
            st.rerun()

def join_room_page():
    st.markdown('<h1>JOIN SECURE ROOM</h1>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Connect to the Network</div>', unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="glass-card">
        <strong>Your Anonymous ID:</strong><br>
        <code>{st.session_state.user_id[:16]}...</code>
        <br><br>
        <div style="color: #94a3b8; font-size: 14px; margin-top: 15px;">
            Enter the 16-character Room ID shared with you to join an encrypted conversation.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        room_id = st.text_input("Room ID", placeholder="Enter 16-character Room ID", key="room_id_join", max_chars=16)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🚪 JOIN ROOM", use_container_width=True, key="join_btn"):
            if room_id and len(room_id) == 16:
                if room_id in st.session_state.rooms:
                    st.session_state.rooms[room_id]['participants'].add(st.session_state.user_id)
                    st.session_state.current_room = room_id
                    st.session_state.page = 'chat'
                    st.rerun()
                else:
                    st.markdown("""
                    <div class="warning-box">
                        ❌ <strong>Room Not Found</strong><br><br>
                        The Room ID you entered does not exist. Please verify the ID or create a new room.
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="warning-box">
                    ❌ <strong>Invalid Room ID Format</strong><br><br>
                    Room ID must be exactly 16 characters. Please check and try again.
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("← BACK TO HOME", use_container_width=True, key="back_join"):
            st.session_state.page = 'landing'
            st.rerun()

def chat_page():
    room_id = st.session_state.current_room
    
    if not room_id or room_id not in st.session_state.rooms:
        st.markdown('<div class="warning-box">❌ Room not found or has been deleted</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("← RETURN TO HOME"):
            st.session_state.page = 'landing'
            st.session_state.current_room = None
            st.rerun()
        return
    
    room = st.session_state.rooms[room_id]
    key = CryptoEngine.generate_key(room_id)
    
    # Header Section
    col1, col2, col3 = st.columns([2, 4, 2])
    
    with col1:
        if st.button("← LEAVE ROOM", key="leave_btn"):
            st.session_state.current_room = None
            st.session_state.page = 'landing'
            st.rerun()
    
    with col2:
        st.markdown(f'<h2 style="text-align: center; margin: 0;">{room["name"]}</h2>', unsafe_allow_html=True)
    
    with col3:
        if st.button("🗑️ CLEAR CHAT", key="clear_btn"):
            # Keep only genesis message
            if len(room['messages']) > 0:
                room['messages'] = [room['messages'][0]]
                st.rerun()
    
    # Room Information Panel
    chain_valid = BlockchainVerifier.verify_chain(room['messages'])
    
    st.markdown(f"""
    <div class="room-info">
        <strong>Room ID:</strong> <code>{room_id}</code> <span style="color: #94a3b8;">(Share this to invite others)</span><br><br>
        <strong>Your ID:</strong> <code>{st.session_state.user_id[:16]}...</code><br><br>
        <strong>Encryption:</strong> <span style="color: #10b981;">🔒 AES-256 Active</span> | 
        <strong>Chain Status:</strong> <span style="color: {'#10b981' if chain_valid else '#ef4444'};">{'✓ Verified' if chain_valid else '✗ Compromised'}</span><br><br>
        <strong>Total Messages:</strong> {len(room['messages'])} | 
        <strong>Active Users:</strong> {len(room['participants'])}
    </div>
    """, unsafe_allow_html=True)
    
    # Chat Container
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    if len(room['messages']) == 0:
        st.markdown("""
        <div style="text-align: center; padding: 60px 20px; color: #64748b;">
            <div style="font-size: 48px; margin-bottom: 20px;">💬</div>
            <div style="font-size: 18px;">No messages yet. Start the conversation!</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for idx, msg in enumerate(room['messages']):
            decrypted = CryptoEngine.decrypt(msg['encrypted'], key)
            ts = datetime.fromtimestamp(msg['timestamp']).strftime('%H:%M:%S')
            user = msg['user_id'][:12] + "..." if msg['user_id'] != 'SYSTEM' else '🤖 SYSTEM'
            
            # Verify message integrity
            computed_hash = BlockchainVerifier.compute_hash(
                msg['message'], 
                msg['timestamp'], 
                msg['prev_hash'], 
                msg['user_id']
            )
            verified = computed_hash == msg['hash']
            
            badge = '<span class="verified-badge">✓ VERIFIED</span>' if verified else '<span style="background: #ef4444; color: #fff; padding: 6px 14px; border-radius: 8px; font-size: 11px; font-weight: 700;">✗ INVALID</span>'
            
            st.markdown(f"""
            <div class="message-bubble" style="animation-delay: {min(idx * 0.05, 1)}s;">
                <div class="message-user">{user} {badge}</div>
                <div class="message-text">{decrypted}</div>
                <div style="color: #64748b; font-size: 12px; margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(100, 116, 139, 0.2); font-family: 'Courier New', monospace;">
                    <strong>Time:</strong> {ts} | <strong>Hash:</strong> {msg['hash'][:20]}... | <strong>Prev:</strong> {msg['prev_hash'][:20]}...
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Message Input Section
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([6, 1])
    
    with col1:
        msg_input = st.text_input(
            "Message", 
            key=f"msg_input_{st.session_state.msg_count}", 
            label_visibility="collapsed", 
            placeholder="Type your encrypted message..."
        )
    
    with col2:
        send_btn = st.button("SEND", use_container_width=True, key=f"send_{st.session_state.msg_count}")
    
    if send_btn and msg_input and msg_input.strip():
        # Get previous message hash
        prev_hash = room['messages'][-1]['hash'] if room['messages'] else "0" * 64
        
        # Create new message
        ts = time.time()
        msg_hash = BlockchainVerifier.compute_hash(
            msg_input,
            ts,
            prev_hash,
            st.session_state.user_id
        )
        
        # Encrypt and store
        encrypted = CryptoEngine.encrypt(msg_input, key)
        
        room['messages'].append({
            'user_id': st.session_state.user_id,
            'message': msg_input,
            'encrypted': encrypted,
            'timestamp': ts,
            'hash': msg_hash,
            'prev_hash': prev_hash
        })
        
        st.session_state.msg_count += 1
        st.rerun()
    
    # Auto-scroll hint
    st.markdown("""
    <div style="text-align: center; margin-top: 20px; color: #64748b; font-size: 13px;">
        Messages are end-to-end encrypted and verified via cryptographic hash chaining
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    init_state()
    load_css()
    
    # Page routing
    pages = {
        'landing': landing_page,
        'create': create_room_page,
        'join': join_room_page,
        'chat': chat_page
    }
    
    # Render current page
    current_page = st.session_state.get('page', 'landing')
    if current_page in pages:
        pages[current_page]()
    else:
        st.session_state.page = 'landing'
        st.rerun()
    
    # Footer
    st.markdown("""
    <div style="position: fixed; bottom: 0; left: 0; width: 100%; text-align: center; padding: 20px; 
                background: linear-gradient(180deg, transparent, rgba(0, 0, 0, 0.95)); 
                border-top: 1px solid rgba(168, 85, 247, 0.2); 
                font-family: 'Orbitron', sans-serif; color: #a855f7; font-size: 14px; z-index: 999;
                backdrop-filter: blur(10px);">
        Made by DE | <strong>DarkRelay v2.0</strong> | Transcending Dimensions
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
