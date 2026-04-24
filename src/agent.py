import os
from typing import TypedDict, List
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END

# Define the State passed between agents
class AgentState(TypedDict):
    query: str
    context_text: str
    graph_text: str
    research_summary: str
    analyst_insights: str
    final_answer: str

def get_moonshot_llm(temperature=0.3):
    return ChatOpenAI(
        model="moonshot-v1-8k",
        api_key=os.environ.get("MOONSHOT_API_KEY"),
        base_url="https://api.moonshot.ai/v1",
        temperature=temperature
    )

def synthesizer_node(state: AgentState):
    print("🧠 [Synthesizer Agent] Extracting facts, analyzing trends, and drafting final briefing...")
    llm = get_moonshot_llm(temperature=0.3)
    
    prompt = f"""You are an elite Executive Advisor & Data Extraction Engine.
    Your task is to review raw podcast transcripts and relationship graphs, extract verified facts, and instantly synthesize them into a strategic executive briefing.
    
    RULES & TONE:
    1. Write with extreme clarity, confidence, and punchiness (e.g., top-tier tech newsletter).
    2. NO WEASEL WORDS ("It is important to note", "In conclusion", "As an AI").
    3. Structure beautifully using Markdown:
       - **Executive Summary** (1-2 sentences).
       - **Core Analysis** (synthesize facts smoothly, note contradictions).
       - **Strategic Implications** (Why it matters).
    4. You MUST cite sources seamlessly. Append [Source N] to facts.
    5. Do not hallucinate. Use ONLY the provided context.
    
    User Query: {state['query']}
    
    --- Foundational Data (Podcast Transcripts) ---
    {state['context_text']}
    
    --- Verified Network Graph ---
    {state['graph_text']}
    
    Now, write the final Executive Briefing:"""
    
    response = llm.invoke([HumanMessage(content=prompt)])
    # Map the output to final_answer (and pass empty strings to others if needed)
    return {"final_answer": response.content}

# Build the Graph
workflow = StateGraph(AgentState)

workflow.add_node("synthesizer", synthesizer_node)

workflow.add_edge(START, "synthesizer")
workflow.add_edge("synthesizer", END)

# Compile into a runnable
synthesis_graph = workflow.compile()

def run_synthesis_pipeline(query: str, context_text: str, graph_text: str) -> str:
    """
    Entry point to run the multi-agent pipeline.
    """
    initial_state = {
        "query": query,
        "context_text": context_text,
        "graph_text": graph_text,
        "research_summary": "",
        "analyst_insights": "",
        "final_answer": ""
    }
    
    print("\n" + "="*60 + "\n[INITIATING LANGGRAPH SYNTHESIS PIPELINE]\n" + "="*60)
    final_state = synthesis_graph.invoke(initial_state)
    print("="*60 + "\n")
    
    return final_state['final_answer']
