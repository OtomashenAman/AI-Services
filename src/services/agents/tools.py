from langchain.tools import tool
from src.services.agents.settings import tavily_api_key
from src.utils.llm import llm


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
def redriect_services(user_query: str):
    """
    Determines the appropriate navigation link or response based on the user's query.
    If the query matches a known navigation target, returns the link.
    Otherwise, informs the user that the feature is currently being integrated.
    """
    # Define available navigation links
    navigation_links = {
        "dashboard": "https://yourapp.com/dashboard",
        "profile": "https://yourapp.com/profile",
        "settings": "https://yourapp.com/settings",
        "help": "https://yourapp.com/help",
        "reports": "https://yourapp.com/reports",
        "support": "https://dev.zorbit.ai/support"
    }

    # Construct a prompt for the LLM to decide where to navigate
    links_str = "\n".join([f"- {name.title()}: {url}" for name, url in navigation_links.items()])
    prompt = (
        f"You are an assistant that helps users navigate a web application. "
        f"Given the user query below, determine which of the following navigation links is most appropriate. "
        f"If none of the links are relevant, respond with: "
        f"'Currently, the requested link is not integrated. We are working on making it available soon.'\n\n"
        f"Available links:\n{links_str}\n\n"
        f"User query: {user_query}\n\n"
        f"Respond ONLY with the URL if a match is found, or the above professional message otherwise."
    )

    # Call the LLM to get the navigation decision
    result = llm().llm.invoke(prompt)
    answer = result.content.strip() if hasattr(result, "content") else str(result).strip()
    return {"user_answer": answer}

