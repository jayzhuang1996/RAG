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
        model="moonshot-v1-128k",
        api_key=os.environ.get("MOONSHOT_API_KEY"),
        base_url="https://api.moonshot.ai/v1",
        temperature=temperature
    )

def researcher_node(state: AgentState):
    print("🧠 [Researcher Agent] Extracting verified facts from transcripts and graph...")
    llm = get_moonshot_llm(temperature=0.1)
    prompt = f"""You are the Lead Researcher. Your job is to extract all the hard facts and summarize what the context says about the query. Be extremely objective. Do NOT try to form conclusions or opinions. Just extract and synthesize the facts found in the provided sources.
    
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
    prompt = f"""You are a brilliant Analyst for a top-tier intelligence firm. Your job is to read the Researcher's summary and identify the "So What?". 
    Why does this matter? What are the underlying trends, contradictions, missing links, or hidden insights? 
    Don't just restate the facts; tell me what they MEAN in the context of the query.

    Query: {state['query']}
    
    Researcher's Facts:
    {state['research_summary']}
    
    Network Graph Context:
    {state['graph_text']}
    """
    response = llm.invoke([HumanMessage(content=prompt)])
    return {"analyst_insights": response.content}

def writer_node(state: AgentState):
    print("🧠 [Writer Agent] Drafting premium newsletter-style synthesis...")
    llm = get_moonshot_llm(temperature=0.5)
    
    prompt = f"""You are an elite Tech Writer (like the Pragmatic Engineer or a McKinsey partner). 
    Your job is to take the raw facts and the analyst's insights, and write a completely seamless, premium, authoritative response to the user's query.
    
    RULES:
    1. DO NOT sound like an AI. Never use phrases like "In conclusion", "It's important to note", or "Here are the facts".
    2. Write using clean Markdown formatting (bolding key terms, using bullet points if necessary).
    3. Be highly insightful, punchy, and confident.
    4. You MUST cite your sources using [Source N] exactly where appropriate.
    
    User Query: {state['query']}
    
    --- Facts (From Researcher) ---
    {state['research_summary']}
    
    --- Synthesis & Meaning (From Analyst) ---
    {state['analyst_insights']}
    
    Write the final cohesive answer:"""
    
    # We will use streaming in src/query.py directly if needed, but for the graph, we invoke it.
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
    
    # Run the graph
    print("\n" + "="*60 + "\n[INITIATING LANGGRAPH SYNTHESIS PIPELINE]\n" + "="*60)
    final_state = synthesis_graph.invoke(initial_state)
    print("="*60 + "\n")
    
    return final_state['final_answer']
