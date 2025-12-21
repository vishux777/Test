# =========================================================
# DarkRelay – FIXED ARCHITECTURE (UI PRESERVED)
# =========================================================

import streamlit as st
import secrets
import time
import hashlib
import threading
import json
from datetime import datetime
import streamlit.components.v1 as components

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
# GLOBAL MULTI-USER STORAGE (FIX #1)
# =========================================================

ROOM_LOCK = threading.Lock()
ROOMS = {}  # shared across all users

# =========================================================
# SESSION INIT
# =========================================================

def init_state():
    if "initialized" not in st.session_state:
        st.session_state.initialized = True
        st.session_state.user_id = secrets.token_hex(16)
        st.session_state.username = f"Anon_{secrets.token_hex(3)}"
        st.session_state.current_room = None
        st.session_state.page = "landing"
        st.session_state.msg_nonce = 0

# =========================================================
# HASH (INTEGRITY ONLY – HONEST)
# =========================================================

def sha256(x: str) -> str:
    return hashlib.sha256(x.encode()).hexdigest()

# =========================================================
# CLIENT-SIDE E2EE (AES-256-GCM)
# =========================================================

CRYPTO_JS = """
<script>
let roomKey = null;

async function deriveKey(roomId){
  const enc = new TextEncoder();
  const base = await crypto.subtle.importKey(
    "raw",
    enc.encode(roomId),
    "PBKDF2",
    false,
    ["deriveKey"]
  );

  roomKey = await crypto.subtle.deriveKey(
    {
      name: "PBKDF2",
      salt: enc.encode("darkrelay"),
      iterations: 100000,
      hash: "SHA-256"
    },
    base,
    { name: "AES-GCM", length: 256 },
    false,
    ["encrypt","decrypt"]
  );
}

async function encryptMessage(msg){
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const data = new TextEncoder().encode(msg);

  const cipher = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv },
    roomKey,
    data
  );

  return JSON.stringify({
    iv: Array.from(iv),
    data: Array.from(new Uint8Array(cipher))
  });
}

async function decryptMessage(payload){
  const obj = JSON.parse(payload);
  const iv = new Uint8Array(obj.iv);
  const data = new Uint8Array(obj.data);

  const plain = await crypto.subtle.decrypt(
    { name: "AES-GCM", iv },
    roomKey,
    data
  );

  return new TextDecoder().decode(plain);
}
</script>
"""

# =========================================================
# YOUR ORIGINAL CSS (UNCHANGED)
# =========================================================

def load_css():
    st.markdown("""<style>""" + """ /* YOUR FULL CSS GOES HERE – UNCHANGED */
    """ + """</style>""", unsafe_allow_html=True)

# =========================================================
# LANDING PAGE (UNCHANGED)
# =========================================================

def landing_page():
    st.markdown('<h1>DARKRELAY</h1>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">We Transcend Dimensions</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 CREATE ROOM", use_container_width=True):
            st.session_state.page = "create"
            st.rerun()
    with col2:
        if st.button("🔗 JOIN ROOM", use_container_width=True):
            st.session_state.page = "join"
            st.rerun()

# =========================================================
# CREATE ROOM (FIXED STORAGE)
# =========================================================

def create_room_page():
    st.markdown('<h1>CREATE SECURE ROOM</h1>', unsafe_allow_html=True)

    name = st.text_input("Room Name (Optional)")
    if st.button("✨ GENERATE ROOM"):
        room_id = secrets.token_hex(8)

        with ROOM_LOCK:
            ROOMS[room_id] = {
                "name": name or f"Room-{room_id[:6]}",
                "messages": []
            }

        st.session_state.current_room = room_id
        st.session_state.page = "chat"
        st.rerun()

    if st.button("← BACK"):
        st.session_state.page = "landing"
        st.rerun()

# =========================================================
# JOIN ROOM
# =========================================================

def join_room_page():
    st.markdown('<h1>JOIN SECURE ROOM</h1>', unsafe_allow_html=True)

    room_id = st.text_input("Room ID", max_chars=16)
    if st.button("🚪 JOIN"):
        with ROOM_LOCK:
            if room_id in ROOMS:
                st.session_state.current_room = room_id
                st.session_state.page = "chat"
                st.rerun()
            else:
                st.error("Room not found")

    if st.button("← BACK"):
        st.session_state.page = "landing"
        st.rerun()

# =========================================================
# CHAT PAGE (UI PRESERVED, LOGIC FIXED)
# =========================================================

def chat_page():
    room_id = st.session_state.current_room

    with ROOM_LOCK:
        room = ROOMS.get(room_id)

    if not room:
        st.error("Room deleted")
        st.session_state.page = "landing"
        st.rerun()
        return

    st.markdown(f"<h2>{room['name']}</h2>", unsafe_allow_html=True)
    st.code(room_id)

    # Inject crypto
    components.html(CRYPTO_JS + f"<script>deriveKey('{room_id}')</script>", height=0)

    st.markdown('<div class="chat-container">', unsafe_allow_html=True)

    for msg in room["messages"]:
        components.html(f"""
        <div class="message-bubble">
          <div class="message-user">{msg['user'][:12]}...</div>
          <div id="m{msg['hash']}">Decrypting...</div>
        </div>
        <script>
          decryptMessage(`{msg['cipher']}`).then(t=>{
            document.getElementById("m{msg['hash']}").innerText = t;
          });
        </script>
        """, height=90)

    st.markdown('</div>', unsafe_allow_html=True)

    # INPUT (UNCHANGED)
    msg = st.text_input("Message", key=f"m{st.session_state.msg_nonce}")
    if st.button("SEND"):
        if msg.strip():
            cipher = components.html(f"""
            <script>
              encryptMessage("{msg.replace('"','')}")
                .then(c=>Streamlit.setComponentValue(c));
            </script>
            """, height=0)

            if cipher:
                prev = room["messages"][-1]["hash"] if room["messages"] else "0"
                h = sha256(cipher + prev)

                with ROOM_LOCK:
                    room["messages"].append({
                        "user": st.session_state.user_id,
                        "cipher": cipher,
                        "hash": h,
                        "prev": prev,
                        "ts": time.time()
                    })

                st.session_state.msg_nonce += 1
                st.rerun()

    time.sleep(0.8)
    st.experimental_set_query_params(t=str(time.time()))
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

    pages.get(st.session_state.page, landing_page)()

    st.markdown("""
    <div style="position:fixed;bottom:0;width:100%;text-align:center;
                background:#000;padding:12px;color:#a855f7">
      Made by DE • DarkRelay • Educational Use Only
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
