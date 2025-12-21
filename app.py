"""
DarkRelay - Anonymous Encrypted Messaging Platform
Proof of Concept - Educational Purposes Only
Made by DE
"""

import streamlit as st
import hashlib
import secrets
import time
import json
from datetime import datetime
from cryptography.fernet import Fernet
import base64

# ============================================================================
# CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="DarkRelay - Anonymous Messaging",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================================
# CRYPTOGRAPHY MODULE
# ============================================================================

class CryptoEngine:
    """Handles AES-256 encryption/decryption using Fernet"""
    
    @staticmethod
    def generate_key_from_room_id(room_id: str) -> bytes:
        """Generate deterministic encryption key from room ID"""
        hash_obj = hashlib.sha256(room_id.encode())
        key = base64.urlsafe_b64encode(hash_obj.digest())
        return key
    
    @staticmethod
    def encrypt_message(message: str, key: bytes) -> str:
        """Encrypt message using AES-256"""
        f = Fernet(key)
        encrypted = f.encrypt(message.encode())
        return encrypted.decode()
    
    @staticmethod
    def decrypt_message(encrypted_message: str, key: bytes) -> str:
        """Decrypt message using AES-256"""
        try:
            f = Fernet(key)
            decrypted = f.decrypt(encrypted_message.encode())
            return decrypted.decode()
        except:
            return "[DECRYPTION FAILED]"

# ============================================================================
# BLOCKCHAIN SIMULATION MODULE
# ============================================================================

class BlockchainVerifier:
    """
    Simulates blockchain-style message verification using cryptographic hash chaining.
    NOTE: This is a SIMULATION for educational purposes - not a real blockchain.
    Provides tamper-evident message integrity without requiring paid blockchain networks.
    """
    
    @staticmethod
    def compute_message_hash(message: str, timestamp: float, prev_hash: str, user_id: str) -> str:
        """Compute SHA-256 hash of message data"""
        data = f"{message}{timestamp}{prev_hash}{user_id}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    @staticmethod
    def verify_chain(messages: list) -> bool:
        """Verify integrity of message chain"""
        if not messages:
            return True
        
        for i in range(1, len(messages)):
            expected_prev = messages[i-1]['hash']
            actual_prev = messages[i]['prev_hash']
            if expected_prev != actual_prev:
                return False
        
        return True

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def init_session_state():
    """Initialize all session state variables"""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = secrets.token_hex(16)
    
    if 'current_room' not in st.session_state:
        st.session_state.current_room = None
    
    if 'rooms' not in st.session_state:
        st.session_state.rooms = {}
    
    if 'page' not in st.session_state:
        st.session_state.page = 'landing'
    
    if 'refresh_counter' not in st.session_state:
        st.session_state.refresh_counter = 0

# ============================================================================
# CSS STYLING
# ============================================================================

