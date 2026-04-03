import os
from typing import TypedDict, Literal
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langchain_anthropic import ChatAnthropic

load_dotenv()

# 1. Expand the State (The Clipboard now holds more data)
class AgentState(TypedDict):
    input: str
    logic_analysis: str
    rhetoric_analysis: str

# 2. Node 1: The Logician
def analyze_logic(state: AgentState):
    print("--- RUNNING LOGIC NODE ---")
    llm = ChatAnthropic(model="claude-sonnet-4-6", temperature=0)
    
    prompt = f"""
    You are an exacting Logician. Analyze the following text for logical fallacies.
    Do not be polite; be brutally honest and precise.
    
    Text: {state['input']}
    """
    response = llm.invoke(prompt)
    return {"logic_analysis": response.content}

# 3. Node 2: The Rhetorician (New!)
def analyze_rhetoric(state: AgentState):
    print("--- RUNNING RHETORIC NODE (INTENT ANALYSIS) ---")
    llm = ChatAnthropic(model="claude-sonnet-4-6", temperature=0)
    
    prompt = f"""
    You are a master Rhetorician and Behavioral Analyst. 
    Review the original text and the Logician's breakdown. 
    Determine the INTENT of the speaker. Are they using malicious manipulation (grifting, scamming), or are they just operating out of ignorance/panic? 
    
    Original Text: {state['input']}
    Logic Breakdown: {state['logic_analysis']}
    """
    response = llm.invoke(prompt)
    return {"rhetoric_analysis": response.content}

# 4. The Router (The Control Flow)
def route_logic(state: AgentState) -> Literal["rhetoric_node", "__end__"]:
    print("--- ROUTER EVALUATING LOGIC REPORT ---")
    analysis = state["logic_analysis"].lower()
    
    # If the Logician found fallacies, send it to the Rhetorician.
    if "fallacy" in analysis or "fallacies" in analysis:
        print(">> Fallacies detected. Routing to Rhetorician.")
        return "rhetoric_node"
    else:
        print(">> Logic is clean. Ending process.")
        return "__end__"

# 5. Assemble the Multi-Node Graph
print("--- ASSEMBLING PHASE 2 GRAPH ---")
workflow = StateGraph(AgentState)

# Add both nodes to the board
workflow.add_node("logic_node", analyze_logic)
workflow.add_node("rhetoric_node", analyze_rhetoric)

# Wire it up with the Conditional Router
workflow.add_edge(START, "logic_node")
workflow.add_conditional_edges(
    "logic_node",
    route_logic,
    {
        "rhetoric_node": "rhetoric_node",
        "__end__": END
    }
)
workflow.add_edge("rhetoric_node", END)

app = workflow.compile()

# 6. Execution
if __name__ == "__main__":
    print("\n--- INITIATING IRON TRIVIUM ANALYST (PHASE 2) ---\n")
    test_input = "Everyone on YouTube says this alt-coin is going to the moon, so I should invest my son's RDSP into it immediately before I miss out."
    print(f"INPUT: {test_input}\n")
    
    result = app.invoke({"input": test_input})
    
    print("\n========== FINAL IRON TRIVIUM REPORT ==========")
    print("\n[LOGIC ANALYSIS]")
    print(result.get('logic_analysis', 'No logic data.'))
    
    if 'rhetoric_analysis' in result:
        print("\n[RHETORIC & INTENT ANALYSIS]")
        print(result['rhetoric_analysis'])