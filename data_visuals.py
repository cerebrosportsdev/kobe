import json
import openai
import streamlit as st
import altair as alt

from data_visuals_prompts import data_visuals_prompt_text

def create_visuals(model_response):
    
    chart_data = generate_visualization(model_response, st.session_state.messages[-1]["content"])
    #Looks like {'requires_visuals': True, 'type': 'BAR', 'x': 'PLAYER', 'y': '3PM'}

    if chart_data.get('requires_visuals') == True:
        type = chart_data['type'].upper()
        x_axis = chart_data['x']
        y_axis = chart_data['y']

        if type == 'BAR':
            #create the altair chart
            altair_source_chart = (
                alt.Chart(model_response).mark_bar().encode(
                    x=x_axis,
                    y=y_axis
                )
            )

            #render source chart on streamlit
            st.altair_chart(altair_source_chart, use_container_width=True)
            
        elif type == 'LINE':
            #create the altair chart
            altair_source_chart = (
                alt.Chart(model_response).mark_line().encode(
                    x=x_axis,
                    y=y_axis
                )
            )

            #render source chart on streamlit
            st.altair_chart(altair_source_chart, use_container_width=True)
        elif type == 'SCATTER':
            #create the altair chart
            altair_source_chart = (
                alt.Chart(model_response).mark_circle().encode(
                    x=x_axis,
                    y=y_axis
                )
            )

            #render source chart on streamlit
            st.altair_chart(altair_source_chart, use_container_width=True)


# generate a different type of visualization based on the output of the second call.
def generate_visualization(table_data, conversation_context):
    # Format the prompt and table data correctly
    input_text = f"Question: {conversation_context}\nTable Data:\n{table_data}"
    full_prompt = data_visuals_prompt_text + input_text
    
    print("Full Prompt:")
    print(full_prompt)

    try:
        response = openai.Completion.create(
            model="gpt-3.5-turbo-instruct",  # Or another suitable model
            prompt=full_prompt,
            max_tokens=150
        )

        query_response = response['choices'][0]['text'].strip()

        # Parse JSON output
        visualization_config = json.loads(query_response)

        #View GPT Response for Debug
        print("Visualization Configuration:")
        print(visualization_config)
        
        return visualization_config

    except Exception as e:
        print(f"An error occurred: {e}")
        return {}
