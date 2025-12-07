import streamlit as st
import numpy as np
np.float_ = np.float64

from agent import history_qa_agent_invoke, HistoryResponse, load_profile

# --- CONFIGURATION ---
TEST_THREAD_ID = "streamlit_session"

# Load user profile once
USER_PROFILE = load_profile()

# --- STREAMLIT SETUP ---
st.set_page_config(page_title="Personal Web Memory Agent", layout="wide")
st.title("Valentina's Web Memory Agent")

st.markdown("""
    Welcome! This agent uses AI to search my personal browsing history and allows you to have conversations with it.
""")

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
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("Searching memory..."):
        try:
            response: HistoryResponse = history_qa_agent_invoke(prompt, thread_id=TEST_THREAD_ID)
            agent_response = response.answer
        except Exception as e:
            agent_response = f"An internal error occurred: {e}"
            st.error("Agent failed to process the request. See console for full error.")
            print(f"--- AGENT FAILURE --- \n Full Error: {e}")

    with st.chat_message("assistant"):
        st.markdown(agent_response)

    st.session_state.messages.append({"role": "assistant", "content": agent_response})