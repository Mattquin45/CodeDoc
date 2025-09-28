import streamlit as st
import requests
import json
import os
import sys
import uuid
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

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
    doc_text = ""

    for event in events:
        if "content" in event and "parts" in event["content"]:
            for part in event["content"]["parts"]:
                if "text" in part:
                    doc_text += part["text"] + "\n"

    if doc_text:
        st.session_state.docs.append((f"Directory: {directory}", doc_text))
        return True
    return False


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
directory = st.text_input("Directory path", "./")

# Let user pick an extension
extension = st.selectbox(
    "File extension",
    options=[".py", ".java", ".js", ".cpp", ".txt", "Other"],
    index=0
)

# If "Other", allow custom extension
if extension == "Other":
    extension = st.text_input("Enter custom extension (include the dot)", ".py")

# Run button
if st.button("Generate Documentation"):
    if directory and extension:
        run_documentation(directory, extension)
    else:
        st.warning("Please provide both directory path and extension.")

# Display results
st.subheader("📑 Documentation Output")
if st.session_state.docs:
    for idx, (source, doc) in enumerate(st.session_state.docs, 1):
        st.markdown(f"### Run {idx}: {source}")
        st.code(doc, language="markdown")
else:
    st.info("No documentation generated yet.")
