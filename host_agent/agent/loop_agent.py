import asyncio
import os
from google.adk.agents import LoopAgent, LlmAgent, BaseAgent, SequentialAgent
from google.genai import types
from google.adk.runners import InMemoryRunner
from google.adk.agents.invocation_context import InvocationContext
from google.adk.tools.tool_context import ToolContext
from typing import AsyncGenerator, Optional
from google.adk.events import Event, EventActions
from typing import List

# --- Constants ---
APP_NAME = "documentation_generation"  # New App Name
USER_ID = "dev_user_01"
SESSION_ID_BASE = "loop_exit_tool_session"  # New Base Session ID
GEMINI_MODEL = "gemini-2.0-flash"
BOLD = '\033[1m'
RESET = '\033[0m'
ITALIC = "\x1B[3m"
RESET2 = "\x1B[0m"

# --- State Keys ---
STATE_CURRENT_DOC = "current_array"
STATE_CRITICISM = "criticism"
# Define the exact phrase the Critic should use to signal completion
COMPLETION_PHRASE = "Documentation complete"


# --- Tool Definition ---
def exit_loop(tool_context: ToolContext):
    """Call this function ONLY when the critique indicates no further changes are needed, signaling the iterative process should end."""
    print(f"  [Tool Call] exit_loop triggered by {tool_context.agent_name}")
    tool_context.actions.escalate = True
    # Return empty dict as tools should typically return JSON-serializable output
    return {}


def get_files(directory1: str, extension1: str = ".py"):
    found_files = []
    for root, _, files in os.walk(directory1):
        for file in files:
            if file.endswith(extension1):
                found_files.append(os.path.join(root, file))

    return found_files


def text_translation(files: List[str], extension: str):
    text_files = []
    for file in files:
        new_file = os.path.basename(file) + ".txt"
        with open(file, 'r') as f:
            code = f.read()
        with open(new_file, 'w') as txt_file:
            # Write the content to the text file
            txt_file.write(code)
            text_files.append(new_file)

    return text_files


# --- Agent Definitions ---

# STEP 1: Initial Reading Agent (Runs ONCE at the beginning)
read_agent = LlmAgent(
    model=GEMINI_MODEL,
    name="read_agent",
    description="Asks user for a directory or a github repository, scans the files fthat have the extension the user "
                "gives"
                "and turn them into .txt",
    instruction="""You are an agent that given a local directory will scan the files in said directory for
    files of the extension given by the user, or by default .py values. 
    You will use the get_files method to scan a directory and return an array of all the extension files 
    that the user specified, and the text_translation method with the parameters equal to the array you 
    returned from get_files and the user's declared extension. 
    Finally you will return an array of the .txt files to writing agent.
    
""",
    tools=[get_files, text_translation],
    output_key=STATE_CURRENT_DOC
)

# STEP 2a: Writing Agent (Inside the Refinement Loop)
interpreter_agent_in_loop = LlmAgent(
    name="WritingAgent",
    model=GEMINI_MODEL,
    include_contents='none',
    # MODIFIED Instruction: More nuanced completion criteria, look for clear improvement paths.
    instruction=f"""You are a documentation AI who's job is to analyze code and be able to provide documentation on what it can accomplish

    **Documents to Review:**
    ```
    {{current_array}}
    ```
    **Task:**
    Review the code and look for essential components such as:
    1. Imported libraries
    2. Class name
    3.What it inherits and extends
    4. Description of the class
    5. Methods that it declares and its parameters 
    6. Constructors
    7. Class variables 
    After finding these components you must provide a description of it that is concise and to the point 
    Example:
    USES: java.util.scanner, java.io.file , 
    CLASS NAME : Math()
    EXTENDS: sqrt.interface 
    INHERITS: Numbers()
    METHODS:
    1. Name: add() , return type: int, parameters: int x, int y Description: Adds two integers together
    2. Name: subtract() , return type: double, parameters : int z , int w , Description: Subtracts two integers together
    .....
    CONSTRUCTORS: Math(), Math(int x , int y) ...
    CLASS_VARIABLES: int pi = 3.14, int e = 2.17
    
    After doing this respond with {COMPLETION_PHRASE}
    
""",
    description="Analyses the file to create proper documentation for the code given",
    output_key=STATE_CRITICISM
)

# STEP 2b: Refiner/Exiter Agent (Inside the Refinement Loop)
documentation_agent_in_loop = LlmAgent(
    name="documentation_agent",
    model=GEMINI_MODEL,
    # Relies solely on state via placeholders
    include_contents='none',
    instruction=f"""You are a Documentation Creator tasked with formatting a documentation file given some parameters.
    **Current Document:**
    ```
    {{current_array}}
    ```
    **Critique/Suggestions:**
    {{criticism}}

    **Task:**
    Analyze the document produced by the writing agent.
    You will now style the document to make it readable for humans, follow this format:
    ===================================================================================
    Class class_name:
        Inherits:                           Extends:
        |inheritance_list|                  |interface_list|
        |...             |                  |...           |
    ===================================================================================
    Description:
      1. inheritance class #1
      2. inheritance class #2
      3. ...
    -------------------------------------------------------------------------------------
      1. interface #1
      2. interface #2
      3. ...
    ===================================================================================
    Constructors:
        Constructor1() || Constructor2(parameter 1) || ... 
    -------------------------------------------------------------------------------------
    Description:
        Constructor 1 description: (parameters, what object it creates, who it inherits from)
        ------------------------------------------------------------------------------
        Constructor 2 description: .....
        -----------------------------------------------------------------------------
        .....
    ===================================================================================
    Methods:
        Method1() || Method2() || ... 
    -------------------------------------------------------------------------------------
    Description:
        Method 1 description: (return type, what it accomplishes, parameters, how to use it)
        ------------------------------------------------------------------------------
        Method 2 description: .....
        -----------------------------------------------------------------------------
        .....
    ===================================================================================
    Class variables:
       class variable1
        ---------------
       class variable2
        ---------------
        ...
    ===================================================================================
    
    After translating it to readable human code,
    If the {{criticism}} text includes the phrase '{COMPLETION_PHRASE}', call `exit_loop` immediately.
    Otherwise, produce a refined version of the documentation.
""",
    description="Refines the document based on writing_agent parameters, or calls exit_loop if document indicates "
                "completion.",
    tools=[exit_loop],  # Provide the exit_loop tool
    output_key=STATE_CURRENT_DOC  # Overwrites state['current_document'] with the refined version
)


# STEP 2: Refinement Loop Agent
refinement_loop = LoopAgent(
    name="RefinementLoop",
    # Agent order is crucial: Critique first, then Refine/Exit
    sub_agents=[
        interpreter_agent_in_loop,
        documentation_agent_in_loop,
    ],
    max_iterations=5  # Limit loops
)

# STEP 3: Overall Sequential Pipeline
# For ADK tools compatibility, the root agent must be named `root_agent`
root_agent = SequentialAgent(
    name="IterativeWritingPipeline",
    sub_agents=[
        read_agent,  # Run first to create initial doc
        refinement_loop  # Then run the critique/refine loop
    ],
    description="Writes an initial document and then iteratively refines it with critique using an exit tool."

)

