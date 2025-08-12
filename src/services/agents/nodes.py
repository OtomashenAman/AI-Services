
from src.services.rag.rag_services import QA_RAGService
from src.services.rag.models import RAGRequestModel,RAGType
from src.services.agents.type import Agentstate
from src.utils.llm import llm
from src.services.agents.tools import websearch,redriect_services

# -------------------
#  Nodes
# -------------------

def is_Navig_query(state: Agentstate) -> Agentstate:
    """
    Check if the user query is related to navigation.
    """
    prompt = f"""
            You are a classifier that determines whether a user query is about **navigating or redirecting** within a web application.

            A "navigation query" means the user is trying to:
            - Open a specific page (e.g., dashboard, settings, reports)
            - Access a section of the app
            - Go to a specific feature or tool

            Examples of navigation queries:
            - "Open my profile"
            - "Go to settings"
            - "Take me to the dashboard"
            - "Where can I see reports?"

            Not navigation queries (these are Q&A or informational):
            - "How do I reset my password?"
            - "What is my current account balance?"
            - "Tell me about leave policies"

            User query: {state['user_query']}

            Answer only with **True** (if it's a navigation request) or **False** (otherwise).
            """
    result = llm().llm.invoke(prompt)
    answer = result.content.strip().lower()
    print(f"output og the is_navig_query {answer}")
    state["navigate_realted"] = answer == "true"
    return state


def user_realted_answer(state:Agentstate)-> Agentstate:
    """
    Check if the answer retrieved from the database is relevant to the user's query.
    """
    prompt = f"Is the following answer related to the user query? Answer only 'True' or 'False'.\nNodes: {state['user_answer']}\nUser Query: {state['user_query']}"
    result = llm().llm.invoke(prompt)
    answer = result.content.strip().lower()
    state["user_realted_answer"] = answer == "true"
    return state

def call_websearch(state: Agentstate) -> Agentstate:
    """
    Call web search.
    """
    web_result = websearch.run(state["user_answer"])
    state["user_answer"]=web_result['answer']
    return state



def call_rag(state: Agentstate) -> Agentstate:
    """
    Calls the RAG service internally without HTTP.
    """
    # Create mock request object (since your service expects FastAPI's Request)
    class MockRequest:
        def __init__(self):
            self.state = type("MockState", (), {})()
            self.state.user_type = "Client"

    mock_request = MockRequest()

    # Prepare the request model
    rag_request = RAGRequestModel(
        queries={"1": state["user_query"]},
        rag_type=RAGType.QUESTION_ANSWER,
        user_type="Client"
    )

    try:
        rag_service = QA_RAGService(rag_type=rag_request.rag_type, request=mock_request)
        answer = rag_service.get_response(state["user_query"])
        state["user_answer"] = answer
    except Exception as e:
        state["user_answer"] = f"Error calling RAG service: {e}"

    return state


def call_redirect(state: Agentstate)->Agentstate:
    """
    calls the redirect endpoint
    """
    response = redriect_services.run(state["user_query"])
    state.update(response)
    return state
