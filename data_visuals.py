import json
import openai
import streamlit as st

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


def create_visuals(model_response):
    chart_data = generate_visualization(model_response, st.session_state.messages[-1]["content"])
    if chart_data != {}:
        type = chart_data['type']
        if type == 'BAR':
            st.bar_chart(data=model_response, x=f"{chart_data['x']}", y=f"{chart_data['y']}")


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
