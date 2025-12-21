"""
DarkRelay - Anonymous Encrypted Messaging Platform
Proof of Concept - Educational Purposes Only
Made by DE
"""

import streamlit as st
import hashlib
import secrets
import time
from datetime import datetime
from cryptography.fernet import Fernet
import base64

# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="DarkRelay",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# CRYPTO ENGINE
# ============================================================

class CryptoEngine:
    @staticmethod
    def key_from_room(room_id: str) -> bytes:
        return base64.urlsafe_b64encode(
            hashlib.sha256(room_id.encode()).digest()
        )

    @staticmethod
    def encrypt(msg: str, key: bytes) -> str:
        return Fernet(key).encrypt(msg.encode()).decode()

    @staticmethod
    def decrypt(token: str, key: bytes) -> str:
        try:
            return Fernet(key).decrypt(token.encode()).decode()
        except:
            return "[DECRYPTION FAILED]"

# ============================================================
# BLOCKCHAIN VERIFIER (SIMULATED)
# ============================================================

class BlockchainVerifier:
    @staticmethod
    def hash_message(msg, ts, prev, uid):
        raw = f"{msg}{ts}{prev}{uid}"
        return hashlib.sha256(raw.encode()).hexdigest()

    @staticmethod
    def verify(chain):
        for i in range(1, len(chain)):
            if chain[i]["prev_hash"] != chain[i-1]["hash"]:
                return False
        return True

# ============================================================
# SESSION INIT
# ============================================================

def init_state():
    if "user_id" not in st.session_state:
        st.session_state.user_id = secrets.token_hex(16)

    if "page" not in st.session_state:
        st.session_state.page = "landing"

    if "rooms" not in st.session_state:
        st.session_state.rooms = {}

    if "current_room" not in st.session_state:
        st.session_state.current_room = None

# ============================================================
# CSS (SHORTENED BUT DARK + ANIMATED)
# ============================================================

def load_css():
    st.markdown("""
    <style>
    body { background:black; }
    .stApp { background:black; color:#00ffff; }
    h1,h2 { text-shadow:0 0 20px #00ffff; }
    input, textarea {
        background:black !important;
        color:#00ffff !important;
        border:1px solid #00ffff !important;
    }
    button {
        background:linear-gradient(135deg,#00ffff,#ff00ff) !important;
        color:black !important;
        font-weight:bold;
    }
    .chat {
        height:480px;
        overflow-y:auto;
        border:1px solid #00ffff;
        padding:15px;
    }
    .msg {
        border-left:3px solid #00ffff;
        padding:10px;
        margin-bottom:10px;
    }
    .footer {
        position:fixed;
        bottom:0;
        width:100%;
        text-align:center;
        color:#00ffff;
    }
    </style>
    """, unsafe_allow_html=True)

# ============================================================
# LANDING
# ============================================================

def landing():
    st.markdown("<h1 style='text-align:center'>DARKRELAY</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center'>Anonymous • Encrypted • Verified</p>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🚀 CREATE ROOM", use_container_width=True):
            st.session_state.page = "create"
            st.rerun()

    with col2:
        if st.button("🔗 JOIN ROOM", use_container_width=True):
            st.session_state.page = "join"
            st.rerun()

# ============================================================
# CREATE ROOM
# ============================================================

def create_room():
    st.header("Create Room")

    name = st.text_input("Room Name (optional)")
    if st.button("Generate Room"):
        rid = secrets.token_hex(8)
        key = CryptoEngine.key_from_room(rid)

        ts = time.time()
        genesis_hash = BlockchainVerifier.hash_message(
            "Room Created", ts, "0"*64, "SYSTEM"
        )

        st.session_state.rooms[rid] = {
            "name": name or f"Room-{rid[:6]}",
            "messages": [{
                "user_id": "SYSTEM",
                "message": "Room Created",
                "encrypted": CryptoEngine.encrypt("Room Created", key),
                "timestamp": ts,
                "hash": genesis_hash,
                "prev_hash": "0"*64
            }]
        }

        st.session_state.current_room = rid
        st.session_state.page = "chat"
        st.rerun()

    if st.button("← Back"):
        st.session_state.page = "landing"
        st.rerun()

# ============================================================
# JOIN ROOM
# ============================================================

def join_room():
    st.header("Join Room")
    rid = st.text_input("Room ID")

    if st.button("Join"):
        if rid in st.session_state.rooms:
            st.session_state.current_room = rid
            st.session_state.page = "chat"
            st.rerun()
        else:
            st.error("Room not found")

    if st.button("← Back"):
        st.session_state.page = "landing"
        st.rerun()

# ============================================================
# CHAT
# ============================================================

def chat():
    rid = st.session_state.current_room
    room = st.session_state.rooms.get(rid)

    if not room:
        st.error("Room expired")
        st.session_state.page = "landing"
        st.rerun()

    key = CryptoEngine.key_from_room(rid)

    st.subheader(room["name"])
    st.code(f"Room ID: {rid}")

    verified = BlockchainVerifier.verify(room["messages"])
    st.write("Chain Verified:", "✅" if verified else "❌")

    st.markdown("<div class='chat'>", unsafe_allow_html=True)

    for m in room["messages"]:
        txt = CryptoEngine.decrypt(m["encrypted"], key)
        ts = datetime.fromtimestamp(m["timestamp"]).strftime("%H:%M:%S")
        st.markdown(
            f"<div class='msg'><b>{m['user_id'][:10]}</b> [{ts}]<br>{txt}</div>",
            unsafe_allow_html=True
        )

    st.markdown("</div>", unsafe_allow_html=True)

    msg = st.text_input("Message")
    if st.button("Send") and msg.strip():
        prev = room["messages"][-1]["hash"]
        ts = time.time()
        h = BlockchainVerifier.hash_message(msg, ts, prev, st.session_state.user_id)

        room["messages"].append({
            "user_id": st.session_state.user_id,
            "message": msg,
            "encrypted": CryptoEngine.encrypt(msg, key),
            "timestamp": ts,
            "hash": h,
            "prev_hash": prev
        })
        st.rerun()

    if st.button("← Leave"):
        st.session_state.page = "landing"
        st.session_state.current_room = None
        st.rerun()

# ============================================================
# MAIN
# ============================================================

def main():
    init_state()
    load_css()

    if st.session_state.page == "landing":
        landing()
    elif st.session_state.page == "create":
        create_room()
    elif st.session_state.page == "join":
        join_room()
    elif st.session_state.page == "chat":
        chat()

    st.markdown("<div class='footer'>Made by DE • DarkRelay</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
