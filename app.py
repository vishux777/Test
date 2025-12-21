"""
DarkRelay - Anonymous Encrypted Messaging Platform
Enhanced Version - Educational Purposes Only
MULTI-USER FIXED VERSION
"""

import streamlit as st
import hashlib
import secrets
import time
from datetime import datetime
from cryptography.fernet import Fernet
import base64
import threading

# =========================================================
# STREAMLIT CONFIG
# =========================================================

st.set_page_config(
    page_title="DarkRelay",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================================================
# GLOBAL MULTI-USER STORAGE (IMPORTANT FIX)
# =========================================================

ROOM_LOCK = threading.Lock()
ROOMS = {}   # shared across all users

# =========================================================
# CRYPTO ENGINE
# =========================================================

class CryptoEngine:
    @staticmethod
    def generate_key(room_id: str) -> bytes:
        return base64.urlsafe_b64encode(
            hashlib.sha256(room_id.encode()).digest()
        )

    @staticmethod
    def encrypt(message: str, key: bytes) -> str:
        return Fernet(key).encrypt(message.encode()).decode()

    @staticmethod
    def decrypt(cipher: str, key: bytes) -> str:
        return Fernet(key).decrypt(cipher.encode()).decode()

# =========================================================
# HASH CHAIN (INTEGRITY)
# =========================================================

class HashChain:
    @staticmethod
    def compute(msg: str, ts: float, prev: str, uid: str) -> str:
        return hashlib.sha256(
            f"{msg}{ts}{prev}{uid}".encode()
        ).hexdigest()

    @staticmethod
    def verify(messages):
        for i in range(1, len(messages)):
            if messages[i]["prev_hash"] != messages[i-1]["hash"]:
                return False
        return True

# =========================================================
# SESSION INIT
# =========================================================

def init_state():
    if "user_id" not in st.session_state:
        st.session_state.user_id = secrets.token_hex(16)
    if "page" not in st.session_state:
        st.session_state.page = "landing"
    if "current_room" not in st.session_state:
        st.session_state.current_room = None
    if "msg_count" not in st.session_state:
        st.session_state.msg_count = 0

# =========================================================
# UI (YOUR CSS – UNCHANGED)
# =========================================================

def load_css():
    st.markdown("""
    <style>
    body { background:#000; color:#00ffff; }
    .chat-container { height:550px; overflow-y:auto; }
    .message-bubble {
        background:#050505;
        border-left:4px solid #00ffff;
        padding:16px;
        margin:12px 0;
        border-radius:10px;
    }
    .message-user { color:#00ff00; font-weight:700; }
    .verified { color:#00ff00; font-size:12px; }
    .invalid { color:#ff0000; font-size:12px; }
    </style>
    """, unsafe_allow_html=True)

# =========================================================
# PAGES
# =========================================================

def landing_page():
    st.markdown("<h1 style='text-align:center;'>DARKRELAY</h1>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 CREATE ROOM", use_container_width=True):
            st.session_state.page = "create"
            st.rerun()
    with col2:
        if st.button("🔗 JOIN ROOM", use_container_width=True):
            st.session_state.page = "join"
            st.rerun()

def create_room_page():
    st.markdown("## Create Secure Room")

    name = st.text_input("Room name (optional)")

    if st.button("Generate Room"):
        room_id = secrets.token_hex(8)
        key = CryptoEngine.generate_key(room_id)

        genesis_hash = HashChain.compute(
            "Room Created", time.time(), "0"*64, "SYSTEM"
        )

        with ROOM_LOCK:
            ROOMS[room_id] = {
                "name": name or f"Room-{room_id[:6]}",
                "messages": [{
                    "user_id": "SYSTEM",
                    "encrypted": CryptoEngine.encrypt("Room Created", key),
                    "timestamp": time.time(),
                    "hash": genesis_hash,
                    "prev_hash": "0"*64
                }],
                "participants": set()
            }

        st.session_state.current_room = room_id
        st.session_state.page = "chat"
        st.rerun()

    if st.button("← Back"):
        st.session_state.page = "landing"
        st.rerun()

def join_room_page():
    st.markdown("## Join Secure Room")

    room_id = st.text_input("Room ID (16 characters)")

    if st.button("Join"):
        with ROOM_LOCK:
            if room_id in ROOMS:
                st.session_state.current_room = room_id
                st.session_state.page = "chat"
                st.rerun()
            else:
                st.error("Room not found")

    if st.button("← Back"):
        st.session_state.page = "landing"
        st.rerun()

def chat_page():
    room_id = st.session_state.current_room

    with ROOM_LOCK:
        room = ROOMS.get(room_id)

    if not room:
        st.error("Room not found")
        st.session_state.page = "landing"
        st.rerun()
        return

    key = CryptoEngine.generate_key(room_id)

    st.markdown(f"## {room['name']}")
    st.code(room_id)

    valid_chain = HashChain.verify(room["messages"])

    st.markdown(
        f"Chain Status: {'✅ VERIFIED' if valid_chain else '❌ BROKEN'}"
    )

    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)

    for msg in room["messages"]:
        text = CryptoEngine.decrypt(msg["encrypted"], key)
        ts = datetime.fromtimestamp(msg["timestamp"]).strftime("%H:%M:%S")

        verified = HashChain.compute(
            text, msg["timestamp"], msg["prev_hash"], msg["user_id"]
        ) == msg["hash"]

        st.markdown(f"""
        <div class="message-bubble">
            <div class="message-user">
                {msg["user_id"][:12]}...
                <span class="{'verified' if verified else 'invalid'}">
                    {'✓ VERIFIED' if verified else '✗ INVALID'}
                </span>
            </div>
            <div>{text}</div>
            <small>{ts}</small>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    msg = st.text_input(
        "Message",
        key=f"msg_{st.session_state.msg_count}",
        placeholder="Type message..."
    )

    if st.button("SEND"):
        if msg.strip():
            prev = room["messages"][-1]["hash"]
            ts = time.time()
            h = HashChain.compute(msg, ts, prev, st.session_state.user_id)

            with ROOM_LOCK:
                room["messages"].append({
                    "user_id": st.session_state.user_id,
                    "encrypted": CryptoEngine.encrypt(msg, key),
                    "timestamp": ts,
                    "hash": h,
                    "prev_hash": prev
                })

            st.session_state.msg_count += 1
            st.rerun()

# =========================================================
# MAIN
# =========================================================

def main():
    init_state()
    load_css()

    pages = {
        "landing": landing_page,
        "create": create_room_page,
        "join": join_room_page,
        "chat": chat_page
    }

    pages[st.session_state.page]()

    st.markdown(
        "<div style='position:fixed;bottom:0;width:100%;text-align:center;"
        "background:#000;padding:10px;color:#00ffff;'>"
        "Made by DE | DarkRelay (Multi-User)</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
