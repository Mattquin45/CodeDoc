# CodeDoc/ShellHacks 2025 project

CodeDoc is a ShellHacks 2025 project that implemented the use of Google's ADK to create easier use of coding documentation and preventing merge errors. This specifically focuses on the aspect of explaining code that is either uploaded or shown in your laptop/computer directory. With tools like ADK, Streamlit, and ADK api server allowed the creation and goal of this project to be shown through the process. This allows companies and teams lessen the stress of trying to understand different coding syntax and focus on their project milestones. 


# 🚀 Stack

- Google ADK (AI agents)
- Streamlit (FrontEnd UI)
- ADK API server ( API )

# 🚀 Features

- Upload one or more source files.
- Automatically generate documentation (classes, methods, variables, descriptions).
- Streamlit UI for easy interaction and being able to record past documentation requests.
- Backend powered by ADK + API server.

# 📦 Requirements

- Python 3.9+
- ADK
- Streamlit (pip install streamlit)
- Other dependencies in requirements.txt

# ⚙️ Installation
- Clone this repository
- git clone https://github.com/Mattquin45/CodeDoc.git
- cd CodeDoc.git

# Create a virtual environment
- python -m venv venv        # Windows
- python3 -m venv venv       #Mac
- source venv/bin/activate   # Mac/Linux
- venv\Scripts\activate      # Windows

# Install dependencies
- pip install -r requirements.txt

# 🔑 Environment Setup

Create a .env file in the project root:
- ADK_AGENT_PATH=./agents
- API_SERVER_PORT=8000
- STREAMLIT_PORT=8501
- GOOGLE_API_KEY=your_api_key_here

 # ▶️ Running the Project
Start the ADK API Server
- python -m adk.api_server --port 8000

Start the Streamlit UI
- streamlit run apps.ui.py --server.port 8501

Open your browser at 👉 http://localhost:8501
or click on the link thats produced on the streamlit terminal

- Please always make sure that both the API server is running at the same time as streamlit

# 💡 Usage

- Enter a directory path or upload files directly in the Streamlit UI.
- Choose a file extension (e.g., .py, .java).
- Click Generate Documentation.
- Documentation will be displayed in the app (and optionally saved to .txt) and also downloaded on your system

Example input:

Directory: /Users/Student/Documents/MyProject
Extension: .java

# 🛠️ Development Notes

- The main ADK agent is defined in root_agent.py.

- Streamlit UI logic is in ui.py.

- Documentation output is handled in the agent.py by default.

- Always before testing on the UI, press create new session!

# ❗ Troubleshooting

- In your ui.py file make sure that your APP-NAME is the name of your project file. 
- Make sure that adk api_server is being run on your folder. I recomend running adk api_server . on the directory that 
  the project is contained in.
- Make sure your api keys are correct and consistent because that can affect the performance of the FrontEnd
- Files not showing in Streamlit → Ensure you are uploading supported file types (.py, .java, .txt).

# Hi My name is Matthew!
- My part in this specific shellhacks project was putting my part in both the ADK development and fully implemeting a UI in       streamlit by connecting it to the backend ADK API. I helped in cooperating in any part anybdoy needed help and mainly focused   on making the FrontEnd and API backend. In ADK development, I help create our project idea and helped in checking if frontend   and the ADK agents were compatible.


