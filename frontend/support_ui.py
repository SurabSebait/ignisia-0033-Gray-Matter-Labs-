import streamlit as st
import requests
import time

st.title("Customer Support - Support Personnel Portal")

# Login
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None

if not st.session_state.logged_in:
    st.header("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        response = requests.post("http://localhost:8000/auth/login", json={"username": username, "password": password})
        if response.status_code == 200:
            data = response.json()
            st.session_state.logged_in = True
            st.session_state.role = data["role"]
            st.rerun()
        else:
            st.error("Invalid credentials")
    st.stop()

if st.session_state.role != "support":
    st.error("Access denied")
    st.stop()

# 3-panel layout
col1, col2, col3 = st.columns([1, 2, 1])

# Left Panel: Ticket List
with col1:
    st.header("Tickets")
    if st.button("Refresh Tickets"):
        st.rerun()
    
    response = requests.get("http://localhost:8000/tickets/")
    if response.status_code == 200:
        tickets = response.json()
        for ticket in tickets:
            if st.button(f"Ticket {ticket['id']}: {ticket['query'][:50]}... - {ticket['status']}", key=ticket['id']):
                st.session_state.selected_ticket = ticket['id']
                st.rerun()

# Center Panel: Chat Window
with col2:
    st.header("Chat")
    if "selected_ticket" in st.session_state:
        ticket_id = st.session_state.selected_ticket
        # Load messages
        response = requests.get(f"http://localhost:8000/messages/{ticket_id}/messages")
        if response.status_code == 200:
            messages = response.json()
            for msg in messages:
                st.write(f"{msg['sender_type']}: {msg['message']}")
        
        if st.button("Generate AI Response"):
            # Get conversation history
            history = [msg['message'] for msg in messages]
            query = next((msg['message'] for msg in messages if msg['sender_type'] == 'user'), "")
            ai_request = {
                "ticket_id": ticket_id,
                "query": query,
                "conversation_history": history
            }
            ai_response = requests.post("http://localhost:8000/ai/generate-response", json=ai_request).json()
            st.session_state.ai_response = ai_response
            st.rerun()
        
        if "ai_response" in st.session_state:
            ai_resp = st.session_state.ai_response
            edited_response = st.text_area("Edit AI Response", value=ai_resp['response'])
            if st.button("Send Response"):
                message_data = {"sender_type": "agent", "message": edited_response}
                requests.post(f"http://localhost:8000/messages/{ticket_id}/messages", json=message_data)
                # Update ticket status or something
                st.success("Response sent")
                del st.session_state.ai_response
                st.rerun()
            if st.button("Regenerate"):
                del st.session_state.ai_response
                st.rerun()

# Right Panel: Citations
with col3:
    st.header("Citations")
    if "ai_response" in st.session_state:
        citations = st.session_state.ai_response['citations']
        for cit in citations:
            with st.expander(f"{cit['source_name']} - {cit['reference']}"):
                st.write(cit['text'])
                st.write(f"Relevance: {cit.get('relevance_score', 'N/A')}")

# Auto-refresh tickets every 30 seconds
time.sleep(30)
st.rerun()