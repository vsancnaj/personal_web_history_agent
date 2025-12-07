import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
# from langchain.chat_models import init_chat_model

load_dotenv()

PERSIST_DIRECTORY = "./data/chroma_db"
COLLECTION_NAME = "user-history-data" 

# ChatOpenAI for the LLM, lets keep it as less creative as possible
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# INITIALIZE EMBEDDINGS AND VECTOR STORE
embeddings = OpenAIEmbeddings() 

vector_store = Chroma(
    collection_name=COLLECTION_NAME,
    embedding_function=embeddings,
    persist_directory=PERSIST_DIRECTORY
)

# RETRIEVER OF DATA
retriever = vector_store.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 8}
)

# HELPER FUNCTION - include the title in the context
def format_docs(docs):
    formatted_content = []
    for doc in docs:
        title = doc.metadata.get('title', 'No Title Available')
        content = doc.page_content
        formatted_content.append(f"--- DOCUMENT TITLE: {title} ---\n{content}")
        
    return "\n\n".join(formatted_content)

# SYSTEM PROMPT
llm_template = """
## TASK
You are a helpful assistant analyzing user browsing history.
Use the following pieces of retrieved website content to answer the question.
## RULES
- If the content looks like navigation menus or footers, ignore it.
- If it is a job search website do not give specific information like names and company.
- Be general in what you find and do not give details that could be too personal, just personal enough
for others to see. 
- If you don't know the answer, just say you don't know.
- Do not hallucinate, always answer based on the context you retrieve for the user's question.
## INTERACTION FORMAT
Context:
{context}

Question:
{question}

Answer:
"""
prompt = ChatPromptTemplate.from_template(llm_template)

# BUILD THE RAG CHAIN
# Retriever -> Format Data -> Fill Prompt -> Send to LLM -> Read Output
rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

def save_profile(profile_text: str, filename: str = "data/user_profile.txt"):
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(profile_text)
        print(f"\nBasic profile information saved {filename}")
    except Exception as e:
        print(f"\nError saving the profile: {e}")


if __name__ == "__main__":
    # question = "What specific destinations did the user search?"
    question = "Summarize the user's primary interests based on all available browsing history."
    print(f"Question: {question}\n")
    
    # Run the chain
    response = rag_chain.invoke(question)
    
    print("Answer:")
    print(response)
    
    # extra step to save basic profile info that will be injected to the agent
    # save_profile(response)