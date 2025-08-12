# check user query is QA or naviagte/redirect page using llm
# if the Query is QA then invoke currect developed /rag endpoind code, if QA answer fetch and give it to llm if it not related to user query then search in websearch using tavily
# if naviagte/redirect page then just return the dynamic links from llm it self

import sys
import os
from langgraph.graph import StateGraph, START, END


from src.services.agents.type import Agentstate
from src.services.agents.nodes import (
                                        call_rag,
                                        is_Navig_query,
                                        call_websearch,
                                        call_redirect,
                                        user_realted_answer
                                       )


# -------------------
# Build Graph
# -------------------

graph_builder = StateGraph(Agentstate)
graph_builder.add_node("is_Navig_query",is_Navig_query)
graph_builder.add_node("user_realted_answer",user_realted_answer)
graph_builder.add_node("call_websearch",call_websearch)
graph_builder.add_node("call_rag",call_rag)
graph_builder.add_node("call_redirect",call_redirect)

# Flow
graph_builder.add_edge(START, "is_Navig_query")
graph_builder.add_conditional_edges(
    "is_Navig_query",
    lambda s: "call_redirect" if s["navigate_realted"] else "call_rag",
    {"call_rag": "call_rag", "call_redirect": "call_redirect"}
)

graph_builder.add_edge("call_rag","user_realted_answer")
graph_builder.add_conditional_edges(
    "user_realted_answer",
    lambda s: "call_websearch" if not s['user_realted_answer'] else END,
    {'call_websearch':'call_websearch',END:END}

)
graph_builder.add_edge("call_redirect",END)
graph_builder.add_edge("call_websearch",END)

graph = graph_builder.compile()



