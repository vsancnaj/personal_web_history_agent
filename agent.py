# src/agent.py

import os
import numpy as np
np.float_ = np.float64
from dotenv import load_dotenv
from typing import List, Any, Optional
import datetime
from urllib.parse import urlparse
from pydantic import BaseModel, Field
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.tools import tool
from langchain_core.messages import HumanMessage
from langchain.agents import create_agent # The main agent builder
from langchain.agents.structured_output import ToolStrategy # Strategy for Pydantic output
from langchain_core.messages import ToolMessage
from langgraph.checkpoint.memory import InMemorySaver # Persistent memory

load_dotenv() 

# --- CONFIGURATION ---
PERSIST_DIRECTORY = "./data/chroma_db"
# PERSIST_DIRECTORY = "./data/chroma_db_full"
COLLECTION_NAME = "user-history-data"
PROFILE_FILENAME = "data/user_profile.txt" 

# Check for API Key
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY environment variable not set. Please check your .env file.")

llm = ChatOpenAI(model="gpt-4o", temperature=0)

# --- VECTOR STORE ---
# NOTE: This assumes you have already run your scraper and indexed your data.
try:
    embeddings = OpenAIEmbeddings() 
    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=PERSIST_DIRECTORY
    )
    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 8}
    )
except Exception as e:
    print(f"Warning: Could not initialize ChromaDB. Run data indexing steps first. Error: {e}")



# --- STRUCTURED RESPONSE ---
class HistoryResponse(BaseModel):
    """Structured response from history agent."""
    answer: str = Field(description="Final comprehensive answer based on retrieved context.")


# --- PROFILE AND HELPERS ---
def load_profile(filename: str = PROFILE_FILENAME) -> str:
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "No user profile available."

USER_PROFILE = load_profile()

def get_domain(url: str) -> str:
    try:
        return urlparse(url).netloc
    except:
        return url

def format_docs(docs: List[Any]) -> tuple[str, List[str]]:
    """Include DATES prominently in context for LLM temporal reasoning."""
    formatted_content = []
    unique_domains = set()
    
    for i, doc in enumerate(docs, 1):
        # Handle dummy data case where doc is a dict, or real data case where doc is a Document
        if isinstance(doc, dict):
            # Handle simulated data
            title = doc.get('metadata', {}).get('title', f'Document {i}')
            source_url = doc.get('metadata', {}).get('source', 'No Source')
            date = doc.get('metadata', {}).get('date', 'No date available')
            content = doc.get('page_content', '')
        else:
            # Handle real langchain Document objects
            title = doc.metadata.get('title', f'Document {i}')
            source_url = doc.metadata.get('source', 'No Source')
            date = doc.metadata.get('date', 'No date available')
            content = doc.page_content
        
        domain = get_domain(source_url)
        if domain and domain != 'No Source':
            unique_domains.add(domain)

        formatted_content.append(
            f"""DOCUMENT {i} (DATE: {date})
                TITLE: {title}
                SOURCE DOMAIN: {domain}
                CONTENT: {content}"""
        )
    
    context = "\n\n---\n\n".join(formatted_content)
    return (
        f"""RETRIEVED DOCUMENTS (sorted by relevance):
{context}

DOMAINS FOUND: {', '.join(unique_domains)}""",
        list(unique_domains)
    )

# --- TOOLS ---
@tool
def search_history(query: str) -> str:
    """Comprehensive search of user's web browsing history INCLUDING DATES."""
    relevant_docs = retriever.invoke(query)
    
    if not relevant_docs:
        return "No relevant browsing history found."
    
    formatted_context, _ = format_docs(relevant_docs)
    return formatted_context

