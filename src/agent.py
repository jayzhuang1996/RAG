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

def researcher_node(state: AgentState):
    print("🧠 [Researcher Agent] Extracting verified facts from transcripts and graph...")
    llm = get_moonshot_llm(temperature=0.1)
    prompt = f"""You are a meticulous Data Extraction Engine. Your only job is to sift through the provided raw transcript chunks and graph relationships and extract EVERY concrete fact, quote, and data point related to the user's query.
    
    RULES:
    1. Do not hallucinate or infer.
    2. Group facts logically.
    3. Retain exact quotes if they represent strong opinions or claims.
    4. Note contradictions if different sources say different things.
    
    Query: {state['query']}
    
    Podcast Transcripts:
    {state['context_text']}
    
    Verified Network Graph:
    {state['graph_text']}
    """
    response = llm.invoke([HumanMessage(content=prompt)])
    return {"research_summary": response.content}

def analyst_node(state: AgentState):
    print("🧠 [Analyst Agent] Identifying trends, contradictions, and actionable insights...")
    llm = get_moonshot_llm(temperature=0.4)
    prompt = f"""You are a brilliant Executive Strategist and Pattern Recognizer (running at Claude Opus 4.7 level intelligence). 
    Your goal is to transform the underlying facts into a high-level strategic briefing. You do not just summarize; you ANALYZE.
    
    Analyze the following facts against the user's query and generate:
    1. The core narrative / overarching truth.
    2. Hidden trends or subtle implications the raw data implies but doesn't state outright.
    3. Contradictions or open questions in the data.
    4. Strategic implications (Why does this matter to a business leader or investor?)

    Query: {state['query']}
    
    Extracted Facts:
    {state['research_summary']}
    """
    response = llm.invoke([HumanMessage(content=prompt)])
    return {"analyst_insights": response.content}

def writer_node(state: AgentState):
    print("🧠 [Writer Agent] Drafting premium strategic advisor synthesis...")
    llm = get_moonshot_llm(temperature=0.5)
    
    prompt = f"""You are an elite Executive Advisor (operating at the intelligence level of an Opus 4.7 master analyst).
    Your task is to synthesize the foundational facts and the strategic analysis into a final, authoritative briefing for the user.
    
    RULES & TONE:
    1. Write with extreme clarity, confidence, and punchiness. (e.g., McKinsey partner or top-tier tech newsletter).
    2. NO WEASEL WORDS ("It is important to note", "In conclusion", "As an AI"). Start directly with the thesis.
    3. Structure the response beautifully using Markdown:
       - Start with a bold **Executive Summary** (1-2 sentences).
       - Provide the **Core Analysis** (synthesize the facts smoothly, no robotic lists unless appropriate).
       - Include a section for **Strategic Implications** or **Actionable Next Steps**.
    4. You MUST cite your sources seamlessly. When you state a fact, append [Source N] immediately.
    
    User Query: {state['query']}
    
    --- Foundational Data (Facts) ---
    {state['research_summary']}
    
    --- Strategic Deep-Dive (Analysis) ---
    {state['analyst_insights']}
    
    Now, write the final Executive Briefing:"""
    
    response = llm.invoke([HumanMessage(content=prompt)])
    return {"final_answer": response.content}

# Build the Graph
workflow = StateGraph(AgentState)

workflow.add_node("researcher", researcher_node)
workflow.add_node("analyst", analyst_node)
workflow.add_node("writer", writer_node)

workflow.add_edge(START, "researcher")
workflow.add_edge("researcher", "analyst")
workflow.add_edge("analyst", "writer")
workflow.add_edge("writer", END)

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
