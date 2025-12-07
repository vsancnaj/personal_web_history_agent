import streamlit as st
import os
import datetime
import numpy as np
np.float_ = np.float64
# Import core agent components from your agent logic file
from src.agent import history_qa_agent_invoke, HistoryResponse, load_profile 

# --- CONFIGURATION ---
# Define the thread ID for continuous memory (LangGraph requires this for session tracking)
TEST_THREAD_ID = "streamlit_session" 

# Load user profile once
USER_PROFILE = load_profile()

# --- STREAMLIT SETUP ---
st.set_page_config(page_title="Personal Web Memory Agent", layout="wide")
st.title("Valentina's Web Memory Agent")

st.markdown(f"""
    Welcome! This agent uses AI to search my personal browsing history and allows you to have conversations with it.

""")    # **Profile Summary:** {USER_PROFILE[:2000]}

with st.expander("🔒 User Profile"):
    st.markdown(USER_PROFILE)

# Initialize chat history in Streamlit session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- MAIN CHAT INPUT & LOGIC ---
if prompt := st.chat_input("Ask something..."):
    
    # 1. Display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Invoke the agent
    with st.spinner("Searching memory..."):
        try:
            # Invoke the agent using the fixed thread ID for memory
            # The history_qa_agent_invoke function now handles wrapping the message in a dict.
            response: HistoryResponse = history_qa_agent_invoke(prompt, thread_id=TEST_THREAD_ID)

            # Format the answer
            agent_response = response.answer
            


        except Exception as e:
            # Catch exceptions from the agent or database
            agent_response = f"An internal error occurred: {e}"
            st.error("Agent failed to process the request. See console for full error.")
            print(f"--- AGENT FAILURE --- \n Full Error: {e}")


    # 3. Display agent response
    with st.chat_message("assistant"):
        st.markdown(agent_response)
        
    # 4. Update session history
    st.session_state.messages.append({"role": "assistant", "content": agent_response})