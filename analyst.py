import os
from typing import TypedDict
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END

# We import Anthropic instead of OpenAI
from langchain_anthropic import ChatAnthropic

load_dotenv()

class AgentState(TypedDict):
    input: str
    analysis: str
    fallacies_found: list[str]

def analyze_logic(state: AgentState):
    print("--- RUNNING LOGIC NODE ---")
    
    # We use Claude Sonnet, widely considered the best reasoning model
    llm = ChatAnthropic(model="claude-sonnet-4-6", temperature=0)
    
    prompt = f"""
    You are an exacting Logician. Analyze the following text for logical fallacies.
    Do not be polite; be brutally honest and precise.
    
    Text: {state['input']}
    """
    
    response = llm.invoke(prompt)
    
    return {"analysis": response.content, "fallacies_found": ["Analyzed via Claude"]}

print("--- ASSEMBLING GRAPH ---")
workflow = StateGraph(AgentState)

workflow.add_node("logic_processor", analyze_logic)
workflow.add_edge(START, "logic_processor")
workflow.add_edge("logic_processor", END)

app = workflow.compile()

if __name__ == "__main__":
    print("\n--- INITIATING IRON TRIVIUM ANALYST ---\n")
    test_input = "Everyone on YouTube says this alt-coin is going to the moon, so I should invest my son's RDSP into it immediately before I miss out."
    print(f"INPUT: {test_input}\n")
    
    result = app.invoke({"input": test_input})
    
    print("\n--- FINAL REPORT ---")
    print(result['analysis'])