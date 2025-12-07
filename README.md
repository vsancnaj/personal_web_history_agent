# My Personal Web Memory Agent

Hi! My name is Valentina and you are interacting with my Chrome web search histroy from
particular dates(so not my whole history)

A lightweight personal tool that:  
- Extracts your Chrome browsing history,  
- Scrapes the visited pages’ content,  
- Embeds and indexes them into a vector store,  
- Lets you query your past browsing via a chat UI powered by an LLM + retrieval.

This demonstrates a full end-to-end pipeline: scraping → document processing → embedding + indexing → retrieval-augmented agent → interactive UI.

## Project Structure
nora/
├── .venv/
├── .env
├── data/
│   ├── history_copy.db
│   └── chroma_db/     # records -> '2025-08-01', '2025-12-01'
│   └── chroma_db_full/ # retrieved a larger date range from my history -> '2025-01-01', '2025-12-01'
│   └── user_profile.txt # basic user profile generated to give the AI context
├── src/
│   ├── extract_urls.py   
│   ├── scraping.py   
│   ├── profile_gen.py
│   ├── agent.py          
├── app.py
└── README.md

## How to run

> Prerequisite: Obtain your OpenAI API keys for embedding and gpt use!









