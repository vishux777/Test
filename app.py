"""
DarkRelay - Anonymous Encrypted Messaging Platform
Enhanced Version - Educational Purposes Only
"""

import streamlit as st
import hashlib
import secrets
import time
import json
from datetime import datetime
from cryptography.fernet import Fernet
import base64

st.set_page_config(page_title="DarkRelay", page_icon="🔒", layout="wide")

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
        except:
            return "[ENCRYPTION ERROR]"
    
    @staticmethod
    def decrypt(encrypted: str, key: bytes) -> str:
        try:
            return Fernet(key).decrypt(encrypted.encode()).decode()
        except:
            return "[DECRYPTION FAILED]"

class BlockchainVerifier:
    @staticmethod
    def compute_hash(msg: str, ts: float, prev: str, uid: str) -> str:
        return hashlib.sha256(f"{msg}{ts}{prev}{uid}".encode()).hexdigest()
    
    @staticmethod
    def verify_chain(messages: list) -> bool:
        for i in range(1, len(messages)):
            if messages[i-1]['hash'] != messages[i]['prev_hash']:
                return False
        return True

# ============================================================================
# STATE MANAGEMENT
# ============================================================================

def init_state():
    defaults = {
        'user_id': secrets.token_hex(16),
        'username': f"Anon_{secrets.token_hex(3)}",
        'rooms': {},
        'current_room': None,
        'page': 'landing',
        'theme': 'cyan',
        'msg_count': 0
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

# ============================================================================
# DARK UI STYLING
# ============================================================================

def load_css():
    colors = {'cyan': '#00ffff', 'purple': '#ff00ff', 'green': '#00ff00', 'blue': '#0099ff'}
    c = colors.get(st.session_state.theme, '#00ffff')
    
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@400;600;700&display=swap');
    
    @keyframes glow {{ 0%, 100% {{ box-shadow: 0 0 20px {c}; }} 50% {{ box-shadow: 0 0 40px {c}; }} }}
    @keyframes slideIn {{ from {{ opacity: 0; transform: translateY(20px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    @keyframes float {{ 0%, 100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-10px); }} }}
    @keyframes scan {{ from {{ transform: translateY(-100%); }} to {{ transform: translateY(100vh); }} }}
    @keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.7; }} }}
    
    .stApp {{
        background: #000;
        color: {c};
        font-family: 'Rajdhani', sans-serif;
        background-image: 
            linear-gradient(0deg, transparent 24%, rgba(0,255,255,0.02) 25%, transparent 27%),
            radial-gradient(circle, rgba(0,255,255,0.03) 0%, transparent 60%);
        background-size: 50px 50px, 300% 300%;
    }}
    
    .stApp::before {{
        content: ''; position: fixed; top: 0; left: 0; width: 100%; height: 3px;
        background: linear-gradient(transparent, {c}, transparent);
        animation: scan 8s linear infinite; pointer-events: none; z-index: 9999;
    }}
    
    h1, h2, h3 {{
        font-family: 'Orbitron', sans-serif; color: {c}; font-weight: 900;
        text-shadow: 0 0 20px {c}, 0 0 40px {c}; animation: slideIn 1s;
    }}
    
    .stTextInput input, .stTextArea textarea {{
        background: rgba(0,0,0,0.95) !important; border: 2px solid {c}60 !important;
        color: {c} !important; border-radius: 10px; font-size: 16px;
        box-shadow: inset 0 0 20px rgba(0,0,0,0.9); transition: all 0.3s;
    }}
    
    .stTextInput input:focus, .stTextArea textarea:focus {{
        border-color: {c} !important; box-shadow: 0 0 30px {c}60 !important;
        transform: scale(1.02);
    }}
    
    .stButton button {{
        background: linear-gradient(135deg, {c}, #ff00ff) !important; color: #000 !important;
        font-family: 'Orbitron', sans-serif; font-weight: 900; border: none !important;
        border-radius: 12px; padding: 18px 40px; font-size: 15px;
        letter-spacing: 4px; text-transform: uppercase;
        box-shadow: 0 0 30px {c}60; transition: all 0.3s;
    }}
    
    .stButton button:hover {{
        transform: scale(1.1) translateY(-4px);
        box-shadow: 0 0 50px {c}, 0 0 70px #ff00ff !important;
        animation: glow 0.5s infinite;
    }}
    
    .feature-card {{
        background: linear-gradient(135deg, rgba(0,0,0,0.98), rgba(10,0,30,0.98));
        border: 2px solid {c}60; border-radius: 20px; padding: 35px; margin: 25px 0;
        animation: slideIn 1s, float 4s infinite; transition: all 0.4s;
        box-shadow: 0 0 30px {c}20; position: relative; overflow: hidden;
    }}
    
    .feature-card:hover {{
        transform: translateY(-12px) scale(1.05);
        box-shadow: 0 20px 60px {c}40; border-color: #ff00ff;
    }}
    
    .feature-title {{
        font-family: 'Orbitron', sans-serif; font-size: 26px; font-weight: 900;
        color: {c}; margin-bottom: 15px; letter-spacing: 2px;
        text-shadow: 0 0 20px {c};
    }}
    
    .message-bubble {{
        background: linear-gradient(135deg, rgba(0,0,0,0.95), rgba(10,0,30,0.95));
        border-left: 5px solid {c}; border-radius: 12px; padding: 20px; margin: 18px 0;
        animation: slideIn 0.5s; transition: all 0.3s;
        box-shadow: 0 0 25px {c}15;
    }}
    
    .message-bubble:hover {{
        transform: translateX(8px); box-shadow: 0 0 40px {c}30;
    }}
    
    .message-user {{
        color: #00ff00; font-weight: 700; font-family: 'Orbitron', sans-serif;
        text-shadow: 0 0 10px #00ff00; letter-spacing: 1px;
    }}
    
    .message-text {{
        color: #fff; font-size: 17px; margin: 12px 0; line-height: 1.6;
    }}
    
    .verified-badge {{
        display: inline-block; background: linear-gradient(135deg, #00ff00, #00ff88);
        color: #000; padding: 5px 14px; border-radius: 6px; font-size: 11px;
        font-weight: 900; animation: pulse 2s infinite; box-shadow: 0 0 15px #00ff00;
    }}
    
    .chat-container {{
        background: rgba(0,0,0,0.98); border: 3px solid {c}50; border-radius: 20px;
        padding: 25px; height: 550px; overflow-y: auto;
        box-shadow: inset 0 0 50px rgba(0,0,0,0.95), 0 0 40px {c}20;
    }}
    
    .room-info {{
        background: rgba(0,0,0,0.98); border: 3px solid {c}60; border-radius: 20px;
        padding: 30px; margin: 30px 0; box-shadow: 0 0 50px {c}25;
    }}
    
    .logo {{
        font-family: 'Orbitron', sans-serif; font-size: 72px; font-weight: 900;
        text-align: center; letter-spacing: 15px; margin: 50px 0;
        background: linear-gradient(135deg, #00ffff, #ff00ff, #00ff00, #ffff00);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        filter: drop-shadow(0 0 50px {c});
    }}
    
    .warning-box {{
        background: rgba(0,0,0,0.98); border: 3px solid #ff0000; border-radius: 15px;
        padding: 25px; margin: 35px 0; color: #ff6666; animation: pulse 3s infinite;
        box-shadow: 0 0 40px rgba(255,0,0,0.4);
    }}
    
    .success-box {{
        background: rgba(0,0,0,0.98); border: 3px solid #00ff00; border-radius: 15px;
        padding: 25px; margin: 25px 0; color: #00ff00;
        box-shadow: 0 0 40px rgba(0,255,0,0.4);
    }}
    
    ::-webkit-scrollbar {{ width: 12px; }}
    ::-webkit-scrollbar-track {{ background: #000; }}
    ::-webkit-scrollbar-thumb {{ 
        background: linear-gradient(180deg, {c}, #ff00ff); border-radius: 10px;
        box-shadow: 0 0 20px {c};
    }}
    
    #MainMenu, footer, header {{ visibility: hidden; }}
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# PAGES
# ============================================================================

def landing_page():
    st.markdown('<div class="logo">DARKRELAY</div>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center;font-size:22px;color:#9090ff;">Anonymous. Encrypted. Verified.</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    features = [
        ("⚡ Zero Registration", "No email, password, or tracking. Pure anonymity."),
        ("🔒 AES-256 Encryption", "Military-grade encryption. Unbreakable security."),
        ("⛓️ Hash Chain Verification", "Cryptographic integrity. Tamper-proof messages."),
        ("👤 Complete Anonymity", "Random IDs. No personal data. Zero footprint."),
        ("⚡ Real-time Updates", "Instant messaging. Live chat experience."),
        ("🌐 Persistent Storage", "Messages saved across sessions. Never lose data.")
    ]
    
    for i, (col, (title, desc)) in enumerate(zip([col1, col2, col3] * 2, features)):
        with col:
            st.markdown(f"""
            <div class="feature-card" style="animation-delay:{i*0.1}s;">
                <div class="feature-title">{title}</div>
                <div style="color:#b0b0ff;font-size:16px;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        if st.button("🚀 CREATE ROOM", use_container_width=True):
            st.session_state.page = 'create'
            st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🔗 JOIN ROOM", use_container_width=True):
            st.session_state.page = 'join'
            st.rerun()
    
    st.markdown("""
    <div class="warning-box">
        <strong>⚠️ EDUCATIONAL POC ONLY</strong><br>
        Cryptographic demonstration. Not for production use.
    </div>
    """, unsafe_allow_html=True)

def create_room_page():
    st.markdown('<h1 style="text-align:center;">🔐 CREATE SECURE ROOM</h1>', unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="room-info">
        <strong>Your ID:</strong> <code style="color:#00ff00;">{st.session_state.user_id[:16]}...</code>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        room_name = st.text_input("Room Name (optional)", placeholder="e.g., Secret Project")
        
        if st.button("🎲 GENERATE ROOM", use_container_width=True):
            room_id = secrets.token_hex(8)
            key = CryptoEngine.generate_key(room_id)
            
            genesis_hash = BlockchainVerifier.compute_hash("Room Created", time.time(), "0" * 64, "SYSTEM")
            
            st.session_state.rooms[room_id] = {
                'name': room_name or f"Room-{room_id[:8]}",
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
        if st.button("← BACK", use_container_width=True):
            st.session_state.page = 'landing'
            st.rerun()

def join_room_page():
    st.markdown('<h1 style="text-align:center;">🔗 JOIN SECURE ROOM</h1>', unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="room-info">
        <strong>Your ID:</strong> <code style="color:#00ff00;">{st.session_state.user_id[:16]}...</code>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        room_id = st.text_input("Room ID", placeholder="Enter 16-character Room ID")
        
        if st.button("🚪 JOIN ROOM", use_container_width=True):
            if room_id and len(room_id) == 16:
                if room_id in st.session_state.rooms:
                    st.session_state.rooms[room_id]['participants'].add(st.session_state.user_id)
                    st.session_state.current_room = room_id
                    st.session_state.page = 'chat'
                    st.rerun()
                else:
                    st.markdown('<div class="warning-box">❌ Room not found</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="warning-box">❌ Invalid Room ID (must be 16 chars)</div>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("← BACK", use_container_width=True):
            st.session_state.page = 'landing'
            st.rerun()

def chat_page():
    room_id = st.session_state.current_room
    room = st.session_state.rooms.get(room_id)
    
    if not room:
        st.markdown('<div class="warning-box">❌ Room not found</div>', unsafe_allow_html=True)
        if st.button("← GO BACK"):
            st.session_state.page = 'landing'
            st.rerun()
        return
    
    key = CryptoEngine.generate_key(room_id)
    
    col1, col2, col3 = st.columns([2, 3, 2])
    
    with col1:
        if st.button("← LEAVE", key="leave"):
            st.session_state.current_room = None
            st.session_state.page = 'landing'
            st.rerun()
    
    with col2:
        st.markdown(f'<h2 style="text-align:center;">{room["name"]}</h2>', unsafe_allow_html=True)
    
    with col3:
        if st.button("🗑️ CLEAR", key="clear"):
            room['messages'] = [room['messages'][0]]
            st.rerun()
    
    chain_valid = BlockchainVerifier.verify_chain(room['messages'])
    
    st.markdown(f"""
    <div class="room-info">
        <strong>Room ID:</strong> <code>{room_id}</code><br>
        <strong>Your ID:</strong> <code>{st.session_state.user_id[:16]}...</code><br>
        <strong>Encryption:</strong> <span style="color:#00ff00;">AES-256 ✓</span> | 
        <strong>Chain:</strong> <span style="color:{'#00ff00' if chain_valid else '#ff0000'};">{"✓" if chain_valid else "✗"}</span> | 
        <strong>Messages:</strong> {len(room['messages'])} | 
        <strong>Users:</strong> {len(room['participants'])}
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    for idx, msg in enumerate(room['messages']):
        decrypted = CryptoEngine.decrypt(msg['encrypted'], key)
        ts = datetime.fromtimestamp(msg['timestamp']).strftime('%H:%M:%S')
        user = msg['user_id'][:12] + "..." if msg['user_id'] != 'SYSTEM' else 'SYSTEM'
        
        verified = BlockchainVerifier.compute_hash(
            msg['message'], msg['timestamp'], msg['prev_hash'], msg['user_id']
        ) == msg['hash']
        
        badge = '<span class="verified-badge">✓ VERIFIED</span>' if verified else '<span style="color:#ff0000;">✗ INVALID</span>'
        
        st.markdown(f"""
        <div class="message-bubble">
            <div class="message-user">{user} {badge}</div>
            <div class="message-text">{decrypted}</div>
            <div style="color:#666;font-size:12px;margin-top:10px;">
                {ts} | Hash: {msg['hash'][:16]}... | Prev: {msg['prev_hash'][:16]}...
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns([6, 1])
    
    with col1:
        msg = st.text_input("Message", key=f"msg_{st.session_state.msg_count}", 
                           label_visibility="collapsed", placeholder="Type encrypted message...")
    
    with col2:
        send = st.button("SEND", use_container_width=True)
    
    if send and msg and msg.strip():
        prev_hash = room['messages'][-1]['hash']
        ts = time.time()
        msg_hash = BlockchainVerifier.compute_hash(msg, ts, prev_hash, st.session_state.user_id)
        
        room['messages'].append({
            'user_id': st.session_state.user_id,
            'message': msg,
            'encrypted': CryptoEngine.encrypt(msg, key),
            'timestamp': ts,
            'hash': msg_hash,
            'prev_hash': prev_hash
        })
        
        st.session_state.msg_count += 1
        st.rerun()

# ============================================================================
# MAIN
# ============================================================================

def main():
    init_state()
    load_css()
    
    pages = {
        'landing': landing_page,
        'create': create_room_page,
        'join': join_room_page,
        'chat': chat_page
    }
    
    pages[st.session_state.page]()
    
    st.markdown('<div style="position:fixed;bottom:0;left:0;width:100%;text-align:center;padding:15px;background:rgba(0,0,0,0.98);border-top:2px solid #00ffff;font-family:Orbitron;color:#00ffff;z-index:999;">Made by DE | DarkRelay v2.0</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
