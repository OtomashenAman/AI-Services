
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
import logging

from src.services.rag.rag_services import QA_RAGService
from src.services.rag.models import RAGRequestModel,RAGType
from src.services.agents.type import AgentState,NavigationSupportCheck
from src.utils.llm import llm
from src.services.agents.tools import websearch,redirect_services

logger = logging.getLogger(__name__)

# -------------------
#  Nodes
# -------------------

def check_navigation_query(state: AgentState) -> AgentState:
    """
    Check if the user query is related to navigation OR creating a support ticket.
    Sets state['navigate_realted'] to True if either is true.
    """

    parser = PydanticOutputParser(pydantic_object=NavigationSupportCheck)

    prompt = PromptTemplate(
        template = """
        You are a strict classifier that determines whether a user query is about:
        1. Navigating or redirecting within a web application
        2. Creating a support ticket

        Instructions:
        - Return ONLY JSON according to the provided schema.
        - Return `is_support_ticket = true` if the user is requesting, asking, or implying creation of a ticket, regardless of reason (e.g., permission issues, payment, account problems, etc.).
        - Return `is_navigation = true` if the user is asking to open, go to, view, or navigate to a page, section, or feature.

        Navigation examples:
        - "Open my profile"
        - "Go to settings"
        - "Take me to the dashboard"
        - "Where can I see reports?"

        Support ticket examples:
        - "I need to create a support ticket for my payment issue"
        - "Please log a ticket for account unlocking"
        - "Create a ticket for my manager permission issue"
        - "Raise a ticket to fix access problem"

        Not navigation or support ticket:
        - "How do I reset my password?"
        - "What is my current account balance?"
        - "Tell me about leave policies"

        {format_instructions}

        User query: {query}
        """,
        input_variables=["query"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    
    logger.debug(f"before check_navigation_query state --> {state}")
    # Format and send prompt to LLM
    _input = prompt.format(query=state["user_query"])
    result = llm().llm.invoke(_input)

    # Parse into Pydantic model
    NavigationCheck = parser.parse(result.content)

    # Keep same variable names in state
    state["navigate_realted"] = NavigationCheck.is_navigation or NavigationCheck.is_support_ticket
    logger.debug(f"after check_navigation_query state --> {state}")
    return state

def fetch_user_related_answer(state:AgentState)-> AgentState:
    """
    Check if the answer retrieved from the database is relevant to the user's query.
    """
    prompt = f"Is the following answer related to the user query? Answer only 'True' or 'False'.\nNodes: {state['user_answer']}\nUser Query: {state['user_query']}"
    result = llm().llm.invoke(prompt)
    answer = result.content.strip().lower()
    state["user_realted_answer"] = answer == "true"
    return state

def perform_web_search(state: AgentState) -> AgentState:
    """
    Call web search.
    """
    web_result = websearch.run(state["user_query"])
    state["user_answer"]=web_result['answer']
    return state

def run_rag_pipeline(state: AgentState) -> AgentState:
    """
    Calls the RAG service internally without HTTP.
    """
    # Create mock request object (since your service expects FastAPI's Request)
    class MockRequest:
        def __init__(self):
            self.state = type("MockState", (), {})()
            self.state.user_type = state.get("user_type",None)

    mock_request = MockRequest()

    # Prepare the request model
    rag_request = RAGRequestModel(
        queries={"1": state["user_query"]},
        rag_type=RAGType.QUESTION_ANSWER,
        user_type=state.get("user_type",None)
    )
    

    try:
        rag_service = QA_RAGService(rag_type=rag_request.rag_type, request=mock_request)
        answer = rag_service.get_response(state["user_query"])
        state["user_answer"] = answer
    except Exception as e:
        state["user_answer"] = f"Error calling RAG service: {e}"

    return state

def execute_redirect(state: AgentState)->AgentState:
    """
    calls the redirect endpoint
    """
    response = redirect_services.run(state["user_query"])
    state['navigation_answer'] = response 
    return state

def check_hr_query(state: AgentState) -> AgentState:
    """
    Checks if the user query is either:
    1. HR-related (hiring, recruiting, onboarding, compliance, payroll, etc.)
    2. Platform-related administrative actions (e.g., creating support tickets, account changes)
    
    Sets 'is_hr_query' in the state accordingly.
    """
    prompt = (
        "You are a strict boolean classifier for a SaaS platform that helps companies recruit employees "
        "from other countries, even if they don't have a local company there. "
        "Given the following user query, return ONLY 'true' or 'false'.\n\n"
        "Return 'true' if the query is:\n"
        "- HR-related (e.g., hiring, recruiting, onboarding, payroll, compliance, employee management, etc.)\n"
        "- Platform-related administrative actions (e.g., creating a support ticket, account unlock request, system access issues)\n"
        "Return 'false' if it is not related to either of the above.\n\n"
        "Examples of 'true':\n"
        "- I want to hire a developer in Germany\n"
        "- How do I process payroll for a remote employee?\n"
        "- I want to create a support ticket for my payment issue\n"
        "- Please log a ticket for manager permission issue\n"
        "Examples of 'false':\n"
        "- What's the weather in Paris?\n"
        "- Tell me a joke\n"
        "- Show me the latest sports news\n\n"
        f"User query: {state['user_query']}"
    )
    try:
        result = llm().llm.invoke(prompt, temperature=0)
        answer = result.content.strip().lower()
        state["is_hr_query"] = answer == "true"
    except Exception:
        state["is_hr_query"] = False

    return state
