import openai
import re
import streamlit as st

from prompts import get_system_prompt, WELCOME_MESSAGE_PROMPT, NO_RESPONSE_TEXT
from data_visuals import create_and_display_chart
from functions import generate_responses
from st_aggrid import AgGrid

LOGIN_PASSWORD = "CerebroAI"
openai.api_key = st.secrets.OPENAI_API_KEY
password_placeholder = "Please Enter The Password"

conn = st.experimental_connection("snowpark")

st.title("🔍 CerebroAI")
st.caption("Chat with the largest basketball dataset ... ever.")

# Initialize session state for login
if "login" not in st.session_state:
    st.session_state.login = ""

if 'loading' not in st.session_state:
    st.session_state.loading = False
if 'text_placeholder' not in st.session_state:
    st.session_state.text_placeholder = st.empty()
if 'gif_placeholder' not in st.session_state:
    st.session_state.gif_placeholder = st.empty()

# Handle Login
login_attempt_input = st.text_input("Enter Password", type = 'password', placeholder=password_placeholder)
if login_attempt_input and st.session_state.login != LOGIN_PASSWORD:
    if login_attempt_input == LOGIN_PASSWORD:
        st.session_state.login = login_attempt_input
        st.experimental_rerun()
    else:
        st.error("Incorrect Password. Please Try Again")
        st.caption("*Hint: You get no hints*")

# Following LOGIN_SUCCESS
if st.session_state.login == LOGIN_PASSWORD:

    # Refresh Button
    if st.button("Refresh"):
        conn.reset()
        st.session_state.messages.clear()
        st.session_state.clear()
        st.experimental_rerun()

    # Initialize the chat messages history
    conn.reset()
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": WELCOME_MESSAGE_PROMPT, "key": "welcome_message"}]

    # Prompt for user input and save
    if user_query := st.chat_input():
        system_prompt = get_system_prompt(user_query)
        st.session_state.messages.append({"role": "system", "content": system_prompt})
        st.session_state.messages.append({"role": "user", "content": user_query})

    # display the existing chat messages
    for message in st.session_state.messages:
        if message["role"] == "system":
            continue
        if message["role"] == "assistant" and "key" in message:
            if "results" in message:
                with st.chat_message(message["role"]):    
                    # AgGrid(message["results"])
                    st.dataframe(message["results"])
                    if message["key"] == "sql_response":
                        create_and_display_chart(message)
            if message["key"] == 'welcome_message':
                with st.chat_message(message["role"]):
                    st.write(message["content"])
        
        if message["role"] == "user":
            with st.chat_message(message["role"]):    
                st.write(message["content"])


    # If last message is not from assistant, we need to generate a new response
    if st.session_state.messages[-1]["role"] != "assistant":
        with st.chat_message("assistant"):
            
            # Placeholder for loading ...
            text_placeholder = st.empty()
            text_placeholder.caption("Let me check with the basketball gods...")
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

                # if response_type == "welcome_message":
                #     st.markdown(response_content)
                
                if response_type == "sql_response":
                    
                    # Showing the Query Gen Response: strictly for debugging the query itself
                    # st.markdown(response_content)
                    
                    message = {"role": "assistant", "content": response_content}
                    
                    sql_match = re.search(r"```sql\n(.*)\n```", response_content, re.DOTALL)
                    if sql_match:
                        sql = sql_match.group(1)
                        table_response = conn.query(sql)

                        message["results"] = table_response
                        message["key"] = response_type

                        if (table_response.empty == False):
                            st.caption("Here's whats I think you were looking for:")
                            st.dataframe(table_response)
                            # AgGrid(table_response)

                            message["chart_data"] = create_and_display_chart(message)
                        else:
                            st.markdown(NO_RESPONSE_TEXT)

                    st.session_state.messages.append(message)
                    conn.reset()
                    session = st.experimental_connection("snowpark").session