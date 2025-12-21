import streamlit as st
from cryptography.fernet import Fernet
import hashlib
import time
import threading
import uuid

lock = threading.Lock()
ROOMS = {}

def verify_chain(messages, genesis_hash):
    prev_h = genesis_hash
    for msg in messages:
        if msg['prev_hash'] != prev_h:
            return False
        user_id_str = str(msg['user_id'])
        timestamp_str = str(msg['timestamp'])
        encrypted_msg = msg['encrypted_msg']
        prev_hash = msg['prev_hash']
        hash_input = user_id_str + timestamp_str + encrypted_msg + prev_hash
        computed = hashlib.sha256(hash_input.encode()).hexdigest()
        if computed != msg['hash']:
            return False
        prev_h = msg['hash']
    return True

css = """
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');
body {
    background-color: black;
    color: white;
    font-family: 'Orbitron', sans-serif;
}
.stButton > button {
    background-color: violet;
    color: black;
    border: none;
    padding: 10px 20px;
    text-align: center;
    text-decoration: none;
    display: inline-block;
    font-size: 16px;
    margin: 4px 2px;
    cursor: pointer;
    border-radius: 4px;
    box-shadow: 0 0 10px violet;
}
.stTextInput > div > div > input {
    background-color: #111;
    color: white;
    border: 1px solid violet;
}
h1, h2, h3 {
    color: violet;
    text-shadow: 0 0 5px violet;
}
.central-visual {
    width: 200px;
    height: 200px;
    background: radial-gradient(circle, violet, transparent);
    border-radius: 50%;
    animation: pulse 2s infinite;
    margin: 0 auto;
}
@keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.05); }
    100% { transform: scale(1); }
}
.chat-message {
    background-color: #222;
    border: 1px solid violet;
    border-radius: 5px;
    padding: 10px;
    margin: 5px 0;
    box-shadow: 0 0 5px violet;
}
"""

st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())[:8]

if 'current_room' not in st.session_state:
    st.session_state.current_room = None

if st.session_state.current_room is None:
    st.markdown('<div class="central-visual"></div>', unsafe_allow_html=True)
    st.markdown('<h1 style="text-align:center;">DarkRelay</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center; font-size:24px; color:purple;">Anonymous Encrypted Messaging Platform</p>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center; color:violet;">Transcending Dimensions in Secure Communication</p>', unsafe_allow_html=True)
    
    room_name = st.text_input("Enter Room Name to Create or Join")
    if st.button("Create Room"):
        with lock:
            if room_name not in ROOMS:
                key = Fernet.generate_key()
                genesis_hash = hashlib.sha256(b'genesis').hexdigest()
                ROOMS[room_name] = {'key': key, 'messages': [], 'genesis_hash': genesis_hash}
        st.session_state.current_room = room_name
        st.rerun()
    
    st.markdown('<h3>Existing Rooms</h3>', unsafe_allow_html=True)
    with lock:
        rooms = list(ROOMS.keys())
    for r in rooms:
        if st.button(f"Join {r}"):
            st.session_state.current_room = r
            st.rerun()
else:
    room = st.session_state.current_room
    st.markdown('<div class="central-visual"></div>', unsafe_allow_html=True)
    st.markdown(f'<h1 style="text-align:center;">Room: {room}</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center; color:violet;">Secure Chain-Verified Messaging</p>', unsafe_allow_html=True)
    
    if st.button("Leave Room"):
        st.session_state.current_room = None
        st.rerun()
    
    if st.button("Refresh"):
        st.rerun()
    
    with lock:
        if room in ROOMS:
            msgs = ROOMS[room]['messages']
            key = ROOMS[room]['key']
            genesis_hash = ROOMS[room]['genesis_hash']
            f = Fernet(key)
            chain_ok = verify_chain(msgs, genesis_hash)
    
    status_text = "Chain Intact" if chain_ok else "Chain Tampered!"
    status_color = "green" if chain_ok else "red"
    st.markdown(f'<p style="text-align:center; color:{status_color};">{status_text}</p>', unsafe_allow_html=True)
    
    for msg in msgs:
        decrypted = f.decrypt(msg['encrypted_msg'].encode()).decode()
        user = msg['user_id']
        ts = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(msg['timestamp']))
        ts_str = ts
        decrypted_safe = decrypted
        st.markdown(f'<div class="chat-message"><span style="color:purple;">{user} [{ts_str}]:</span> {decrypted_safe}</div>', unsafe_allow_html=True)
    
    message = st.text_input("Enter Message")
    if st.button("Send"):
        if message:
            with lock:
                if room in ROOMS:
                    prev_hash = ROOMS[room]['messages'][-1]['hash'] if ROOMS[room]['messages'] else ROOMS[room]['genesis_hash']
                    ts = time.time()
                    encrypted = f.encrypt(message.encode()).decode()
                    user_id_str = str(st.session_state.user_id)
                    timestamp_str = str(ts)
                    hash_input = user_id_str + timestamp_str + encrypted + prev_hash
                    msg_hash = hashlib.sha256(hash_input.encode()).hexdigest()
                    new_msg = {
                        'user_id': st.session_state.user_id,
                        'timestamp': ts,
                        'encrypted_msg': encrypted,
                        'hash': msg_hash,
                        'prev_hash': prev_hash
                    }
                    ROOMS[room]['messages'].append(new_msg)
            st.rerun()
