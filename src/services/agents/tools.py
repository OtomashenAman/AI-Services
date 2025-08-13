from langchain.tools import tool
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate

from src.services.agents.settings import tavily_api_key
from src.utils.llm import llm
from src.services.agents.type import SupportTicket


# -------------------
# Tools
# -------------------
@tool
def websearch(query: str):
    """
    Search for answers using Tavily web search.
    """
    from langchain_tavily import TavilySearch
    tavily_tool = TavilySearch(max_results=3, topic="general", include_answer="basic", tavily_api_key=tavily_api_key)
    output = tavily_tool.invoke({"query": query})
    return output


@tool
def redirect_services(user_query: str) -> SupportTicket:
    """
    If the query is about creating a support ticket, return a description and the support link.
    Otherwise, leave both fields empty.
    """

    navigation_links = {
        "support": "https://dev.zorbit.ai/support"
    }

    parser = PydanticOutputParser(pydantic_object=SupportTicket)

    prompt = PromptTemplate(
        template=(
            "You are an assistant that helps create support tickets.\n"
            "Given the user query below, determine if a support ticket is needed.\n"
            "If yes:\n"
            " - Provide a clear and detailed description of the issue.\n"
            f" - Use this exact link: {navigation_links['support']}\n"
            "If not related to support, leave description and link empty.\n\n"
            "{format_instructions}\n\n"
            "User query: {query}"
        ),
        input_variables=["query"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    _input = prompt.format(query=user_query)

    result = llm().llm.invoke(_input)

    return parser.parse(result.content)