from typing import TypedDict, Callable, Dict
from langgraph.graph import StateGraph, START, END

class AgentState(TypedDict):
    is_con1 : bool
    is_con2 : bool

# ---------- Load your JSON ----------
config_json = {
    "nodes": [
        { "id": "node1", "type": "function" },
        { "id": "node2", "type": "function" },
        { "id": "node3", "type": "function" },
        { "id": "node4", "type": "function" },
        { "id": "_end_", "type": "end" }
    ],
    "edges": [
        { "from": "node1", "to": "node3", "condition": "yes" },
        { "from": "node1", "to": "node2", "condition": "no" },
        { "from": "node2", "to": "node4", "condition": "yes" },
        { "from": "node2", "to": "_end_", "condition": "no" },
        { "from": "node3", "to": "_end_", "condition": None },
        { "from": "node4", "to": "_end_", "condition": None }
    ],
    "start": "node1",
    "end": "_end_"
}

def node1(state:AgentState)->AgentState:
    print("node1")
    return state

def node2(state:AgentState)->AgentState:
    print("node2")
    return state

def node3(state:AgentState)->AgentState:
    print("node3")
    return state

def node4(state:AgentState)->AgentState:
    print("node4")
    return state

workflow = StateGraph(AgentState)

# Map node ids from the JSON to actual callables defined above
node_registry: Dict[str, Callable[[AgentState], AgentState]] = {
    "node1": node1,
    "node2": node2,
    "node3": node3,
    "node4": node4,
}

# Add function nodes (skip explicit end pseudo-node)
if "nodes" in config_json:
    for node in config_json["nodes"]:
        node_id = node.get("id")
        node_type = node.get("type")
        if not node_id:
            continue
        if node_type == "end" or node_id == "_end_":
            continue
        func = node_registry.get(node_id)
        if callable(func):
            workflow.add_node(node_id, func)
        else:
            raise ValueError(f"No callable found for node id '{node_id}'. Registered: {list(node_registry.keys())}")

# Connect START to configured start node
start_node = config_json.get("start")
if start_node:
    workflow.add_edge(START, start_node)

# Define simple routers for conditional edges using AgentState flags.
def route_from_node1(state: AgentState) -> str:
    return "yes" if state.get("is_con1", False) else "no"

def route_from_node2(state: AgentState) -> str:
    return "yes" if state.get("is_con2", False) else "no"

# Add edges from config
edges = config_json.get("edges", [])
if edges:
    # Group edges by source to determine conditional routing
    edges_by_from: Dict[str, list] = {}
    for e in edges:
        edges_by_from.setdefault(e.get("from"), []).append(e)

    for source, group in edges_by_from.items():
        # Determine if conditional
        has_conditions = any(e.get("condition") is not None for e in group)
        if has_conditions:
            cond_mapping: Dict[str, str] = {}
            for e in group:
                cond = e.get("condition")
                target = e.get("to")
                if target == "_end_":
                    target = END
                if cond is not None:
                    cond_mapping[str(cond)] = target  # type: ignore[assignment]

            if source == "node1":
                workflow.add_conditional_edges(source, route_from_node1, cond_mapping)
            elif source == "node2":
                workflow.add_conditional_edges(source, route_from_node2, cond_mapping)
            else:
                # Default router mirrors node1's flag
                def default_router(state: AgentState) -> str:
                    return "yes" if state.get("is_con1", False) else "no"

                workflow.add_conditional_edges(source, default_router, cond_mapping)
        else:
            # Unconditional edges
            for e in group:
                target = e.get("to")
                workflow.add_edge(source, END if target == "_end_" else target)

agent = workflow.compile()

png = agent.get_graph().draw_mermaid_png()
with open("graph.png", "wb") as f:
    f.write(png)

# Open it on Windows
import os, pathlib, sys, webbrowser
path = str(pathlib.Path("graph.png").resolve())
if sys.platform.startswith("win"):
    os.startfile(path)  # opens with default app
else:
    webbrowser.open(path)







