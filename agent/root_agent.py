# shellhack_current/agent/root_agent.py

import os
from dotenv import load_dotenv
from google.adk.agents import LlmAgent, SequentialAgent, LoopAgent
from google.adk.tools.tool_context import ToolContext
from google.adk import Agent

# --- Load environment variables ---
load_dotenv()
API_KEY = os.environ.get("GOOGLE_GENAI_API_KEY")
GEMINI_MODEL = "gemini-2.0-flash"

# --- Constants ---
COMPLETION_PHRASE = "Documentation complete"
STATE_CURRENT_DOC = "current_array"
STATE_CRITICISM = "criticism"


# --- Tools ---
def exit_loop(tool_context: ToolContext):
    """Stop the refinement loop if documentation is complete."""
    tool_context.actions.escalate = True
    return {}


# --- File reading / processing tools ---
def get_files(directory: str, extension: str = ".py"):
    import os
    found_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(extension):
                found_files.append(os.path.join(root, file))
    return found_files


def text_translation(files):
    text_files = []
    for file in files:
        new_file = os.path.basename(file) + ".txt"
        with open(file, "r") as f:
            code = f.read()
        with open(new_file, "w") as txt_file:
            txt_file.write(code)
            text_files.append(new_file)
    return text_files


# --- Agents ---
# STEP 1: Initial reading agent
read_agent = LlmAgent(
    model=GEMINI_MODEL,
    api_key=API_KEY,
    name="read_agent",
    description="Scan directory and create .txt files",
    instruction="Use get_files() and text_translation() to return array of .txt files.",
    tools=[get_files, text_translation],
    output_key=STATE_CURRENT_DOC
)

# STEP 2a: Writing agent
writing_agent = LlmAgent(
    model=GEMINI_MODEL,
    api_key=API_KEY,
    name="writing_agent",
    instruction=f"""
You are a documentation AI. Review files in {{current_array}} and produce structured documentation.
After completing, respond with {COMPLETION_PHRASE}.
""",
    output_key=STATE_CRITICISM
)

# STEP 2b: Refiner/Exiter agent
documentation_agent = LlmAgent(
    model=GEMINI_MODEL,
    api_key=API_KEY,
    name="documentation_agent",
    instruction=f"""
Refine the document in {{current_array}} using critique {{criticism}}.
If critique includes '{COMPLETION_PHRASE}', call exit_loop immediately.
""",
    tools=[exit_loop],
    output_key=STATE_CURRENT_DOC
)

# STEP 3: Refinement loop
refinement_loop = LoopAgent(
    name="refinement_loop",
    sub_agents=[writing_agent, documentation_agent],
    max_iterations=5
)

# STEP 4: Root sequential pipeline
root_agent = SequentialAgent(
    name="IterativeDocumentationPipeline",
    sub_agents=[read_agent, refinement_loop],
    description="Reads code files and iteratively generates/refines documentation."
)

# --- Expose root_agent ---
# ADK looks for a variable named 'root_agent' in this file
