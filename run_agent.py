from agent.agent import root_agent  # replace 'your_agent_file' with your actual filename
from google.adk.runners import InMemoryRunner

# Create a runner with your root_agent
runner = InMemoryRunner(root_agent)

# Run the agent
runner.run()