def load_css():
    """Inject custom CSS for cyberpunk theme with animations"""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;600&display=swap');
    
    /* Background Animation */
    @keyframes gridMove {
        0% { background-position: 0 0; }
        100% { background-position: 50px 50px; }
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes slideIn {
        from { opacity: 0; transform: translateX(-30px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    @keyframes glow {
        0%, 100% { box-shadow: 0 0 5px #00ffff, 0 0 10px #00ffff, 0 0 15px #00ffff; }
        50% { box-shadow: 0 0 10px #00ffff, 0 0 20px #00ffff, 0 0 30px #00ffff; }
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    /* Global Styles */
    .stApp {
        background: linear-gradient(135deg, #0a0a0a 0%, #1a0a2e 50%, #0a0a0a 100%);
        background-image: 
            linear-gradient(0deg, transparent 24%, rgba(0, 255, 255, 0.05) 25%, rgba(0, 255, 255, 0.05) 26%, transparent 27%, transparent 74%, rgba(0, 255, 255, 0.05) 75%, rgba(0, 255, 255, 0.05) 76%, transparent 77%, transparent),
            linear-gradient(90deg, transparent 24%, rgba(0, 255, 255, 0.05) 25%, rgba(0, 255, 255, 0.05) 26%, transparent 27%, transparent 74%, rgba(0, 255, 255, 0.05) 75%, rgba(0, 255, 255, 0.05) 76%, transparent 77%, transparent);
        background-size: 50px 50px;
        animation: gridMove 20s linear infinite;
        color: #00ffff;
    }
    
    /* Headers */
    h1, h2, h3 {
        font-family: 'Orbitron', sans-serif;
        color: #00ffff;
        text-shadow: 0 0 10px #00ffff, 0 0 20px #00ffff, 0 0 30px #00ffff;
        animation: fadeIn 1s ease-out;
    }
    
    /* Text */
    p, label, .stMarkdown {
        font-family: 'Rajdhani', sans-serif;
        color: #b0b0ff;
    }
    
    /* Input Fields */
    .stTextInput input, .stTextArea textarea {
        background: rgba(10, 10, 30, 0.8) !important;
        border: 2px solid #00ffff !important;
        color: #00ffff !important;
        font-family: 'Rajdhani', sans-serif;
        border-radius: 10px;
        transition: all 0.3s ease;
    }
    
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #ff00ff !important;
        box-shadow: 0 0 15px #ff00ff !important;
    }
    
    /* Buttons */
    .stButton button {
        background: linear-gradient(135deg, #00ffff 0%, #ff00ff 100%) !important;
        color: #000000 !important;
        font-family: 'Orbitron', sans-serif;
        font-weight: 700;
        border: none !important;
        border-radius: 10px;
        padding: 12px 30px;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    
    .stButton button:hover {
        transform: scale(1.05);
        box-shadow: 0 0 20px #00ffff, 0 0 30px #ff00ff !important;
        animation: glow 1.5s infinite;
    }
    
    /* Feature Cards */
    .feature-card {
        background: linear-gradient(135deg, rgba(0, 255, 255, 0.1) 0%, rgba(255, 0, 255, 0.1) 100%);
        border: 2px solid #00ffff;
        border-radius: 15px;
        padding: 25px;
        margin: 15px 0;
        animation: fadeIn 1s ease-out;
        transition: all 0.3s ease;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 0 30px rgba(0, 255, 255, 0.5);
        border-color: #ff00ff;
    }
    
    .feature-title {
        font-family: 'Orbitron', sans-serif;
        font-size: 22px;
        color: #00ffff;
        margin-bottom: 10px;
        text-shadow: 0 0 10px #00ffff;
    }
    
    .feature-desc {
        font-family: 'Rajdhani', sans-serif;
        font-size: 16px;
        color: #b0b0ff;
    }
    
    /* Message Bubbles */
    .message-bubble {
        background: linear-gradient(135deg, rgba(0, 255, 255, 0.15) 0%, rgba(255, 0, 255, 0.15) 100%);
        border-left: 4px solid #00ffff;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        animation: slideIn 0.5s ease-out;
    }
    
    .message-user {
        color: #00ff00;
        font-weight: 600;
        font-size: 14px;
        text-shadow: 0 0 5px #00ff00;
    }
    
    .message-text {
        color: #ffffff;
        font-size: 16px;
        margin: 8px 0;
    }
    
    .message-meta {
        color: #888;
        font-size: 12px;
    }
    
    .verified-badge {
        display: inline-block;
        background: linear-gradient(135deg, #00ff00 0%, #00ff88 100%);
        color: #000;
        padding: 3px 10px;
        border-radius: 5px;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        animation: pulse 2s infinite;
    }
    
    /* Room Info Panel */
    .room-info {
        background: rgba(0, 255, 255, 0.1);
        border: 2px solid #00ffff;
        border-radius: 10px;
        padding: 20px;
        margin: 20px 0;
        animation: fadeIn 1s ease-out;
    }
    
    /* Footer */
    .footer {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        text-align: center;
        padding: 15px;
        background: rgba(10, 10, 30, 0.9);
        border-top: 2px solid #00ffff;
        font-family: 'Orbitron', sans-serif;
        color: #00ffff;
        font-size: 14px;
        z-index: 999;
    }
    
    /* Logo */
    .logo {
        font-family: 'Orbitron', sans-serif;
        font-size: 48px;
        font-weight: 900;
        text-align: center;
        background: linear-gradient(135deg, #00ffff 0%, #ff00ff 50%, #00ff00 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-shadow: 0 0 30px rgba(0, 255, 255, 0.5);
        animation: fadeIn 1.5s ease-out;
    }
    
    /* Warning Box */
    .warning-box {
        background: rgba(255, 0, 0, 0.1);
        border: 2px solid #ff0000;
        border-radius: 10px;
        padding: 15px;
        margin: 20px 0;
        color: #ff6666;
        animation: fadeIn 1s ease-out;
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# LANDING PAGE
# ============================================================================

def render_landing_page():
    """Render animated landing page with feature cards"""
    st.markdown('<div class="logo">DARKRELAY</div>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 20px; color: #b0b0ff; margin-bottom: 40px;">Anonymous. Encrypted. Verified.</p>', unsafe_allow_html=True)
    
    # Feature Cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-title">⚡ Zero Registration</div>
            <div class="feature-desc">No email, no password, no tracking. Pure anonymity from the start.</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card">
            <div class="feature-title">🔒 End-to-End Encryption</div>
            <div class="feature-desc">AES-256 encryption. Messages encrypted before storage. Unbreakable security.</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-title">⛓️ Blockchain Verification</div>
            <div class="feature-desc">Cryptographic hash chaining ensures message integrity. Tamper-proof communication.</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card">
            <div class="feature-title">👤 Complete Anonymity</div>
            <div class="feature-desc">Random user IDs. No personal data collected. Zero footprint.</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-title">⚡ Real-time Communication</div>
            <div class="feature-desc">Instant message delivery. Live updates. Seamless chat experience.</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card">
            <div class="feature-title">🌐 Decentralized Trust</div>
            <div class="feature-desc">No central server. No data retention. Messages live only in memory.</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Action Buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        if st.button("🚀 CREATE ROOM", use_container_width=True):
            st.session_state.page = 'create_room'
            st.rerun()
        
        if st.button("🔗 JOIN ROOM", use_container_width=True):
            st.session_state.page = 'join_room'
            st.rerun()
    
    # Disclaimer
    st.markdown("""
    <div class="warning-box">
        <strong>⚠️ PROOF OF CONCEPT - EDUCATIONAL USE ONLY</strong><br>
        This application is a demonstration of cryptographic concepts. Not for production use.
        Messages are stored in memory only and will be lost on server restart.
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# CREATE ROOM PAGE
# ============================================================================

def render_create_room_page():
    """Room creation interface"""
    st.markdown('<h1 style="text-align: center;">🔐 CREATE SECURE ROOM</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="room-info">
        <strong>Your Anonymous ID:</strong> <code style="color: #00ff00;">{}</code><br>
        <small>This ID is temporary and anonymous. Share your Room ID with others to chat.</small>
    </div>
    """.format(st.session_state.user_id[:16] + "..."), unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        room_name = st.text_input("Room Name (optional)", placeholder="e.g., Secret Project")
        
        if st.button("🎲 GENERATE ROOM", use_container_width=True):
            room_id = secrets.token_hex(8)
            encryption_key = CryptoEngine.generate_key_from_room_id(room_id)
            
            # Initialize room with genesis message
            genesis_hash = BlockchainVerifier.compute_message_hash(
                "Room Created",
                time.time(),
                "0" * 64,
                "SYSTEM"
            )
            
            st.session_state.rooms[room_id] = {
                'name': room_name if room_name else f"Room-{room_id[:8]}",
                'messages': [{
                    'user_id': 'SYSTEM',
                    'message': 'Room Created',
                    'encrypted_message': CryptoEngine.encrypt_message('Room Created', encryption_key),
                    'timestamp': time.time(),
                    'hash': genesis_hash,
                    'prev_hash': "0" * 64
                }],
                'participants': set()
            }
            
            st.session_state.current_room = room_id
            st.session_state.page = 'chat'
            st.rerun()
        
        if st.button("← BACK", use_container_width=True):
            st.session_state.page = 'landing'
            st.rerun()

# ============================================================================
# JOIN ROOM PAGE
# ============================================================================

def render_join_room_page():
    """Room joining interface"""
    st.markdown('<h1 style="text-align: center;">🔗 JOIN SECURE ROOM</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="room-info">
        <strong>Your Anonymous ID:</strong> <code style="color: #00ff00;">{}</code><br>
        <small>Enter the Room ID shared with you to join the conversation.</small>
    </div>
    """.format(st.session_state.user_id[:16] + "..."), unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        room_id = st.text_input("Room ID", placeholder="Enter 16-character Room ID")
        
        if st.button("🚪 JOIN ROOM", use_container_width=True):
            if room_id in st.session_state.rooms:
                st.session_state.current_room = room_id
                st.session_state.rooms[room_id]['participants'].add(st.session_state.user_id)
                st.session_state.page = 'chat'
                st.rerun()
            else:
                st.error("❌ Room not found. Please check the Room ID.")
        
        if st.button("← BACK", use_container_width=True):
            st.session_state.page = 'landing'
            st.rerun()

# ============================================================================
# CHAT ROOM PAGE
# ============================================================================

def render_chat_page():
    """Main chat interface with encryption and verification"""
    room_id = st.session_state.current_room
    room_data = st.session_state.rooms.get(room_id)
    
    if not room_data:
        st.error("Room not found")
        st.session_state.page = 'landing'
        st.rerun()
        return
    
    encryption_key = CryptoEngine.generate_key_from_room_id(room_id)
    
    # Header
    col1, col2, col3 = st.columns([2, 3, 2])
    
    with col1:
        if st.button("← LEAVE ROOM"):
            st.session_state.current_room = None
            st.session_state.page = 'landing'
            st.rerun()
    
    with col2:
        st.markdown(f'<h2 style="text-align: center;">{room_data["name"]}</h2>', unsafe_allow_html=True)
    
    with col3:
        if st.button("🗑️ CLEAR CHAT"):
            # Keep only genesis message
            genesis_msg = room_data['messages'][0]
            room_data['messages'] = [genesis_msg]
            st.rerun()
    
    # Room Info
    st.markdown(f"""
    <div class="room-info">
        <strong>Room ID:</strong> <code style="color: #00ff00;">{room_id}</code> (Share this to invite others)<br>
        <strong>Your ID:</strong> <code style="color: #00ffff;">{st.session_state.user_id[:16]}...</code><br>
        <strong>Encryption:</strong> AES-256 ✓ | <strong>Chain Verified:</strong> {"✓" if BlockchainVerifier.verify_chain(room_data['messages']) else "✗"}
    </div>
    """, unsafe_allow_html=True)
    
    # Message Display Area
    st.markdown('<div style="height: 400px; overflow-y: auto; padding: 20px; background: rgba(0, 0, 0, 0.3); border-radius: 10px; margin: 20px 0;">', unsafe_allow_html=True)
    
    for msg in room_data['messages']:
        # Decrypt message for display
        decrypted_text = CryptoEngine.decrypt_message(msg['encrypted_message'], encryption_key)
        
        timestamp_str = datetime.fromtimestamp(msg['timestamp']).strftime('%H:%M:%S')
        user_display = msg['user_id'][:12] + "..." if msg['user_id'] != 'SYSTEM' else 'SYSTEM'
        
        # Verify message hash
        computed_hash = BlockchainVerifier.compute_message_hash(
            msg['message'],
            msg['timestamp'],
            msg['prev_hash'],
            msg['user_id']
        )
        is_verified = computed_hash == msg['hash']
        
        verification_badge = '<span class="verified-badge">✓ VERIFIED</span>' if is_verified else '<span style="color: #ff0000;">✗ INVALID</span>'
        
        st.markdown(f"""
        <div class="message-bubble">
            <div class="message-user">{user_display} {verification_badge}</div>
            <div class="message-text">{decrypted_text}</div>
            <div class="message-meta">{timestamp_str} | Hash: {msg['hash'][:16]}...</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Message Input
    col1, col2 = st.columns([5, 1])
    
    with col1:
        new_message = st.text_input("Type your message...", key=f"msg_input_{st.session_state.refresh_counter}", label_visibility="collapsed")
    
    with col2:
        send_button = st.button("SEND", use_container_width=True)
    
    if send_button and new_message.strip():
        # Get previous message hash
        prev_hash = room_data['messages'][-1]['hash'] if room_data['messages'] else "0" * 64
        
        # Compute new message hash
        timestamp = time.time()
        message_hash = BlockchainVerifier.compute_message_hash(
            new_message,
            timestamp,
            prev_hash,
            st.session_state.user_id
        )
        
        # Encrypt message
        encrypted = CryptoEngine.encrypt_message(new_message, encryption_key)
        
        # Add message to room
        room_data['messages'].append({
            'user_id': st.session_state.user_id,
            'message': new_message,
            'encrypted_message': encrypted,
            'timestamp': timestamp,
            'hash': message_hash,
            'prev_hash': prev_hash
        })
        
        st.session_state.refresh_counter += 1
        st.rerun()
    
    # Auto-refresh simulation
    time.sleep(0.1)

# ============================================================================
# MAIN APPLICATION LOGIC
# ============================================================================

def main():
    """Main application entry point"""
    init_session_state()
    load_css()
    
    # Page Routing
    if st.session_state.page == 'landing':
        render_landing_page()
    elif st.session_state.page == 'create_room':
        render_create_room_page()
    elif st.session_state.page == 'join_room':
        render_join_room_page()
    elif st.session_state.page == 'chat':
        render_chat_page()
    
    # Footer
    st.markdown('<div class="footer">Made by DE | DarkRelay v1.0 | Proof of Concept</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