@tool
def get_links(query: str) -> str:
    """
    Extract source URLs/domains from browsing history. 
    Use ONLY when user explicitly asks for "links", "sources", "domains", "websites".
    """
    relevant_docs = retriever.invoke(query)
    
    if not relevant_docs:
        return "No source links found for this query."
    
    links_info = []
    seen_domains = set()
    
    for doc in relevant_docs:
        # Handle dict or Document type for metadata access
        metadata = doc.metadata if not isinstance(doc, dict) else doc.get('metadata', {})
        
        source_url = metadata.get('source', 'No Source')
        domain = get_domain(source_url)
        
        if source_url != 'No Source' and domain not in seen_domains:
            links_info.append({
                'url': source_url,
                'domain': domain,
                'title': metadata.get('title', 'No Title'),
                'date': metadata.get('date', 'No date')
            })
            seen_domains.add(domain)
    
    if not links_info:
        return "No unique source links found."
    
    links_text = "\n".join([
        f"• {item['title']} ({item['date']}): {item['url']} [{item['domain']}]"
        for item in links_info
    ])
    
    return f"FOUND {len(links_info)} UNIQUE SOURCE LINKS:\n{links_text}"

TOOLS = [search_history, get_links]

# --- SYSTEM PROMPT ---
LLM_PROMPT = f"""
You analyze Valentina's web browsing history, and provide users with answer about it.
Basic context about Valentina: {USER_PROFILE}

RULES:
1. ALWAYS call 'search_history' FIRST
2. Examine document dates ONLY for temporal questions ("latest", "when", "recent"), BUT do not specify the exact date (only month and year). 
3. Answer using HistoryResponse schema
4. ONLY call 'get_links' if user wants to find out more about the source of the web search.
5. DO NOT hallucinate at all, especially if you cannot find context.
6. DO NOT provide any personal information, be as general as possible, for instance, avoid being as specific about job search, companies or names of people.
7. SUMMARIZE briefly what you find, be as general as possible to protect privacy.

EXAMPLE TEMPORAL REASONING:
DOC 1 (DATE: 2024-05-15): Niacinamide Serum
DOC 2 (DATE: 2024-11-20): Air purifier filter
Q: "Latest amazon search?" → Answer: "The most recent amazon search was in November for air purifier filters."""

# --- AGENT CREATION & INVOKE ---
checkpointer = InMemorySaver()
agent = create_agent(
    model=llm,
    tools=TOOLS, 
    system_prompt=LLM_PROMPT,
    response_format=ToolStrategy(HistoryResponse),
    checkpointer=checkpointer
)

def history_qa_agent_invoke(question: str, thread_id: str) -> HistoryResponse:
    state = {"messages": [HumanMessage(content=question)]}

    while True:
        result = agent.invoke(state, config={"configurable": {"thread_id": thread_id}})
        msg = result["messages"][-1]

        # 1. If LLM wants to call a tool
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            tool_call = msg.tool_calls[0]
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_id = tool_call["id"]

            # 2. Execute the tool
            if tool_name == "search_history":
                tool_result = search_history.invoke(tool_args)
            elif tool_name == "get_links":
                tool_result = get_links.invoke(tool_args)
            else:
                tool_result = "Unknown tool"

            state["messages"].append(
                ToolMessage(
                    content=tool_result,
                    tool_call_id=tool_id,
                )
            )
            continue

        # 4. Final output
        return result["structured_response"]


if __name__ == "__main__":
    TEST_THREAD_ID = "test-session-001"
    
    print("-" * 60)
    q1 = "What was the most recent technical search I performed?"
    print(f"Q: {q1}")
    r1 = history_qa_agent_invoke(q1, TEST_THREAD_ID)
    
    print(f"\nAI Answer (search_history called):\n{r1.answer[:150]}...")

    
    q2 = "Can you give me the sources or domains for my job searches?"
    print(f"Q: {q2}")
    r2 = history_qa_agent_invoke(q2, TEST_THREAD_ID)
    
    print(f"\nAI Answer (get_links called):\n{r2.answer[:150]}...")
    
    q3 = "Did I read about RAG patterns after that job search?"
    print(f"Q: {q3}")
    r3 = history_qa_agent_invoke(q3, TEST_THREAD_ID)
    
    print(f"\nAI Answer (Uses search_history context):\n{r3.answer[:150]}...")
