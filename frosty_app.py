import openai
import re
import streamlit as st
from prompts import get_system_prompt
from data_visuals import create_visuals
import json

viz_classification_prompt = '''
You are responsible for determining whether the following basketball data should be visualized in a BAR chart or a PIE chart.
You will get the original question from a user who is asking a question about some data, and the data that was retrieved for that
query. Only return your answer in JSON format. If the data cannot be visualized or it is unclear, return an empty JSON object {}.
{
    "type": "[BAR or PIE]"
    "x": "[the column name for data to be displayed on the x axis]"
    "y": "[the column name for data to be displayed on the y axis]"
}
'''

st.title("KOBE v2")
conn = st.experimental_connection("snowpark")
openai.api_key = st.secrets.OPENAI_API_KEY
if st.button("Refresh"):
    conn.reset()

# generate a different type of visualization based on the output of the second call.
def generate_visualization(table_data, conversation_context):
    # Format the prompt and table data correctly
    input_text = f"Question: {conversation_context}\nTable Data:\n{table_data}"
    full_prompt = viz_classification_prompt + input_text
    
    print("Formatted Input")
    print(full_prompt)

    try:
        response = openai.Completion.create(
            model="gpt-3.5-turbo-instruct",  # Or another suitable model
            prompt=full_prompt,
            max_tokens=150
        )
        print("GPT-4 Response:")
        print(response)

        content = response['choices'][0]['text'].strip()
        print("Extracted Content:")
        print(content)

        # Parse JSON output
        visualization_config = json.loads(content)
        print("Visualization Configuration:")
        print(visualization_config)
        
        return visualization_config

    except Exception as e:
        print(f"An error occurred: {e}")
        return {}

if "login" not in st.session_state:
    st.session_state.login = ""
password = ""
if st.session_state.login == "":
    st.session_state.login = st.text_input("Enter Password", type = 'password')

if st.session_state.login == "password":
    # Initialize the chat messages history
    conn.reset()
    openai.api_key = st.secrets.OPENAI_API_KEY
    if "messages" not in st.session_state:
        # system prompt includes table information, rules, and prompts the LLM to produce
        # a welcome message to the user.
        st.session_state.messages = [{"role": "system", "content": get_system_prompt()}]

    # Prompt for user input and save
    if prompt := st.chat_input():
        st.session_state.messages.append({"role": "user", "content": prompt})

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
            response = ""
            resp_container = st.empty()
            for delta in openai.ChatCompletion.create(
                model="gpt-4-1106-preview",
                messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                stream=True,
            ):
                response += delta.choices[0].delta.get("content", "")
                resp_container.markdown(response)

            message = {"role": "assistant", "content": response}
            # Parse the response for a SQL query and execute if available
            sql_match = re.search(r"```sql\n(.*)\n```", response, re.DOTALL)
            if sql_match:
                sql = sql_match.group(1)
                message["results"] = conn.query(sql)
                model_response = message["results"]
                st.dataframe(model_response)

                create_visuals(model_response)


            st.session_state.messages.append(message)
            conn.reset()
            session = st.experimental_connection("snowpark").session