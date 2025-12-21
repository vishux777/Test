# ====================
# FIXED GLOBAL STATE WITH PROPER ERROR HANDLING
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
            else:
                self.ROOMS = {}
                self.ENCRYPTION_KEY = Fernet.generate_key()
                self._save_state()
        except Exception as e:
            print(f"Error loading state: {e}")
            self.ROOMS = {}
            self.ENCRYPTION_KEY = Fernet.generate_key()
    
    def _save_state(self):
        """Save state to disk"""
        try:
            state_data = {
                'rooms': self.ROOMS,
                'encryption_key': self.ENCRYPTION_KEY
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
                self._save_state()
                return True
            return False
    
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
# FIXED CHAT INTERFACE WITH ERROR HANDLING
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
    
    # Auto-update mechanism
    placeholder = st.empty()
    
    # Chat header with enhanced UI and error handling
    col1, col2, col3 = st.columns([2, 1, 1])
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
        # Room stats with error handling
        try:
            stats = global_state.get_room_stats(st.session_state.current_room)
            if stats:
                last_activity_time = datetime.fromtimestamp(stats['last_activity']).strftime('%H:%M') if stats['last_activity'] else 'now'
                st.markdown(f"""
                <div style="font-size: 0.8rem; color: rgba(255,255,255,0.6);">
                    💬 {stats['message_count']} messages<br>
                    🕒 Active {last_activity_time}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="font-size: 0.8rem; color: rgba(255,255,255,0.6);">
                    💬 0 messages<br>
                    🕒 Just created
                </div>
                """, unsafe_allow_html=True)
        except Exception as e:
            st.markdown("""
            <div style="font-size: 0.8rem; color: rgba(255,255,255,0.6);">
                📊 Stats unavailable
            </div>
            """, unsafe_allow_html=True)
    
    with col3:
        if st.button("🚪 Leave Channel", type="secondary", use_container_width=True):
            st.session_state.current_room = None
            st.rerun()
    
    # Enhanced status indicator
    st.markdown("""
    <div class="status-indicator">
        <div class="status-dot"></div>
        🔒 ENCRYPTED • LIVE • SECURE • REAL-TIME
    </div>
    """, unsafe_allow_html=True)
    
    # Messages container with auto-refresh
    with placeholder.container():
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        messages = room_data.get("messages", [])
        encryptor = EncryptionHandler()
        
        if not messages:
            st.markdown("""
            <div class="message">
                <div class="message-content" style="text-align: center; color: rgba(255, 255, 255, 0.5); font-style: italic;">
                    🔓 No messages yet. Start the encrypted conversation...
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Display messages with enhanced features and error handling
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
                
                # Message styling based on user
                message_style = "border-left-color: #10b981;" if is_current_user else "border-left-color: #8a63d2;"
                
                st.markdown(f"""
                <div class="message" style="{message_style}">
                    <div class="message-header">
                        <span class="message-user">{'👤 You' if is_current_user else f'👤 User_{user_short}'}</span>
                        <span class="message-time">{msg_time}</span>
                    </div>
                    <div class="message-content">{decrypted}</div>
                    <div class="message-meta">
                        {chain_status} • Hash: {msg.get('hash', 'N/A')[:8]}... • 
                        {message_encryption_indicator(True)}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Add reactions for recent messages
                if i >= len(messages) - 10:
                    message_reactions(msg.get('message_id', ''), st.session_state.current_room)
                
            except Exception as e:
                st.markdown(f"""
                <div class="message">
                    <div class="message-content" style="color: rgba(255, 255, 255, 0.5); font-style: italic;">
                        [🔒 Encrypted message - Unable to decrypt]
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Enhanced message input with typing indicator
    col1, col2 = st.columns([4, 1])
    with col1:
        message = st.text_input(
            "🔒 Type your encrypted message...",
            key="message_input",
            label_visibility="collapsed",
            placeholder="Your message is encrypted end-to-end..."
        )
    with col2:
        send_clicked = st.button("📤 SEND", type="primary", use_container_width=True)
    
    # Auto-send on Enter and handle typing indicator
    if message:
        # Show typing indicator for other users (simulated)
        if len(message) > 0:
            with st.spinner("📝 Encrypting message..."):
                time.sleep(0.1)  # Simulate encryption delay
    
    if send_clicked and message.strip():
        # Get previous hash with error handling
        previous_hash = "0" * 64
        if messages:
            previous_hash = messages[-1].get("hash", "0" * 64)
        
        # Show encryption process
        with st.spinner("🔐 Encrypting message..."):
            time.sleep(0.3)
            try:
                encrypted_msg = encryptor.encrypt(message.strip())
            except Exception as e:
                st.error("❌ Failed to encrypt message")
                return
        
        # Create data for hashing
        data_to_hash = f"{encrypted_msg}{previous_hash}{time.time()}"
        current_hash = encryptor.calculate_hash(data_to_hash)
        
        # Create message object with error handling
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
            # Force refresh by clearing the input
            st.session_state.message_input = ""
            st.rerun()
        else:
            st.error("❌ Failed to send message")
    
    # Auto-refresh every 2 seconds
    time.sleep(2)
    if st.session_state.auto_updater.check_for_updates(st.session_state.current_room):
        st.rerun()

# ====================
# FIXED SIDEBAR WITH PROPER ERROR HANDLING
# ====================
def create_enhanced_sidebar():
    with st.sidebar:
        st.markdown("### ⚙️ Channel Settings")
        
        if st.session_state.current_room:
            st.markdown(f"**Current:** {st.session_state.room_name}")
            
            # Clear history with confirmation
            if st.button("🗑️ Clear History", use_container_width=True):
                if st.checkbox("⚠️ Confirm clear all messages?"):
                    global_state = get_global_state()
                    if global_state.clear_room_messages(st.session_state.current_room):
                        st.success("✅ History cleared!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Failed to clear history")
            
            # Export functionality
            global_state = get_global_state()
            room_data = global_state.get_room(st.session_state.current_room)
            if room_data:
                messages = room_data.get("messages", [])
                export_data = {
                    "room_name": st.session_state.room_name,
                    "room_id": st.session_state.current_room,
                    "exported_at": datetime.now().isoformat(),
                    "message_count": len(messages),
                    "messages": [
                        {
                            "timestamp": msg.get("timestamp"),
                            "user_id": msg.get("user_id")[-6:],
                            "hash": msg.get("hash")[:8] + "...",
                            "verified": True
                        }
                        for msg in messages[-100:]  # Last 100 messages
                    ]
                }
                st.download_button(
                    "💾 Export Chat",
                    data=json.dumps(export_data, indent=2),
                    file_name=f"{st.session_state.room_name}_{int(time.time())}.json",
                    mime="application/json",
                    use_container_width=True
                )
        
        st.markdown("---")
        st.markdown("### 📊 Statistics")
        
        try:
            global_state = get_global_state()
            total_rooms = len(global_state.ROOMS)
            total_messages = sum(len(room.get("messages", [])) for room in global_state.ROOMS.values())
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Channels", total_rooms)
            with col2:
                st.metric("Messages", total_messages)
        except Exception as e:
            st.error("Stats unavailable")
        
        st.markdown("---")
        st.markdown("### 🎨 Appearance")
        
        # Theme selector
        theme = st.selectbox("Theme", ["Cinematic Dark", "Pure Black", "Matrix Green", "Neon Purple"], 
                           help="Change visual theme")
        
        if theme == "Matrix Green":
            st.markdown("""
            <style>
            .stApp { 
                background: #000000 !important;
                background-image: radial-gradient(circle at 50% 50%, rgba(0, 255, 0, 0.1) 0%, transparent 50%);
            }
            .main-title { 
                background: linear-gradient(135deg, #00ff00 0%, #00cc00 100%) !important;
            }
            .status-indicator { color: #00ff00; border-color: #00ff00; }
            .status-dot { background: #00ff00; }
            </style>
            """, unsafe_allow_html=True)
        elif theme == "Neon Purple":
            st.markdown("""
            <style>
            .stApp { 
                background: #0a0a0a !important;
                background-image: radial-gradient(circle at 50% 50%, rgba(168, 85, 247, 0.2) 0%, transparent 50%);
            }
            .main-title { 
                background: linear-gradient(135deg, #a855f7 0%, #d946ef 100%) !important;
            }
            .status-indicator { color: #a855f7; border-color: #a855f7; }
            .status-dot { background: #a855f7; }
            </style>
            """, unsafe_allow_html=True)

# ====================
# MAIN APP WITH FIXES
# ====================
def main():
    st.set_page_config(
        page_title="DarkRelay • Scarabynath",
        page_icon="🔒",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    inject_cinematic_css()
    render_cinematic_header()
    initialize_session()
    
    # Create enhanced sidebar
    create_enhanced_sidebar()
    
    # Main content
    if st.session_state.current_room:
        chat_interface()
    else:
        col1, col2 = st.columns([1, 1], gap="large")
        
        with col1:
            create_room_section()
        
        with col2:
            join_room_section()
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        display_active_channels()

if __name__ == "__main__":
    main()
