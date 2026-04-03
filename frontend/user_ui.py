import streamlit as st
import requests
import json

st.title("Customer Support - User Portal")

# Assume user_id is set, e.g., from auth
user_id = "user123"  # Placeholder

# Chat interface
st.header("Chat with Support")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if prompt := st.chat_input("Enter your query"):
    # Create ticket
    ticket_data = {"user_id": user_id, "query": prompt}
    response = requests.post("http://localhost:8000/tickets/", json=ticket_data)
    if response.status_code == 200:
        ticket = response.json()
        ticket_id = ticket["id"]
        # Send message
        message_data = {"sender_type": "user", "message": prompt}
        requests.post(f"http://localhost:8000/messages/{ticket_id}/messages", json=message_data)
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()
    else:
        st.error("Failed to create ticket")

# View past queries
st.header("Past Queries")
response = requests.get("http://localhost:8000/tickets/")
if response.status_code == 200:
    tickets = response.json()
    for ticket in tickets:
        if ticket["user_id"] == user_id:
            st.write(f"Ticket {ticket['id']}: {ticket['query']} - Status: {ticket['status']}")