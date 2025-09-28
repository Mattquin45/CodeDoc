from agent.agent import root_agent  # replace 'your_agent_file' with your actual filename
from google.adk.runners import InMemoryRunner

runner = InMemoryRunner(root_agent)


runner.run()
