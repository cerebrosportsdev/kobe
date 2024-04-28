import openai
import re
import streamlit as st
from prompts import get_system_prompt, WELCOME_MESSAGE_PROMPT
from data_visuals import create_visuals
from functions import generate_responses

LOGIN_PASSWORD = "CerebroAI"
openai.api_key = st.secrets.OPENAI_API_KEY
password_placeholder = "Please Enter The Password"

conn = st.experimental_connection("snowpark")

st.title("🔍 CerebroAI")
st.caption("Chat with the largest basketball dataset ... ever.")

# Initialize session state for login
if "login" not in st.session_state:
    st.session_state.login = ""

if st.session_state.login != LOGIN_PASSWORD:
    login_attempt_input = st.text_input("Enter Password", type = 'password', placeholder=password_placeholder)
    if login_attempt_input == LOGIN_PASSWORD:
        st.session_state.login = login_attempt_input
        st.experimental_rerun()
    else:
        if login_attempt_input: # Unsuccessful Login
            st.error("Incorrect Password. Please Try Again")
            st.caption("*Hint: You Get No Hints*")
else: # Following LOGIN_SUCCESS

    # Refresh Button
    if st.button("Refresh"):
        conn.reset()
        st.session_state.clear()

    # Initialize the chat messages history
    conn.reset()
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "system", "content": WELCOME_MESSAGE_PROMPT, "key": "welcome-message"}]

    # Prompt for user input and save
    if user_query := st.chat_input():
        system_prompt = get_system_prompt(user_query)
        st.session_state.messages.append({"role": "system", "content": system_prompt})
        st.session_state.messages.append({"role": "user", "content": user_query})

    # display the existing chat messages
    for message in st.session_state.messages:
        if message["role"] == "system":
            continue
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if "results" in message:
                st.dataframe(message["results"])

    # If last message is not from assistant, we need to generate a new response
    if st.session_state.messages[-1]["role"] != "assistant":
        with st.chat_message("assistant"):
            
            # Placeholder for loading ...
            text_placeholder = st.empty()
            text_placeholder.caption("Assistant is typing...")
            gif_placeholder = st.empty()
            gif_placeholder.image("shaiDance.gif", width=250)

            # Generate and Classify Model Responses
            responses = generate_responses(st.session_state.messages)

            # Clear Loading placeholders
            text_placeholder.empty()  # Clears the text
            gif_placeholder.empty()  # Clears the GIF
            
            for response_object in responses:
                response_type = response_object["type"]
                response_content = response_object["content"]

                if response_type == "welcome_message":
                    st.markdown(response_content)
                
                elif response_type == "sql_response":
                    
                    # Showing the Query Gen Response: strictly for debugging the query itself
                    # st.markdown(response_content)
                    
                    message = {"role": "assistant", "content": response_content}
                    
                    sql_match = re.search(r"```sql\n(.*)\n```", response_content, re.DOTALL)
                    if sql_match:
                        sql = sql_match.group(1)
                        table_response = conn.query(sql)

                        message["results"] = table_response
                        message["key"] = response_type

                        st.caption("Here's whats I think you were looking for:")
                        st.dataframe(table_response)

                        create_visuals(table_response)
                    st.session_state.messages.append(message)
                    conn.reset()
                    session = st.experimental_connection("snowpark").session