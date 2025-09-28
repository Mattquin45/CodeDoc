import asyncio
import logging
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
APP_NAME = "CodeDoc"  # change this name every time if your file name is different for it to work.
USER_ID = "dev_user_01"
SESSION_ID_BASE = "loop_exit_tool_session" 
GEMINI_MODEL = "gemini-2.0-flash"
BOLD = '\033[1m'
RESET = '\033[0m'
ITALIC = "\x1B[3m"
RESET2 = "\x1B[0m"

# --- State Keys ---
STATE_CURRENT_DOC = "current_array"
STATE_CRITICISM = "criticism"
COMPLETION_PHRASE = "Documentation complete"


# --- Tool Definition ---
def process_uploaded_file(filename: str, code: str, tool_context: Optional[ToolContext] = None):
    """
    Store uploaded file content in state for the agents to process.
    """
    text_file = os.path.abspath(filename + ".txt")
    with open(text_file, 'w') as f:
        f.write(code)

    if tool_context is not None:
        existing_files = tool_context.state.get("temp:processed_data", [])
        tool_context.state["temp:processed_data"] = existing_files + [text_file]
        tool_context.state["criticism"] = "Documentation complete"

    return [text_file]


def exit_loop(tool_context: ToolContext):
    """Call this function ONLY when the critique indicates no further changes are needed, signaling the iterative process should end."""
    print(f"  [Tool Call] exit_loop triggered by {tool_context.agent_name}")
    tool_context.actions.escalate = True
    return {}


def get_files(directory1: str, extension1: str = ".py"):
    found_files = []
    for root, _, files in os.walk(directory1):
        for file in files:
            if file.endswith(extension1):
                found_files.append(os.path.join(root, file))

    return found_files


def text_translation(files: List[str], extension: str, tool_context: ToolContext):
    text_files = []
    for file in files:
        new_file = os.path.basename(file) + ".txt"
        with open(file, 'r') as f:
            code = f.read()
        with open(new_file, 'w') as txt_file:
            txt_file.write(code)
            text_files.append(new_file)

    processed_data = text_files
    tool_context.state["temp:processed_data"] = processed_data
    return text_files

def pattern_matching_java(tool_context: ToolContext):
    text_files = tool_context.state.get("temp:processed_data", [])
    if not text_files:
        return []

    array = [[] for _ in range(len(text_files))]
    access = {"public", "private", "protected", "(", ")", "}", "{", "throws"}
    stopper = "#"

    for index, file1 in enumerate(text_files):
        try:
            with open(file1, "r") as file:
                for line in file:
                    count = sum(1 for item in access if item in line.strip())
                    if count >= 4 and not line.startswith(stopper):
                        array[index].append(line)
        except FileNotFoundError:
            print(f"Error: The file '{file1}' was not found.")
        except Exception as e:
            print(f"An error occurred while reading {file1}: {e}")

    return array


def pattern_matching_python(tool_context: ToolContext):
    text_files = tool_context.state.get("temp:processed_data", [])
    if not text_files:
        return [] 

    array = [[] for _ in range(len(text_files))]
    keyword = "def"
    stopper = "#"

    for index, file1 in enumerate(text_files):
        try:
            with open(file1, "r") as file:
                for line in file:
                    if line.startswith(stopper):
                        continue
                    elif keyword in line.strip():
                        array[index].append(line)
        except FileNotFoundError:
            print(f"Error: The file '{file1}' was not found.")
        except Exception as e:
            print(f"An error occurred while reading {file1}: {e}")

    return array



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
    A list of uploaded file paths or text content, in which case you will process those files directly without scanning directories.
    Finally you will return an array of the .txt files to writing agent.
    
""",
    tools=[get_files, text_translation, process_uploaded_file],
    output_key=STATE_CURRENT_DOC
)

# STEP 2a: Writing Agent (Inside the Refinement Loop)
interpreter_agent_in_loop = LlmAgent(
    name="WritingAgent",
    model=GEMINI_MODEL,
    include_contents='none',
    output_key=STATE_CRITICISM,
    instruction=f"""You are a documentation AI who's job is to analyze code and be able to provide documentation on 
    what it can accomplish

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
    
    if its in java: use the pattern_matching_java method with no parameter
     to check the entire script for methods:
        It will return a 2D array, in each index of the array is a list of the methods for the corresponding 
        list of text files given by reader agent
    if its in python: use the pattern_matching_python method with parameter no parameter
     to check the entire script for methods:
        It will return a 2D array, in each index is a list of the methods for the corresponding list of text files
        given by reader agent 
        
     Example: reader agent output: [Script1.txt , Script2.txt, Script3.txt]  
     Example output: output of pattern_matching methods: [(Script1_methods):[Method1 , Method2, Method3],...]
     
     This is just to fetch the methods, you must fetch the rest manually
        
    After finding all components you must provide a description of it that is concise and to the point 
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
    
    Returns {COMPLETION_PHRASE} only after a minimum of two itterations have passed and all elements of the 
    notepad have been interpreted
    
""",
    tools=[pattern_matching_java, pattern_matching_python],
    description="Analyses the file to create proper documentation for the code given",
)

# STEP 2b: Refiner/Exiter Agent (Inside the Refinement Loop)
documentation_agent_in_loop = LlmAgent(
    name="documentation_agent",
    model=GEMINI_MODEL,
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
        read_agent,  
        refinement_loop  
    ],
    description="Writes an initial document and then iteratively refines it with critique using an exit tool."

)

