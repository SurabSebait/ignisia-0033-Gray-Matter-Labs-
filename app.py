"""
Streamlit UI for Vector-Based RAG
==================================
Interactive chat interface for querying Meridian policies via RAG.
"""

import streamlit as st
import os
from pathlib import Path
from dotenv import load_dotenv
from vectorRAG import VectorRAG

# Load environment variables from .env file
load_dotenv()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Meridian Policy RAG Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📚 Meridian Supply Chain Policy Assistant")
st.markdown("*Powered by Vector RAG + Google Gemini + Chroma Vector Database*")

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR - CONFIGURATION & DOCUMENT INGESTION
# ══════════════════════════════════════════════════════════════════════════════

# Initialize RAG on page load
if "rag" not in st.session_state:
    try:
        with st.spinner("🚀 Initializing RAG System..."):
            st.session_state.rag = VectorRAG(
                persist_dir="./chroma_db",
                google_api_key=os.environ.get("GOOGLE_API_KEY"),
                hf_api_key=os.environ.get("HUGGINGFACE_API_KEY"),
            )
    except Exception as e:
        st.error(f"❌ RAG Initialization Error: {str(e)}")
        st.info("⚠️ Make sure .env file has GOOGLE_API_KEY and HUGGINGFACE_API_KEY")
        st.session_state.rag = None

with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Show API status
    st.subheader("🔑 API Status")
    google_key_set = bool(os.environ.get("GOOGLE_API_KEY"))
    hf_key_set = bool(os.environ.get("HUGGINGFACE_API_KEY"))
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Google API", "✓ Set" if google_key_set else "✗ Missing")
    with col2:
        st.metric("HuggingFace API", "✓ Set" if hf_key_set else "✗ Missing")
    
    if not (google_key_set and hf_key_set):
        st.warning("⚠️ Please set API keys in .env file")
    
    # Embedding Model Info
    st.subheader("🧠 Embedding Model")
    st.info("Model: **BAAI/bge-small-en-v1.5**\n\nDimensions: 384\n\n(Fast, local embeddings - no API key needed)")
    
    # Document Ingestion
    st.subheader("📄 Document Management")
    
    # File Upload
    st.subheader("Upload Documents")
    uploaded_files = st.file_uploader(
        "Choose files to index",
        type=["pdf", "docx", "xlsx", "xls", "txt"],
        accept_multiple_files=True
    )
    
    if uploaded_files and st.button("📤 Ingest Documents"):
        if st.session_state.rag is None:
            st.error("❌ Initialize RAG system first!")
        else:
            # Save uploaded files temporarily
            temp_dir = Path("./temp_uploads")
            temp_dir.mkdir(exist_ok=True)
            
            file_paths = []
            for uploaded_file in uploaded_files:
                try:
                    temp_path = temp_dir / uploaded_file.name
                    temp_path.write_bytes(uploaded_file.getbuffer())
                    file_paths.append(str(temp_path))
                except Exception as e:
                    st.error(f"❌ Error saving file {uploaded_file.name}: {e}")
            
            if not file_paths:
                st.error("❌ No files were successfully saved")
                st.stop()
            
            with st.spinner(f"Ingesting {len(file_paths)} file(s)..."):
                try:
                    stats = st.session_state.rag.ingest(file_paths)
                    if stats['chunks'] > 0:
                        st.success(f"✅ Ingestion Complete!\n- Files: {stats['files']}\n- Pages: {stats['pages']}\n- Chunks: {stats['chunks']}")
                        st.session_state.ingestion_stats = stats
                    else:
                        st.warning("⚠️ No documents were indexed. Check file formats.")
                except Exception as e:
                    import traceback
                    st.error(f"❌ Ingestion Error: {str(e)}")
                    with st.expander("📋 Error Details"):
                        st.code(traceback.format_exc())
    
    # Display Stats
    st.subheader("📊 Database Stats")
    if st.session_state.rag:
        try:
            stats = st.session_state.rag.get_stats()
            st.metric("Total Documents Indexed", stats.get("total_documents", "N/A"))
        except:
            st.info("No documents indexed yet")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN CHAT INTERFACE
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("---")

# Chat history initialization
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Query Section
st.subheader("🔍 Ask a Question")

query = st.text_area(
    "Enter your question about Meridian policies:",
    placeholder="E.g., What is the ambient pallet storage rate?",
    height=80,
    key="query_input"
)

col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    submit_button = st.button("🚀 Search", key="submit_query", use_container_width=True)

with col2:
    clear_button = st.button("🗑️ Clear History", key="clear_history", use_container_width=True)

if clear_button:
    st.session_state.chat_history = []
    st.rerun()

# ──────────────────────────────────────────────────────────────────────────────
# PROCESS QUERY
# ──────────────────────────────────────────────────────────────────────────────

if submit_button:
    if st.session_state.rag is None:
        st.error("❌ Please initialize the RAG system first in the sidebar!")
    elif not query.strip():
        st.warning("⚠️ Please enter a question!")
    else:
        with st.spinner("🔍 Searching and generating answer..."):
            try:
                result = st.session_state.rag.query(query)
                st.session_state.chat_history.append(result)
            except Exception as e:
                st.error(f"❌ Query Error: {str(e)}")
                result = None

# ──────────────────────────────────────────────────────────────────────────────
# DISPLAY RESULTS
# ──────────────────────────────────────────────────────────────────────────────

if st.session_state.chat_history:
    st.markdown("---")
    st.subheader("📋 Results")
    
    # Show most recent result
    result = st.session_state.chat_history[-1]
    
    # Main Answer
    st.markdown("### ✅ Answer")
    st.info(result["answer"])
    
    # Sources Tab
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📍 Cited Sources")
        if result["sources"]:
            for source in result["sources"]:
                with st.expander(f"{source['label']} — {source['doc_id']}, Page {source['page_num']}"):
                    st.write(f"**Score:** {source['score']}")
                    st.write(f"**Preview:** {source['preview']}")
                    st.markdown(f"**Chunk Index:** {source['chunk_index']}")
        else:
            st.info("No sources explicitly cited in the answer.")
    
    with col2:
        st.markdown("### 🔗 All Retrieved Documents")
        st.write(f"(Searched top {len(result['retrieved'])} documents)")
        for doc in result["retrieved"]:
            with st.expander(f"{doc['label']} — {doc['doc_id']}, Page {doc['page_num']} (Score: {doc['score']})"):
                st.write(doc["preview"])

# ══════════════════════════════════════════════════════════════════════════════
# CHAT HISTORY SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════

if st.session_state.chat_history:
    st.markdown("---")
    st.subheader("💬 Query History")
    for idx, chat in enumerate(st.session_state.chat_history[-5:], 1):  # Show last 5
        with st.expander(f"Q{idx}: {chat['question'][:50]}..."):
            st.write(f"**Q:** {chat['question']}")
            st.write(f"**A:** {chat['answer'][:300]}...")
            st.write(f"**Sources Cited:** {len(chat['sources'])}")
