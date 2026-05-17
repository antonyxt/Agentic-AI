# Test script for DirectPromptAgent class

from workflow_agents.base_agents import DirectPromptAgent # TODO: 1 - Import the DirectPromptAgent class from BaseAgents
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# TODO: 2 - Load the OpenAI API key from the environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")

prompt = "What is the Capital of France?"

# TODO: 3 - Instantiate the DirectPromptAgent as direct_agent
direct_agent = DirectPromptAgent(openai_api_key=openai_api_key)
# TODO: 4 - Use direct_agent to send the prompt defined above and store the response
direct_agent_response = direct_agent.respond(prompt=prompt)

# Print the response from the agent
print(direct_agent_response)

# TODO: 5 - Print an explanatory message describing the knowledge source used by the agent to generate the response
agentDescription = (
    "The agent answered the prompt using its internal knowledge acquired during training.\n"
    "No external knowledge sources or additional context provided in the prompt were used."
)
print(agentDescription)
