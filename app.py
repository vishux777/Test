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
                    self.CHANNEL_THEMES = state_data.get('channel_themes', {})  # Track channel themes
            else:
                self.ROOMS = {}
                self.ENCRYPTION_KEY = Fernet.generate_key()
                self.ACTIVE_USERS = {}  # room_id -> {user_id: last_seen_timestamp}
                self.CHANNEL_THEMES = {}  # room_id -> theme_name
                self._save_state()
        except Exception as e:
            print(f"Error loading state: {e}")
            self.ROOMS = {}
            self.ENCRYPTION_KEY = Fernet.generate_key()
            self.ACTIVE_USERS = {}
            self.CHANNEL_THEMES = {}
    
    def _save_state(self):
        """Save state to disk"""
        try:
            state_data = {
                'rooms': self.ROOMS,
                'encryption_key': self.ENCRYPTION_KEY,
                'active_users': self.ACTIVE_USERS,
                'channel_themes': self.CHANNEL_THEMES
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
                self.CHANNEL_THEMES[room_id] = "Cinematic Dark"  # Default theme
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
    
    def get_channel_theme(self, room_id: str) -> str:
        """Get the theme for a specific channel"""
        with self._lock:
            return self.CHANNEL_THEMES.get(room_id, "Cinematic Dark")
    
    def set_channel_theme(self, room_id: str, theme_name: str):
        """Set the theme for a specific channel"""
        with self._lock:
            self.CHANNEL_THEMES[room_id] = theme_name
            self._save_state()
    
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
# FIXED ACTIVE USERS SIDEBAR WITH PROPER ERROR HANDLING
# ====================
def display_active_users_sidebar(room_id: str):
    """Display active users in the current room with proper error handling"""
    if not room_id:
        return
    
    try:
        global_state = get_global_state()
        
        with st.sidebar:
            st.markdown("### 👥 Active Users")
            
            # Update current user activity with error handling
            try:
                global_state.update_user_activity(room_id, st.session_state.user_id)
            except Exception as e:
                print(f"Error updating user activity: {e}")
            
            # Cleanup inactive users
            try:
                removed_count = global_state.cleanup_inactive_users(room_id)
            except Exception as e:
                print(f"Error cleaning up inactive users: {e}")
                removed_count = 0
            
            # Get active users with error handling
            try:
                active_users = global_state.get_active_users(room_id)
            except Exception as e:
                print(f"Error getting active users: {e}")
                active_users = {}
            
            if active_users:
                st.markdown(f"**{len(active_users)}** users online")
                
                for user_id, last_seen in active_users.items():
                    is_current_user = user_id == st.session_state.user_id
                    user_display = "👤 You" if is_current_user else f"👤 User_{user_id[-6:]}"
                    status_color = "#10b981" if is_current_user else "#8a63d2"
                    
                    st.markdown(f"""
                    <div style="
                        padding: 0.6rem 1rem; 
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
            try:
                if global_state.should_cleanup_messages(room_id):
                    room_data = global_state.get_room(room_id)
                    if room_data and len(room_data.get("messages", [])) > 0:
                        st.warning("⚠️ No active users - messages will be cleared")
                        
                        if st.button("🗑️ Clear All Messages", use_container_width=True):
                            try:
                                if global_state.clear_room_messages(room_id):
                                    st.success("✅ Messages cleared")
                                    st.rerun()
                            except Exception as e:
                                st.error("❌ Failed to clear messages")
                                print(f"Error clearing messages: {e}")
            except Exception as e:
                print(f"Error checking cleanup status: {e}")
    
    except Exception as e:
        st.error("❌ Error loading active users")
        print(f"Error in display_active_users_sidebar: {e}")

# ====================
# PROFESSIONAL UI COMPONENTS WITH OPTIMIZED SIZING
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
# ULTRA-FAST CHAT INTERFACE WITH PROFESSIONAL STYLING
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
    
    # Create placeholder for ultra-fast auto-updating content
    chat_placeholder = st.empty()
    
    # Ultra-fast auto-update mechanism (0.5 seconds)
    current_time = time.time()
    if current_time - st.session_state.last_activity_update >= 0.5:
        st.session_state.last_activity_update = current_time
        
        # Check for new messages
        if st.session_state.auto_updater.check_for_updates(st.session_state.current_room):
            st.rerun()
    
    # Chat header with professional styling
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
        🔒 ENCRYPTED • LIVE • ANONYMOUS • 0.5s UPDATES
    </div>
    """, unsafe_allow_html=True)
    
    # Display messages with professional styling and ultra-fast updates
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
        
        # Display messages with professional animations (last 50 messages)
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
                
                # Professional message styling based on user
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
                """, unsafe_for_html=True)
        
        st.markdown('</div>', unsafe_for_html=True)
    
    # Professional message input with improved sizing
    col1, col2 = st.columns([5, 1])
    with col1:
        message_key = f"message_input_{st.session_state.get('message_key', 0)}"
        message = st.text_input(
            "🔒 Type your message...",
            key=message_key,
            label_visibility="collapsed",
            placeholder="Your encrypted message here..."
        )
    with col2:
        send_clicked = st.button("⚡ SEND", type="primary", use_container_width=True)
    
    # Handle message sending with professional flow
    if send_clicked and message and message.strip():
        # Get previous hash with error handling
        previous_hash = "0" * 64
        if messages:
            previous_hash = messages[-1].get("hash", "0" * 64)
        
        # Show encryption process
        with st.spinner("🔐 Encrypting..."):
            time.sleep(0.15)  # Minimal delay for professional feel
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
            st.toast("✅ Message sent securely!", icon="🔒")
            # Increment key to clear input
            st.session_state.message_key = st.session_state.get('message_key', 0) + 1
            st.rerun()
        else:
            st.error("❌ Failed to send message")

# ====================
# MAIN APP WITH PROFESSIONAL DESIGN
# ====================
def main():
    st.set_page_config(
        page_title="DarkRelay • DE STUDIO",
        page_icon="🔒",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    inject_professional_styles()
    render_header()
    initialize_session()
    
    # Show enhanced active users sidebar when in a room
    if st.session_state.current_room:
        display_active_users_sidebar(st.session_state.current_room)
    
    # Main content area
    main_area = st.container()
    
    with main_area:
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

if __name__ == "__main__":
    main()
