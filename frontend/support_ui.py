import streamlit as st
import requests
import time

st.set_page_config(layout="wide")

# ---------- STYLES ----------
st.markdown("""
<style>
.block-container { padding-top: 1rem; }

/* Chat bubbles */
.user-msg { background:#e3f2fd; padding:10px; border-radius:10px; margin-bottom:8px; }
.agent-msg { background:#e8f5e9; padding:10px; border-radius:10px; margin-bottom:8px; }
.ai-msg { background:#fff3e0; padding:10px; border-radius:10px; margin-bottom:8px; }

/* Ticket card */
.ticket-card {
    padding:10px;
    border-radius:10px;
    margin-bottom:8px;
    border:1px solid #ddd;
}

/* Section header */
.section-header {
    font-weight:600;
    font-size:18px;
    margin:10px 0;
}

/* Scroll */
.scrollable {
    max-height:75vh;
    overflow-y:auto;
}
</style>
""", unsafe_allow_html=True)

st.title("🎧 Support Dashboard")

# ---------- LOGIN ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None

if not st.session_state.logged_in:
    st.header("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        res = requests.post("http://localhost:8000/auth/login",
                            json={"username": username, "password": password})
        if res.status_code == 200:
            data = res.json()
            st.session_state.logged_in = True
            st.session_state.role = data["role"]
            st.session_state.agent_id = username
            st.rerun()
        else:
            st.error("Invalid credentials")
    st.stop()

if st.session_state.role != "support":
    st.error("Access denied")
    st.stop()

# ---------- LOGOUT ----------
if st.button("Logout"):
    if "selected_ticket" in st.session_state:
        requests.patch(f"http://localhost:8000/tickets/{st.session_state.selected_ticket}/unlock?agent_id={st.session_state.agent_id}")
    st.session_state.clear()
    st.rerun()

agent_id = st.session_state.agent_id

# ---------- LAYOUT ----------
col1, col2, col3 = st.columns([1.2, 2.5, 1.3])

# ---------- LEFT PANEL ----------
with col1:
    st.markdown("<div class='section-header'>📋 Tickets</div>", unsafe_allow_html=True)

    search = st.text_input("🔍 Search")
    status = st.selectbox("Status", ["All", "open", "pending", "resolved"])
    priority = st.selectbox("Priority", ["All", "low", "medium", "high"])
    my_only = st.checkbox("My Tickets")

    tickets = requests.get("http://localhost:8000/tickets/").json()

    st.markdown('<div class="scrollable">', unsafe_allow_html=True)

    for t in tickets:
        if search and search.lower() not in t["query"].lower():
            continue
        if status != "All" and t["status"] != status:
            continue
        if priority != "All" and t.get("priority", "medium") != priority:
            continue
        if my_only and t.get("assigned_to") != agent_id:
            continue

        locked = t.get("locked_by")
        locked_other = locked and locked != agent_id

        st.markdown(f"""
        <div class="ticket-card">
            <b>{t['query'][:40]}...</b><br>
            Status: {t['status']}<br>
            {f'🔒 Locked by {locked}' if locked_other else ''}
        </div>
        """, unsafe_allow_html=True)

        if locked_other:
            st.button("Locked", disabled=True, key=f"lock_{t['id']}")
        else:
            if st.button("Open", key=t['id']):
                if "selected_ticket" in st.session_state and st.session_state.selected_ticket != t['id']:
                    requests.patch(f"http://localhost:8000/tickets/{st.session_state.selected_ticket}/unlock?agent_id={agent_id}")

                res = requests.patch(f"http://localhost:8000/tickets/{t['id']}/lock?agent_id={agent_id}")
                if res.status_code == 200:
                    st.session_state.selected_ticket = t['id']
                    st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# ---------- CENTER PANEL ----------
with col2:
    st.markdown("<div class='section-header'>💬 Conversation</div>", unsafe_allow_html=True)

    if "selected_ticket" in st.session_state:
        tid = st.session_state.selected_ticket

        if "current_messages" not in st.session_state or st.session_state.get("current_ticket") != tid:
            msgs = requests.get(f"http://localhost:8000/messages/{tid}/messages")
            st.session_state.current_messages = msgs.json() if msgs.status_code == 200 else []
            st.session_state.current_ticket = tid

        for m in st.session_state.current_messages:
            if m['sender_type'] == "user":
                st.markdown(f"<div class='user-msg'><b>User:</b><br>{m['message']}</div>", unsafe_allow_html=True)
            elif m['sender_type'] == "agent":
                st.markdown(f"<div class='agent-msg'><b>You:</b><br>{m['message']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='ai-msg'><b>AI:</b><br>{m['message']}</div>", unsafe_allow_html=True)

        colA, colB = st.columns(2)

        with colA:
            if st.button("⚡ Generate AI"):
                history = [m['message'] for m in st.session_state.current_messages]
                query = next((m['message'] for m in st.session_state.current_messages if m['sender_type']=="user"), "")

                ai = requests.post("http://localhost:8000/ai/generate-response",
                                   json={"ticket_id": tid, "query": query, "conversation_history": history})
                st.session_state.ai_response = ai.json()
                st.rerun()

        with colB:
            if st.button("🔄 Regenerate"):
                st.session_state.pop("ai_response", None)
                st.rerun()

        if "ai_response" in st.session_state:
            ai = st.session_state.ai_response
            edited = st.text_area("Edit Response", value=ai['response'])

            if st.button("Send"):
                requests.post(f"http://localhost:8000/messages/{tid}/messages",
                              json={"sender_type":"agent","message":edited})

                msgs = requests.get(f"http://localhost:8000/messages/{tid}/messages")
                st.session_state.current_messages = msgs.json()
                st.success("Sent")
                st.session_state.pop("ai_response")
                st.rerun()

# ---------- RIGHT PANEL ----------
with col3:
    st.markdown("<div class='section-header'>📚 Context</div>", unsafe_allow_html=True)

    if "ai_response" in st.session_state:
        st.markdown("**Citations**")
        for c in st.session_state.ai_response['citations']:
            st.markdown(f"""
            <div class="ticket-card">
                <b>{c['source_name']}</b><br>
                {c['text']}<br>
                <i>{c.get('reference','')} | Score: {c.get('relevance_score','N/A')}</i>
            </div>
            """, unsafe_allow_html=True)

    if "selected_ticket" in st.session_state:
        st.markdown("**Similar Tickets**")
        sim = requests.get(f"http://localhost:8000/tickets/{st.session_state.selected_ticket}/similar")
        if sim.status_code == 200:
            for s in sim.json():
                st.markdown(f"""
                <div class="ticket-card">
                    <b>{s['query'][:40]}...</b><br>
                    Score: {s['similarity_score']}<br>
                    <i>{s['last_response'][:100]}...</i>
                </div>
                """, unsafe_allow_html=True)

# ---------- AUTO REFRESH ----------
time.sleep(10)
st.rerun()