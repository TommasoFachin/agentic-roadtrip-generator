from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIResponsesModel
import os
from dotenv import load_dotenv

load_dotenv()

llm = OpenAIResponsesModel(
    model_name=os.getenv("OPENAI_MODEL")
)

agent = Agent(
    model=llm,
    instructions="Rispondi sempre in italiano in modo chiaro e conciso."
)

result = agent.run_sync("Ciao! Come stai?")

print(result.output)
