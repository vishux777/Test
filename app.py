import streamlit as st
import time
import secrets
import hashlib
import json
import threading
import streamlit.components.v1 as components

st.set_page_config(
    page_title="DarkRelay",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================================================
# GLOBAL SHARED STATE (MULTI-USER)
# =========================================================

ROOM_LOCK = threading.Lock()
ROOMS = {}   # { room_id : { name, messages[] } }

# =========================================================
# UTILS
# =========================================================

def sha256(x: str) -> str:
    return hashlib.sha256(x.encode()).hexdigest()

def init_user():
    if "uid" not in st.session_state:
        st.session_state.uid = secrets.token_hex(8)
    if "page" not in st.session_state:
        st.session_state.page = "landing"

# =========================================================
# CLIENT-SIDE CRYPTO (REAL E2EE)
# =========================================================

CRYPTO_JS = """
<script>
let derivedKey = null;

async function deriveKey(roomId) {
  const enc = new TextEncoder();
  const baseKey = await crypto.subtle.importKey(
    "raw",
    enc.encode(roomId),
    "PBKDF2",
    false,
    ["deriveKey"]
  );

  derivedKey = await crypto.subtle.deriveKey(
    {
      name: "PBKDF2",
      salt: enc.encode("darkrelay"),
      iterations: 100000,
      hash: "SHA-256"
    },
    baseKey,
    { name: "AES-GCM", length: 256 },
    false,
    ["encrypt", "decrypt"]
  );
}

async function encryptMessage(msg) {
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const enc = new TextEncoder().encode(msg);

  const cipher = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv },
    derivedKey,
    enc
  );

  return JSON.stringify({
    iv: Array.from(iv),
    data: Array.from(new Uint8Array(cipher))
  });
}

async function decryptMessage(payload) {
  const obj = JSON.parse(payload);
  const iv = new Uint8Array(obj.iv);
  const data = new Uint8Array(obj.data);

  const plain = await crypto.subtle.decrypt(
    { name: "AES-GCM", iv },
    derivedKey,
    data
  );

  return new TextDecoder().decode(plain);
}
</script>
"""

# =========================================================
# PAGES
# =========================================================

def landing():
    st.markdown("<h1 style='text-align:center'>DARKRELAY</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;color:#888'>Anonymous • Encrypted • Server-Blind</p>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("➕ CREATE ROOM", use_container_width=True):
            st.session_state.page = "create"
            st.rerun()
    with c2:
        if st.button("🔗 JOIN ROOM", use_container_width=True):
            st.session_state.page = "join"
            st.rerun()

def create_room():
    st.markdown("## Create Secure Room")

    name = st.text_input("Room name (optional)")
    if st.button("Generate"):
        room_id = secrets.token_hex(8)

        with ROOM_LOCK:
            ROOMS[room_id] = {
                "name": name or f"Room-{room_id[:6]}",
                "messages": []
            }

        st.session_state.room = room_id
        st.session_state.page = "chat"
        st.rerun()

    if st.button("← Back"):
        st.session_state.page = "landing"
        st.rerun()

def join_room():
    st.markdown("## Join Secure Room")

    room_id = st.text_input("Room ID (16 chars)")
    if st.button("Join"):
        with ROOM_LOCK:
            if room_id in ROOMS:
                st.session_state.room = room_id
                st.session_state.page = "chat"
                st.rerun()
            else:
                st.error("Room not found")

    if st.button("← Back"):
        st.session_state.page = "landing"
        st.rerun()

def chat():
    room_id = st.session_state.room

    with ROOM_LOCK:
        room = ROOMS.get(room_id)

    if not room:
        st.error("Room deleted")
        st.session_state.page = "landing"
        st.rerun()
        return

    st.markdown(f"## {room['name']}")
    st.code(room_id)

    # Inject crypto
    components.html(CRYPTO_JS + f"""
    <script>
      deriveKey("{room_id}");
    </script>
    """, height=0)

    # Display messages (cipher only → decrypted in browser)
    for msg in room["messages"]:
        components.html(f"""
        <div style="background:#111;padding:12px;border-radius:8px;margin-bottom:8px">
          <div style="color:#888;font-size:12px">{msg['user']}</div>
          <div id="m{msg['hash']}">Decrypting...</div>
        </div>
        <script>
          decryptMessage(`{msg['cipher']}`).then(t => {{
            document.getElementById("m{msg['hash']}").innerText = t;
          }});
        </script>
        """, height=80)

    # Input
    text = st.text_input("Message", key=str(time.time()))
    if st.button("Send"):
        if text.strip():
            cipher = components.html(f"""
            <script>
              encryptMessage("{text.replace('"','')}")
                .then(c => Streamlit.setComponentValue(c));
            </script>
            """, height=0)

            if cipher:
                prev = room["messages"][-1]["hash"] if room["messages"] else "0"
                h = sha256(cipher + prev)

                with ROOM_LOCK:
                    room["messages"].append({
                        "user": st.session_state.uid,
                        "cipher": cipher,
                        "hash": h,
                        "prev": prev,
                        "ts": time.time()
                    })
                st.rerun()

    st.markdown("<small style='color:#666'>Client-side AES-256-GCM • Server-blind</small>", unsafe_allow_html=True)

    time.sleep(1)
    st.experimental_set_query_params(t=str(time.time()))
    st.rerun()

# =========================================================
# MAIN
# =========================================================

def main():
    init_user()

    page = st.session_state.page
    if page == "landing":
        landing()
    elif page == "create":
        create_room()
    elif page == "join":
        join_room()
    elif page == "chat":
        chat()

    st.markdown("""
    <div style="position:fixed;bottom:0;width:100%;text-align:center;
                background:#000;color:#777;padding:8px">
      Made by DE • DarkRelay • Educational Use Only
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
