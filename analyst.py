import os
import re
from typing import TypedDict, Literal
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langchain_anthropic import ChatAnthropic
from youtube_transcript_api import YouTubeTranscriptApi

load_dotenv()

# 1. State Definition
class AgentState(TypedDict):
    input: str
    logic_analysis: str
    rhetoric_analysis: str

# 2. The Extractor Module (NEW)
from langchain_community.document_loaders import YoutubeLoader

def get_youtube_transcript(url: str) -> str:
    print("\n--- RIPPING TRANSCRIPT FROM YOUTUBE ---")
    print(f">> Target Locked: [{url}]")
    
    try:
        # LangChain's native loader handles the extraction flawlessly
        loader = YoutubeLoader.from_youtube_url(url, add_video_info=False)
        docs = loader.load()
        
        if not docs:
            return "ERROR: No transcript found. Ensure closed captions are enabled."
            
        transcript_text = docs[0].page_content
        print(f">> Successfully ripped {len(transcript_text)} characters of text.\n")
        return transcript_text
        
    except Exception as e:
        return f"ERROR fetching transcript: {str(e)}\nMake sure it is a valid YouTube link."

# 3. Node 1: The Logician
def analyze_logic(state: AgentState):
    print("--- RUNNING LOGIC NODE ---")
    llm = ChatAnthropic(model="claude-sonnet-4-6", temperature=0)
    
    prompt = f"""
    You are an exacting Logician. Analyze the following transcript for logical fallacies.
    Do not be polite; be brutally honest and precise. Ignore minor grammatical errors inherent to spoken text.
    
    Transcript: {state['input']}
    """
    response = llm.invoke(prompt)
    return {"logic_analysis": response.content}

# 4. Node 2: The Rhetorician
def analyze_rhetoric(state: AgentState):
    print("--- RUNNING RHETORIC NODE (INTENT ANALYSIS) ---")
    llm = ChatAnthropic(model="claude-sonnet-4-6", temperature=0)
    
    prompt = f"""
    You are a master Rhetorician and Behavioral Analyst. 
    Review the transcript and the Logician's breakdown. 
    Determine the INTENT of the speaker. Are they using malicious manipulation (grifting, scamming), or are they just operating out of ignorance? 
    
    Transcript: {state['input']}
    Logic Breakdown: {state['logic_analysis']}
    """
    response = llm.invoke(prompt)
    return {"rhetoric_analysis": response.content}

# 5. The Router
def route_logic(state: AgentState) -> Literal["rhetoric_node", "__end__"]:
    print("--- ROUTER EVALUATING LOGIC REPORT ---")
    analysis = state["logic_analysis"].lower()
    
    if "fallacy" in analysis or "fallacies" in analysis:
        print(">> Fallacies detected. Routing to Rhetorician.")
        return "rhetoric_node"
    else:
        print(">> Logic is clean. Ending process.")
        return "__end__"

# 6. Graph Assembly
print("--- ASSEMBLING PHASE 3 GRAPH ---")
workflow = StateGraph(AgentState)

workflow.add_node("logic_node", analyze_logic)
workflow.add_node("rhetoric_node", analyze_rhetoric)

workflow.add_edge(START, "logic_node")
workflow.add_conditional_edges("logic_node", route_logic, {"rhetoric_node": "rhetoric_node", "__end__": END})
workflow.add_edge("rhetoric_node", END)

app = workflow.compile()

# 7. Execution (Now Interactive)
if __name__ == "__main__":
    print("\n========== IRON TRIVIUM TERMINAL ==========")
    
    # We now prompt the user for a live target
    target_url = input("Enter Target YouTube URL: ").strip()
    
    raw_transcript = get_youtube_transcript(target_url)
    
    if raw_transcript.startswith("ERROR"):
        print(raw_transcript)
    else:
        print("--- INITIATING ANALYSIS ENGINE ---")
        # Pass the massive ripped string into the state
        result = app.invoke({"input": raw_transcript})
        
        print("\n========== FINAL IRON TRIVIUM REPORT ==========")
        print("\n[LOGIC ANALYSIS]")
        print(result.get('logic_analysis', 'No logic data.'))
        
        if 'rhetoric_analysis' in result:
            print("\n[RHETORIC & INTENT ANALYSIS]")
            print(result['rhetoric_analysis'])