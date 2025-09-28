📄 Documentation Generator

A web-based documentation generator powered by ADK, an ADK API server, and a Streamlit interface.
Upload your source files (.java, .py, .txt, etc.), and the system will analyze the code and generate structured documentation automatically.

🚀 Features

Upload one or more source files.

Automatically generate documentation (classes, methods, variables, descriptions).

Streamlit UI for easy interaction.

Backend powered by ADK + API server.

📦 Requirements

Python 3.9+

ADK
 installed

Streamlit (pip install streamlit)

Other dependencies in requirements.txt

⚙️ Installation
# Clone this repository
git clone https://github.com/yourusername/yourrepo.git
cd yourrepo

# Create a virtual environment
python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows

# Install dependencies
pip install -r requirements.txt

🔑 Environment Setup

Create a .env file in the project root:

ADK_AGENT_PATH=./agents
API_SERVER_PORT=8000
STREAMLIT_PORT=8501
GOOGLE_API_KEY=your_api_key_here

▶️ Running the Project
1. Start the ADK API Server
python -m adk.api_server --port 8000

2. Start the Streamlit UI
streamlit run app.py --server.port 8501


Open your browser at 👉 http://localhost:8501

💡 Usage

Enter a directory path or upload files directly in the Streamlit UI.

Choose a file extension (e.g., .py, .java).

Click Generate Documentation.

Documentation will be displayed in the app (and optionally saved to .txt).

Example input:

Directory: /Users/Student/Documents/MyProject
Extension: .java

🛠️ Development Notes

The main ADK agent is defined in root_agent.yaml.

Streamlit UI logic is in app.py.

Documentation output is handled in /output by default.

❗ Troubleshooting

ValueError: No root_agent found… → Ensure root_agent.yaml exists in your ADK directory.

PermissionError: [Errno 13] Permission denied → Check folder permissions.

Files not showing in Streamlit → Ensure you are uploading supported file types (.py, .java, .txt).

🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss your ideas.

📜 License

MIT License — free to use and modify.
