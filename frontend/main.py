import streamlit as st
import requests
import time
from datetime import datetime

# Page config
st.set_page_config(
    page_title="AI Customer Support",
    page_icon="🎫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Zendesk-like styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
    }
    .ticket-card {
        background: white;
        border: 1px solid #e1e5e9;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .ticket-locked {
        background: #fff3cd;
        border-color: #ffeaa7;
    }
    .status-badge {
        padding: 0.25rem 0.5rem;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: bold;
    }
    .status-open { background: #d4edda; color: #155724; }
    .status-pending { background: #fff3cd; color: #856404; }
    .status-resolved { background: #d1ecf1; color: #0c5460; }
    .chat-message {
        padding: 0.75rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        max-width: 80%;
    }
    .chat-user { background: #007bff; color: white; margin-left: auto; }
    .chat-agent { background: #f8f9fa; color: #333; }
    .chat-ai { background: #e9ecef; color: #495057; border-left: 4px solid #6c757d; }
    .sidebar-content {
        padding: 1rem;
    }
    .citation-card {
        background: #f8f9fa;
        border-left: 4px solid #007bff;
        padding: 0.75rem;
        margin: 0.5rem 0;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# Session state initialization
if "page" not in st.session_state:
    st.session_state.page = "login"
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = None
if "selected_ticket" not in st.session_state:
    st.session_state.selected_ticket = None
if "tickets_cache" not in st.session_state:
    st.session_state.tickets_cache = []
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = datetime.now()

def login_page():
    st.markdown('<div class="main-header"><h1>🎫 AI Customer Support Platform</h1><p>Powered by Advanced AI for Seamless Support</p></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("🔐 Login to Your Account")
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submitted = st.form_submit_button("🚀 Login", use_container_width=True)
            
            if submitted:
                if username and password:
                    with st.spinner("Authenticating..."):
                        try:
                            response = requests.post("http://localhost:8000/auth/login", 
                                                   json={"username": username, "password": password}, 
                                                   timeout=10)
                            if response.status_code == 200:
                                data = response.json()
                                st.session_state.user = username
                                st.session_state.role = data["role"]
                                st.session_state.page = data["role"]  # user, admin, or support
                                st.success(f"Welcome back, {username}!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Invalid username or password")
                        except requests.exceptions.RequestException:
                            st.error("Unable to connect to server. Please try again.")
                else:
                    st.error("Please enter both username and password")

def user_ui():
    st.markdown('<div class="main-header"><h2>👤 Customer Portal</h2><p>Get instant support for your queries</p></div>', unsafe_allow_html=True)
    
    # Sidebar with user info and logout
    with st.sidebar:
        st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
        st.subheader(f"👋 Welcome, {st.session_state.user}")
        st.caption(f"Role: {st.session_state.role.title()}")
        if st.button("🚪 Logout", use_container_width=True):
            logout()
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("💬 Start a Conversation")
        
        # Chat interface
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        # Display chat history
        chat_container = st.container()
        with chat_container:
            for msg in st.session_state.messages:
                if msg["role"] == "user":
                    st.markdown(f'<div class="chat-message chat-user">{msg["content"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="chat-message chat-agent">{msg["content"]}</div>', unsafe_allow_html=True)
        
        # Chat input
        if prompt := st.chat_input("Type your message here..."):
            # Create ticket if first message
            if not st.session_state.messages:
                ticket_data = {"user_id": st.session_state.user, "query": prompt}
                response = requests.post("http://localhost:8000/tickets/", json=ticket_data)
                if response.status_code == 200:
                    ticket = response.json()
                    st.session_state.current_ticket = ticket["id"]
            
            # Send message
            if "current_ticket" in st.session_state:
                message_data = {"sender_type": "user", "message": prompt}
                requests.post(f"http://localhost:8000/messages/{st.session_state.current_ticket}/messages", json=message_data)
                st.session_state.messages.append({"role": "user", "content": prompt})
                st.rerun()
    
    with col2:
        st.subheader("📋 Your Tickets")
        
        # Fetch and display user's tickets
        try:
            response = requests.get("http://localhost:8000/tickets/", timeout=5)
            if response.status_code == 200:
                tickets = response.json()
                user_tickets = [t for t in tickets if t.get("user_id") == st.session_state.user]
                
                if user_tickets:
                    for ticket in user_tickets[-5:]:  # Show last 5
                        status_class = f"status-{ticket['status']}"
                        st.markdown(f"""
                        <div class="ticket-card">
                            <strong>Ticket #{ticket['id'][:8]}</strong><br>
                            <span class="status-badge {status_class}">{ticket['status'].upper()}</span><br>
                            <small>{ticket['query'][:50]}...</small>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No tickets yet. Start a conversation!")
        except:
            st.warning("Unable to load tickets")

def admin_ui():
    st.markdown('<div class="main-header"><h2>⚙️ Admin Portal</h2><p>Manage knowledge base and system settings</p></div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
        st.subheader(f"👋 Welcome, {st.session_state.user}")
        st.caption(f"Role: {st.session_state.role.title()}")
        if st.button("🚪 Logout", use_container_width=True):
            logout()
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.subheader("📤 Upload Knowledge Base Files")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### File Upload")
        uploaded_file = st.file_uploader("Choose a file", type=["pdf", "xlsx", "eml"], 
                                       help="Upload PDF, Excel, or Email files to update the knowledge base")
        
        if uploaded_file is not None:
            with st.spinner("Processing file..."):
                # In production, upload to GCS and trigger processing
                time.sleep(2)  # Simulate processing
                st.success(f"✅ {uploaded_file.name} uploaded successfully!")
                st.info("File processing will be completed in the background.")
    
    with col2:
        st.markdown("### Upload History")
        # Mock upload history
        st.markdown("""
        <div class="ticket-card">
            <strong>user_manual.pdf</strong><br>
            <span class="status-badge status-resolved">COMPLETED</span><br>
            <small>Uploaded 2 hours ago</small>
        </div>
        <div class="ticket-card">
            <strong>faq.xlsx</strong><br>
            <span class="status-badge status-pending">PROCESSING</span><br>
            <small>Uploaded 30 min ago</small>
        </div>
        """, unsafe_allow_html=True)

def support_ui():
    st.markdown('<div class="main-header"><h2>🎧 Support Dashboard</h2><p>Manage customer tickets with AI assistance</p></div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
        st.subheader(f"👋 Welcome, {st.session_state.user}")
        st.caption(f"Role: {st.session_state.role.title()}")
        if st.button("🚪 Logout", use_container_width=True):
            logout()
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Main 3-panel layout
    col1, col2, col3 = st.columns([1, 2, 1])
    
    # Left Panel: Control Panel
    with col1:
        st.subheader("🎛️ Control Panel")
        
        # Search and filters
        search_query = st.text_input("🔍 Search tickets", "", placeholder="Search by query...")
        status_filter = st.selectbox("📊 Status", ["All", "open", "pending", "resolved"])
        priority_filter = st.selectbox("⚡ Priority", ["All", "low", "medium", "high"])
        my_tickets = st.checkbox("👤 My Tickets Only")
        
        col_refresh, col_new = st.columns(2)
        with col_refresh:
            if st.button("🔄 Refresh", use_container_width=True):
                refresh_tickets()
        
        # Fetch tickets
        tickets = get_tickets()
        
        # Apply filters
        filtered_tickets = []
        for ticket in tickets:
            if search_query and search_query.lower() not in ticket["query"].lower():
                continue
            if status_filter != "All" and ticket["status"] != status_filter:
                continue
            if priority_filter != "All" and ticket.get("priority", "medium") != priority_filter:
                continue
            if my_tickets and ticket.get("assigned_to") != st.session_state.user:
                continue
            filtered_tickets.append(ticket)
        
        st.subheader("📋 Tickets")
        
        ticket_container = st.container()
        with ticket_container:
            for ticket in filtered_tickets[:10]:  # Limit display
                locked = ticket.get("locked_by")
                is_locked_by_me = locked == st.session_state.user
                is_locked_by_other = locked and locked != st.session_state.user
                
                card_class = "ticket-card ticket-locked" if is_locked_by_other else "ticket-card"
                status_class = f"status-{ticket['status']}"
                
                lock_icon = "🔒" if is_locked_by_other else "🔓" if is_locked_by_me else "📋"
                
                if st.button(f"{lock_icon} {ticket['query'][:35]}...", 
                           key=f"ticket_{ticket['id']}", 
                           disabled=is_locked_by_other,
                           use_container_width=True):
                    handle_ticket_selection(ticket['id'])
    
    # Center Panel: Chat
    with col2:
        st.subheader("💬 Conversation")
        
        if st.session_state.selected_ticket:
            ticket_id = st.session_state.selected_ticket
            
            # Load messages
            messages = get_messages(ticket_id)
            
            # Display chat
            chat_container = st.container()
            with chat_container:
                for msg in messages:
                    msg_class = f"chat-{msg['sender_type']}"
                    st.markdown(f'<div class="chat-message {msg_class}">{msg["message"]}</div>', unsafe_allow_html=True)
            
            # AI Response section
            if st.button("🤖 Generate AI Response", use_container_width=True):
                generate_ai_response(ticket_id, messages)
            
            if "ai_response" in st.session_state:
                ai_resp = st.session_state.ai_response
                edited_response = st.text_area("Edit AI Response", value=ai_resp['response'], height=100)
                
                col_send, col_regen = st.columns(2)
                with col_send:
                    if st.button("📤 Send Response", use_container_width=True):
                        send_response(ticket_id, edited_response)
                with col_regen:
                    if st.button("🔄 Regenerate", use_container_width=True):
                        del st.session_state.ai_response
                        st.rerun()
        else:
            st.info("👈 Select a ticket from the left panel to start chatting")
    
    # Right Panel: Context
    with col3:
        st.subheader("📚 Context")
        
        if "ai_response" in st.session_state:
            st.markdown("### 📖 Citations")
            citations = st.session_state.ai_response['citations']
            for cit in citations:
                with st.expander(f"📄 {cit['source_name']} - {cit['reference']}"):
                    st.write(cit['text'])
                    if 'relevance_score' in cit:
                        st.caption(f"Relevance: {cit['relevance_score']}")
        
        if st.session_state.selected_ticket:
            st.markdown("### 🔍 Similar Tickets")
            similar_tickets = get_similar_tickets(st.session_state.selected_ticket)
            for sim in similar_tickets[:3]:
                with st.expander(f"🎯 {sim['query'][:30]}... ({sim['similarity_score']})"):
                    st.write(f"**Last Response:** {sim['last_response']}")

def logout():
    # Unlock current ticket if support user
    if st.session_state.role == "support" and st.session_state.selected_ticket:
        try:
            requests.patch(f"http://localhost:8000/tickets/{st.session_state.selected_ticket}/unlock?agent_id={st.session_state.user}")
        except:
            pass
    
    # Clear session
    st.session_state.page = "login"
    st.session_state.user = None
    st.session_state.role = None
    st.session_state.selected_ticket = None
    st.session_state.messages = []
    if "ai_response" in st.session_state:
        del st.session_state.ai_response
    st.rerun()

def refresh_tickets():
    st.session_state.tickets_cache = []
    st.session_state.last_refresh = datetime.now()

def get_tickets():
    # Cache tickets for 30 seconds
    now = datetime.now()
    if (now - st.session_state.last_refresh).seconds > 30 or not st.session_state.tickets_cache:
        try:
            response = requests.get("http://localhost:8000/tickets/", timeout=5)
            if response.status_code == 200:
                st.session_state.tickets_cache = response.json()
                st.session_state.last_refresh = now
        except:
            st.session_state.tickets_cache = []
    
    return st.session_state.tickets_cache

def get_messages(ticket_id):
    try:
        response = requests.get(f"http://localhost:8000/messages/{ticket_id}/messages", timeout=5)
        return response.json() if response.status_code == 200 else []
    except:
        return []

def get_similar_tickets(ticket_id):
    try:
        response = requests.get(f"http://localhost:8000/tickets/{ticket_id}/similar", timeout=5)
        return response.json() if response.status_code == 200 else []
    except:
        return []

def handle_ticket_selection(ticket_id):
    # Unlock previous ticket
    if st.session_state.selected_ticket and st.session_state.selected_ticket != ticket_id:
        try:
            requests.patch(f"http://localhost:8000/tickets/{st.session_state.selected_ticket}/unlock?agent_id={st.session_state.user}")
        except:
            pass
    
    # Lock new ticket
    try:
        response = requests.patch(f"http://localhost:8000/tickets/{ticket_id}/lock?agent_id={st.session_state.user}")
        if response.status_code == 200:
            st.session_state.selected_ticket = ticket_id
            st.rerun()
        else:
            st.error("Failed to lock ticket")
    except:
        st.error("Unable to connect to server")

def generate_ai_response(ticket_id, messages):
    history = [msg['message'] for msg in messages]
    query = next((msg['message'] for msg in messages if msg['sender_type'] == 'user'), "")
    
    ai_request = {
        "ticket_id": ticket_id,
        "query": query,
        "conversation_history": history
    }
    
    try:
        response = requests.post("http://localhost:8000/ai/generate-response", json=ai_request, timeout=10)
        if response.status_code == 200:
            st.session_state.ai_response = response.json()
            st.rerun()
        else:
            st.error("Failed to generate AI response")
    except:
        st.error("Unable to connect to AI service")

def send_response(ticket_id, message):
    message_data = {"sender_type": "agent", "message": message}
    try:
        response = requests.post(f"http://localhost:8000/messages/{ticket_id}/messages", json=message_data)
        if response.status_code == 200:
            st.success("Response sent successfully!")
            # Clear AI response and refresh
            if "ai_response" in st.session_state:
                del st.session_state.ai_response
            st.rerun()
        else:
            st.error("Failed to send response")
    except:
        st.error("Unable to send response")

# Main app logic
if st.session_state.page == "login":
    login_page()
elif st.session_state.page == "user":
    user_ui()
elif st.session_state.page == "admin":
    admin_ui()
elif st.session_state.page == "support":
    support_ui()
else:
    login_page()