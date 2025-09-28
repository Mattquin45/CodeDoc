import streamlit as st
import requests
import json
import os
import sys
import uuid
import time
import tempfile
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from agent.agent import process_uploaded_file, root_agent

# --- Config ---
st.set_page_config(
    page_title="CodeDoc",
    page_icon="/Users/Student/Documents/club.png",
    layout="centered"
)

API_BASE_URL = "http://localhost:8000"   
APP_NAME = "CodeDoc"    

# --- Session State ---
if "user_id" not in st.session_state:
    st.session_state.user_id = f"user-{uuid.uuid4()}"

if "session_id" not in st.session_state:
    st.session_state.session_id = None

if "docs" not in st.session_state:
    st.session_state.docs = []


# --- API Helpers ---
def create_session():
    """Create a new session with the documentation agent."""
    session_id = f"session-{int(time.time())}"
    response = requests.post(
        f"{API_BASE_URL}/apps/{APP_NAME}/users/{st.session_state.user_id}/sessions/{session_id}",
        headers={"Content-Type": "application/json"},
        data=json.dumps({})
    )

    if response.status_code == 200:
        st.session_state.session_id = session_id
        st.session_state.docs = []
        return True
    else:
        st.error(f"Failed to create session: {response.text}")
        return False


def run_documentation(directory, extension):
    """Send directory + extension to ADK and process output."""
    if not st.session_state.session_id:
        st.error("No active session. Please create one first.")
        return False

    response = requests.post(
        f"{API_BASE_URL}/run",
        headers={"Content-Type": "application/json"},
        data=json.dumps({
            "app_name": APP_NAME,
            "user_id": st.session_state.user_id,
            "session_id": st.session_state.session_id,
            "new_message": {
                "role": "user",
                "parts": [
                    {"text": f"Generate documentation for directory: {directory}, extension: {extension}"}
                ]
            }
        })
    )

    if response.status_code != 200:
        st.error(f"Error: {response.text}")
        return False

    events = response.json()
    doc_text = None

    doc_text = ""  

    for event in events:
        if "content" in event and "parts" in event["content"]:
            for part in event["content"]["parts"]:
                if "text" in part:
                    doc_text += part["text"] + "\n"

    if doc_text:
        st.session_state.docs.append(("Directory Scan", doc_text))
        st.code(doc_text, language="java")  # <-- displays in the UI
        return True


def run_uploaded_file(file):
    """
    Process a single uploaded file, run it through the ADK agent, and store the generated documentation.
    """
    # --- Save file to temp ---
    temp_dir = tempfile.gettempdir()
    txt_file_path = os.path.join(temp_dir, file.name)
    code = file.read().decode("utf-8")
    with open(txt_file_path, "w") as f:
        f.write(code)

    # --- Add file to agent state so pattern_matching can see it ---
    process_uploaded_file(file.name, code)

    # --- Build the message for ADK ---
    message_text = (
        f"Generate documentation for the uploaded file: {txt_file_path}\n\n"
        "Please process it and return human-readable documentation."
    )

    response = requests.post(
        f"{API_BASE_URL}/run",
        headers={"Content-Type": "application/json"},
        data=json.dumps({
            "app_name": APP_NAME,
            "user_id": st.session_state.user_id,
            "session_id": st.session_state.session_id,
            "new_message": {
                "role": "user",
                "parts": [{"text": message_text}]
            }
        })
    )

    if response.status_code != 200:
        st.error(f"Error processing file {file.name}: {response.text}")
        return None
    
    # --- Collect documentation output ---
    events = response.json()
    doc_text = ""
    for event in events:
        if "content" in event and "parts" in event["content"]:
            for part in event["content"]["parts"]:
                if "text" in part:
                    doc_text += part["text"] + "\n"

    # --- Store in session state ---
    if doc_text:
        st.session_state.docs.append((file.name, doc_text))
        return doc_text
    return None


# --- UI ---
col1, col2, col3 = st.columns([2, 2, 1]) 
with col2:
    st.image("/Users/Student/Documents/club.png", width=100)
col1, col2, col3 = st.columns([1, 5, 1])  
with col2:
    st.markdown(
        "<h1 style='margin: 0; text-align: center;'>CodeDoc</h1>",
        unsafe_allow_html=True
    )

# Sidebar: session management
with st.sidebar:
    st.header("Session Management")
    if st.session_state.session_id:
        st.success(f"Active session: {st.session_state.session_id}")
        if st.button("➕ New Session"):
            create_session()
    else:
        st.warning("No active session")
        if st.button("➕ Create Session"):
            create_session()

    st.divider()
    st.caption("This app interacts with the Documentation Agent via the ADK API Server.")
    st.caption("Make sure the ADK API Server is running on port 8000.")

# Main input
st.subheader("Generate Documentation")
col1, col2 = st.columns([3, 1])
with col1:
    directory = st.text_input("Directory path", "./")
with col2:
    extension = st.text_input("File extension", ".py")


# Display results
st.subheader("📑 Documentation Output")
if st.session_state.docs:
    for idx, (source, doc) in enumerate(st.session_state.docs, 1):
        st.markdown(f"### Run {idx}: {source}")
        st.code(doc, language="markdown")
else:
    st.info("No documentation generated yet.")