import os
import requests
from dotenv import load_dotenv
from langchain_community.document_loaders import WebBaseLoader 
from langchain_community.document_transformers import Html2TextTransformer
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from extract_urls import get_history_data

load_dotenv()
PERSIST_DIRECTORY = "./data/chroma_db_full"
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT_SECONDS", 15)) 
COLLECTION_NAME = "user-history-data" 

def batch_load_documents(urls, batch_size=50):
    raw_documents = []
    
    # keywords/domains to skip immediately to avoid login pages etc.
    SKIP_DOMAINS = ['login', 'account', 'mfa', 'password', 'oauth']
    # Filter out problematic URLs
    filtered_urls = [url for url in urls if not any(skip_word in url for skip_word in SKIP_DOMAINS)]
    
    
    print(f"Loading {len(filtered_urls)} URLs in batches of {batch_size}...")

    for i in range(0, len(filtered_urls), batch_size):
        batch_urls = filtered_urls[i:i + batch_size]
        try:
            # WebBaseLoader is synchronous, but we handle errors robustly
            loader = WebBaseLoader(
                web_paths=batch_urls,
                requests_kwargs={
                    "timeout": REQUEST_TIMEOUT
                }
            )
            
            batch_docs = loader.load()
            raw_documents.extend(batch_docs)
            print(f"Successfully loaded batch {i//batch_size + 1}. Total documents: {len(raw_documents)}")
            
        except Exception as e:
            # Catch exceptions from the entire batch and skip it
            print(f"⚠️ Error loading batch {i//batch_size + 1}: {e}")
            continue 
            
    return raw_documents

def process_and_index_webbase(history_data):
    if not history_data:
        print(f"No history data to process.")
        return

    valid_data = [
        item for item in history_data
        if item['url'] and (item['url'].startswith('http') or item['url'].startswith('https'))
    ]
    
    urls = [item['url'] for item in valid_data]
    url_to_meta = {item['url']: item for item in valid_data}
    
    print(f"Total valid URLs for fetching: {len(urls)}")
    
    raw_documents = batch_load_documents(urls, batch_size=50)
    
    print(f"Sucessfully loaded {len(raw_documents)} pages!")
    
    # TRANSFORM TO PLAIN TEXT
    html2text = Html2TextTransformer() 
    docs_transformed = html2text.transform_documents(raw_documents) 
    
    # METADATA ENRICHMENT
    final_documents = []
    for doc in docs_transformed:
        url = doc.metadata.get('source')
        if url in url_to_meta:
            original_meta = url_to_meta[url]
            doc.metadata['title'] = original_meta.get('title', 'No Title')
            doc.metadata['date'] = original_meta.get('date')
            final_documents.append(doc)
    
    # CHUNKING
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=200)
    splits = text_splitter.split_documents(final_documents)
    
    if not splits:
        print("No valid text found after transformation or chunking.")
        return

    print(f"Created {len(splits)} chunks.")
    
    # LOAD VECTOR STORE
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=OpenAIEmbeddings(),
        persist_directory=PERSIST_DIRECTORY,
        collection_name=COLLECTION_NAME 
    )
    
    print(f"Data successfully saved to {PERSIST_DIRECTORY}!")

if __name__ == "__main__":
    # records = get_history_data('2025-08-01', '2025-12-01')
    records = get_history_data('2025-01-01', '2025-12-01')
    if len(records) > 0:
        print(f"full ingestion of {len(records)}")
        process_and_index_webbase(records)
    else:
        print("No records found.")