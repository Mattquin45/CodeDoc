from google.adk.agents import ParallelAgent, LlmAgent, SequentialAgent

import loop_agent

# --- 2. Create the ParallelAgent (Runs researchers concurrently) ---
# This agent orchestrates the concurrent execution of the researchers.
# It finishes once all researchers have completed and stored their results in state.
parallel_research_agent = ParallelAgent(
    name="ParallelWebResearchAgent",
    sub_agents=[loop_agent, loop_agent],
    description="Runs multiple research agents in parallel to gather information."
)

# --- 3. Define the Merger Agent (Runs *after* the parallel agents) ---
# This agent takes the results stored in the session state by the parallel agents
# and synthesizes them into a single, structured response with attributions.
merger_agent = LlmAgent(
    name="SynthesisAgent",
    model=loop_agent.GEMINI_MODEL,  # Or potentially a more powerful model if needed for synthesis
    instruction="""You are an AI Assistant responsible for checking the result of two loop_agent and comparing their attributes.
    
    The loop_agent will return a description of coding files in the same project. Your job is to take the summaries
    provided by the writer agent of the two loop_agents and compare them to each other. Your job is to check for any 
    vulnerabilities when merging files of two different projects, you should look out for:
    1-coding files such as c++,c java, python, etc with same names
    2- Folders with same name
    
    If you come across case 1, simply highlight them in yellow and point it out to the user
    If you come across case 2, you will call the documentation_agent in loop_agents and compare the two files by:
    
    a)Highlighting every method with the same signature as red
    b)Highlighting every variable that they share as yellow 
    
    You will then ask the user which file they want to keep between the first and the second by typing 1 or 2
    You will select the one they chose to keep in the project and delete the other.
    
    Do this until there are no more coding files with the same name
""",
    description="Compares two different coding projects that want to be merged.",
    # No tools needed for merging
    # No output_key needed here, as its direct response is the final output of the sequence
)

# --- 4. Create the SequentialAgent (Orchestrates the overall flow) ---
# This is the main agent that will be run. It first executes the ParallelAgent
# to populate the state, and then executes the MergerAgent to produce the final output.
sequential_pipeline_agent = SequentialAgent(
    name="ResearchAndSynthesisPipeline",
    # Run parallel research first, then merge
    sub_agents=[parallel_research_agent, merger_agent],
    description="Coordinates parallel research and synthesizes the results."
)

root_agent = sequential_pipeline_agent
