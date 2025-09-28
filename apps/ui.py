import streamlit as st
import requests
import json
import os
import uuid
import time

# --- Config ---
st.set_page_config(
    page_title="Documentation Generator",
    page_icon="📄",
    layout="centered"
)

API_BASE_URL = "http://localhost:8000"   # ADK server
APP_NAME = "shellhack_current"    # Matches your root_agent app_name

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

    # ADK returns a list of events
    events = response.json()
    doc_text = None

    doc_text = ""  # start with empty string

    for event in events:
        if "content" in event and "parts" in event["content"]:
            for part in event["content"]["parts"]:
                if "text" in part:
                    doc_text += part["text"] + "\n"

    if doc_text:
        st.session_state.docs.append(("Directory Scan", doc_text))
        st.code(doc_text, language="java")  # <-- displays in the UI
        return True


def run_uploaded_file(filename, code):
    """Send uploaded file contents to ADK."""
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
                    {"text": f"Generate documentation for file: {filename}\n\n{code}"}
                ]
            }
        })
    )

    if response.status_code != 200:
        st.error(f"Error: {response.text}")
        return False

    events = response.json()
    doc_text = ""  # start with empty string

    for event in events:
        if "content" in event and "parts" in event["content"]:
            for part in event["content"]["parts"]:
                if "text" in part:
                    doc_text += part["text"] + "\n"

    if doc_text:
        st.session_state.docs.append((filename, doc_text))
        return True
    return False


# --- UI ---
col1, col2, col3 = st.columns([2, 2, 1]) 
with col2:
    st.image("/Users/Student/Documents/club.png", width=100)
col1, col2, col3 = st.columns([1, 5, 1])  # widen the middle column
with col2:
    st.markdown(
        "<h1 style='margin: 0; text-align: center;'>Documentation Generator</h1>",
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

# --- File upload option ---
uploaded_files = st.file_uploader(
    "Upload your source files",
    type=["java", "py", "txt"],
    accept_multiple_files=True
)

# --- Merge options ---
st.subheader("Or upload two documents to make sure no merge error's occur")
col1, col2 = st.columns(2)  
with col1:
    directory1 = st.text_input("Directory 1", "./")
with col2:
    directory2 = st.text_input("Directory 2", "./")
col1, col2 = st.columns(2)
col1, col2 = st.columns(2)
with col1:
    extension1 = st.text_input("File extension 1", ".py")
with col2:
    extension2 = st.text_input("File extension 2", ".py")

with col1:
    uploaded_files1 = st.file_uploader(
        "Upload files for Directory 1",
        type=["java", "py", "txt"],
        accept_multiple_files=True,
        key="uploader1"
    )

with col2:
    uploaded_files2 = st.file_uploader(
        "Upload files for Directory 2",
        type=["java", "py", "txt"],
        accept_multiple_files=True,
        key="uploader2"
    )


# --- Buttons ---
if st.button("Generate Documentation"):
    if uploaded_files:
        for file in uploaded_files:
            code = file.read().decode("utf-8")
            run_uploaded_file(file.name, code)
    elif directory and extension:
        run_documentation(directory, extension)
    else:
        st.warning("Please provide either a directory/extension or upload files.")

# Display results
st.subheader("📑 Documentation Output")
if st.session_state.docs:
    for idx, (source, doc) in enumerate(st.session_state.docs, 1):
        st.markdown(f"### Run {idx}: {source}")
        st.code(doc, language="markdown")
else:
    st.info("No documentation generated yet.")