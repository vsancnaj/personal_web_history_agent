# My Personal Web Memory Agent

Hi! My name is Valentina and you are interacting with my Chrome web search histroy from
particular dates(so not my whole history)

A lightweight personal tool that:  
- Extracts your Chrome browsing history,  
- Scrapes the visited pages’ content,  
- Embeds and indexes them into a vector store,  
- Lets you query your past browsing via a chat UI powered by an LLM + retrieval.

## DEMO


https://github.com/user-attachments/assets/ae116288-edde-45ac-82c1-467ac49aa06b




This demonstrates a full end-to-end pipeline: scraping → document processing → embedding + indexing → retrieval-augmented agent → interactive UI.

> Prerequisite: Obtain your OpenAI API keys for embedding and gpt use!

## Project Structure
```
personal_web_history_agent/
├── .venv/
├── .env
├── data/
│   ├── history_copy.db
│   └── chroma_db/     # records -> '2025-08-01', '2025-12-01'
│   └── chroma_db_full/ # retrieved a larger date range from my history -> '2025-01-01', '2025-12-01'
│   └── user_profile.txt # basic user profile generated to give the AI context
├── src/
├── __init__.py   
│   ├── extract_urls.py   
│   ├── scraping.py   
│   ├── profile_gen.py  
├── app.py
├── agent.py 
└── README.md
```
## How to run without my Streamlit Link

> Prerequisite: Obtain your OpenAI API keys for embedding and gpt use!
```
# 1. Clone the repository
git clone https://github.com/vsancnaj/personal_web_history_agent.git
cd personal_web_history_agent

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt  

# 4. Configure environment variables
OPENAI_API_KEY=your_key_here

# 5. Launch the chat UI
streamlit run app.py
```













