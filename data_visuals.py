import json
import openai
import re
import streamlit as st
import altair as alt
import time

from data_visuals_prompts import data_visuals_prompt_text

def error_handle(message_object):
    if not message_object:
        return True
    
    if "results" not in message_object:
        print("results incorrect: \n ", message_object)
        return True

    if "key" not in message_object:
        print("key incorrect: \n ", message_object)
        return True

    return False # No Error

# Data Viz Entry Pt
def create_and_display_chart(message_object):

    if error_handle(message_object):
        return

    table_data = message_object["results"]
    # mesasge_type = message_object["key"]

    # for debugging - save API calls
    chart_data = message_object.get("chart_data", generate_visualization_from_gpt(table_data, st.session_state.messages[-1]["content"]))
    # chart_data = message_object.get("chart_data", {'requires_visuals': True, 'type': 'LINE', 'x': 'DATE', 'y': 'TOTAL_POINTS'})

    if not chart_data:
        print("message no chart: ", message_object)
        return 
    time.sleep(1)

    if chart_data.get('requires_visuals') == False:
        st.text("No relevant visual generated. Ask me another question!")
        return

    if chart_data.get('requires_visuals') == True:
        try: 
            type = chart_data['type'].upper()
            x_axis = chart_data['x']
            y_axis = chart_data['y']

            if type == 'BAR':
                altair_source_chart = (
                    alt.Chart(table_data).mark_bar().encode(
                        alt.X(x_axis),
                        alt.Y(y_axis)
                    )
                )            
            elif type == 'LINE':
                #create the altair chart
                altair_source_chart = (
                    alt.Chart(table_data).mark_line().encode(
                        x=x_axis,
                        y=y_axis
                    )
                )
            elif type == 'SCATTER':
                #create the altair chart
                altair_source_chart = (
                    alt.Chart(table_data).mark_circle().encode(
                        x=x_axis,
                        y=y_axis
                    )
                )
            #render source chart on streamlit        
            st.altair_chart(altair_source_chart, use_container_width=True)
            
            return chart_data
        except Exception as e:
            error_text = (f'Could not produce visual because of error: {e}')
            print(error_text)
            st.code("No Visualization Generated. See logs for more info")

# generate a different type of visualization based on the output of the second call.
def generate_visualization_from_gpt(table_data, conversation_context):
    # Format the prompt and table data correctly
    input_text = f"Question: {conversation_context}\nTable Data:\n{table_data}"
    full_prompt = data_visuals_prompt_text + input_text

    try:
        response = openai.Completion.create(
            model="gpt-3.5-turbo-instruct",  # Or another suitable model
            prompt=full_prompt,
            max_tokens=150
        )

        query_response = response['choices'][0]['text'].strip()

        print("Data Visual JSON Response from AI: \n", query_response)        
        # Parse JSON output
        json_match = re.search(r'\{.*?\}', query_response, re.DOTALL)
        
        if json_match:
            visualization_config = json.loads(json_match.group(0))
            return visualization_config
        else:
            print("No JSON found in response.")
            return {"requires_visuals": False}

    except Exception as e:
        print(f"An error occurred: {e}")
        st.code("No Visualization Generated")
        return {}

