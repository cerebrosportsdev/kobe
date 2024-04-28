import openai
import streamlit as st

def generate_responses(messages):
    responses = []

    response_content = ""
    for delta in openai.ChatCompletion.create(
        model="gpt-4-1106-preview",
        messages=[{"role": m["role"], "content": m["content"]} for m in messages],
        stream=True,
    ):
        response_content += delta.choices[0].delta.get("content", "")
        # Add simple logic to classify the type of response
    if "```sql" in response_content:
        response_type = "sql_response"
    elif "I am CerebroAI" in response_content:
        response_type = "welcome_message"
    else:
        response_type = "info"
    
    responses.append({"content": response_content, "type": response_type})

    return responses