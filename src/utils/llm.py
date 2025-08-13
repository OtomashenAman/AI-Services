from langchain_openai import ChatOpenAI

from src.services.agents.settings import Model_Name,open_api_key


# -------------------
#  LLM
# -------------------

class llm:
    def __init__(self) -> None:
        self.llm = ChatOpenAI(model=Model_Name, api_key=open_api_key)