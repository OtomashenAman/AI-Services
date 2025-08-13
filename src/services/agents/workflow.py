# check user query is QA or naviagte/redirect page using llm
# if the Query is QA then invoke currect developed /rag endpoind code, if QA answer fetch and give it to llm if it not related to user query then search in websearch using tavily
# if naviagte/redirect page then just return the dynamic links from llm it self

import sys
import os

# # Add the project root to Python path for imports
# project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
# sys.path.insert(0, project_root)

from langgraph.graph import StateGraph, START, END
from src.services.agents.type import UserQueryRequest
import logging

from src.services.agents.type import AgentState
from src.services.agents.nodes import (
                                        run_rag_pipeline,
                                        check_navigation_query,
                                        perform_web_search,
                                        execute_redirect,
                                        fetch_user_related_answer,
                                        check_hr_query
                                       )

logger = logging.getLogger(__name__)
# from IPython.display import Image, display
# -------------------
# Build Graph
# -------------------

def build_agent_graph():

    graph_builder = StateGraph(AgentState)

    # Node definitions
    graph_builder.add_node("check_hr_query", check_hr_query)
    graph_builder.add_node("check_navigation_query", check_navigation_query)
    graph_builder.add_node("fetch_user_related_answer", fetch_user_related_answer)
    graph_builder.add_node("perform_web_search", perform_web_search)
    graph_builder.add_node("run_rag_pipeline", run_rag_pipeline)
    graph_builder.add_node("execute_redirect", execute_redirect)

    # Flow
    graph_builder.add_edge(START,"check_hr_query")
    graph_builder.add_conditional_edges(
        "check_hr_query",
        lambda s:'check_navigation_query' if s['is_hr_query'] else "perform_web_search",
        {'check_navigation_query':'check_navigation_query','perform_web_search':'perform_web_search'}
        
        )
    graph_builder.add_conditional_edges(
        "check_navigation_query",
        lambda s: "execute_redirect" if s["navigate_realted"] else "run_rag_pipeline",
        {"run_rag_pipeline": "run_rag_pipeline", "execute_redirect": "execute_redirect"}
    )

    graph_builder.add_edge("run_rag_pipeline", "fetch_user_related_answer")
    graph_builder.add_conditional_edges(
        "fetch_user_related_answer",
        lambda s: "perform_web_search" if not s['user_realted_answer'] else END,
        {"perform_web_search": "perform_web_search", END: END}
    )

    graph_builder.add_edge("execute_redirect", END)
    graph_builder.add_edge("perform_web_search", END)

    
    agent = graph_builder.compile()
    # png_data = agent.get_graph().draw_mermaid_png()
    # # Save it locally
    # output_path = "src/services/agents/graph.png"  # You can give absolute path if needed
    # with open(output_path, "wb") as f:
    #     f.write(png_data)

    # # Optional: Display it inline as well
    # try:
    #     display(Image(output_path))
    # except Exception:
    #     pass

    # print(f"Graph image saved at: {output_path}")

    return agent






