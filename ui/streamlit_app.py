import streamlit as st
import sys
import os
import threading
from pathlib import Path

# Add parent dir to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.repo_manager import RepoManager
from core.simple_rag import SimpleRAG
from core.llm import GeminiClient
from core.router import Router
from core.agentic_client import AgenticClient
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Page Config
st.set_page_config(
    page_title="Git Assist AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Initialization ---

if "initialized" not in st.session_state:
    st.session_state.repo_mgr = RepoManager()
    st.session_state.rag = SimpleRAG()
    st.session_state.llm = GeminiClient()
    st.session_state.router = Router()
    st.session_state.agentic_client = AgenticClient()
    st.session_state.initialized = True
    st.session_state.messages = []
    st.session_state.evidence = ""
    st.session_state.trace = ""
    st.session_state.debug = ""

# --- Sidebar ---

with st.sidebar:
    st.title("Git Assist AI 🤖")
    
    st.header("Repo Manager")
    
    # Repo List
    repos = [d.name for d in st.session_state.repo_mgr.data_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
    selected_repo = st.selectbox(
        "Select Repository",
        repos if repos else ["No repos found"],
        index=0 if repos else 0
    )
    
    if selected_repo != "No repos found":
         # Clear history if repo changes (handled by logic check or manual clear)
         pass

    st.divider()
    
    # Clone Repo
    with st.expander("Clone Repository"):
        url_input = st.text_input("Git URL", placeholder="https://github.com/...")
        if st.button("Clone Repo"):
            if url_input:
                with st.spinner(f"Cloning {url_input}..."):
                    try:
                        st.session_state.repo_mgr.clone_repo(url_input)
                        st.success("Clone complete!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Clone Error: {e}")
            else:
                st.warning("Please enter a URL.")

    # Index Docs
    if st.button("Index Documents", disabled=(not repos)):
        if selected_repo and selected_repo != "No repos found":
            with st.spinner(f"Indexing {selected_repo}..."):
                try:
                    docs = st.session_state.repo_mgr.index_docs(selected_repo)
                    st.session_state.rag.ingest(docs)
                    st.success(f"Indexed {len(docs)} documents.")
                except Exception as e:
                    st.error(f"Index Error: {e}")

    st.divider()
    
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.session_state.evidence = ""
        st.session_state.trace = ""
        st.session_state.debug = ""
        st.session_state.agentic_client.clear_history()
        st.rerun()

    st.divider()
    
    # Inspector Tabs in Sidebar
    st.subheader("Inspector")
    tab1, tab2, tab3 = st.tabs(["Evidence", "Trace", "Debug"])
    
    with tab1:
        st.text_area("Evidence", value=st.session_state.evidence, height=300, disabled=True)
    
    with tab2:
        st.text_area("MCP Trace", value=st.session_state.trace, height=300, disabled=True)
    
    with tab3:
        st.text_area("Debug", value=st.session_state.debug, height=300, disabled=True)


# --- Main Chat Area ---

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat Input
if prompt := st.chat_input("Ask something about the code..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Process Response
    if selected_repo == "No repos found":
        error_msg = "Please clone and select a repository first."
        st.session_state.messages.append({"role": "assistant", "content": error_msg})
        with st.chat_message("assistant"):
            st.error(error_msg)
    else:
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Route
                    route = st.session_state.router.route(prompt)
                    st.session_state.debug += f"Query: '{prompt}' -> Route: {route.upper()}\n"
                    
                    response_text = ""
                    
                    if route == "agentic":
                        # Agentic Path
                        repo_path = str(st.session_state.repo_mgr.get_repo_path(selected_repo))
                        
                        def on_agent_log(msg):
                            st.session_state.trace += msg + "\n"
                            # We can't easily update the sidebar in real-time during execution without placeholders
                            # but session state update will show on next rerun/interaction
                            
                        response_text = st.session_state.agentic_client.ask(prompt, repo_path, on_log=on_agent_log)
                        st.session_state.evidence = "Agentic search performed. See Trace tab.\n" + st.session_state.evidence
                        
                    else:
                        # Simple Path (RAG)
                        context = st.session_state.rag.retrieve(prompt, repo_filter=selected_repo)
                        
                        # Evidence
                        new_evidence = ""
                        context_text = ""
                        for doc in context:
                            new_evidence += f"File: {doc['id']}\n---\n{doc['text'][:200]}...\n\n"
                            context_text += f"Source: {doc['id']}\nContent: {doc['text']}\n\n"
                        
                        st.session_state.evidence = new_evidence + "\n" + st.session_state.evidence
                        
                        if not context_text:
                            response_text = "No relevant documentation found."
                        else:
                            # Ask LLM
                            llm_prompt = f"Answer based on:\n{context_text}\n\nQuestion: {prompt}"
                            response_text = st.session_state.llm.ask(llm_prompt)
                    
                    st.markdown(response_text)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
                    
                except Exception as e:
                    st.error(f"Error: {e}")
                    st.session_state.messages.append({"role": "assistant", "content": f"Error: {e}"})
