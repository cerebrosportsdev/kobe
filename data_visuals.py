import json
import openai
import streamlit as st

viz_classification_prompt = '''
You are responsible for determining the appropriate visualization for the following basketball data. 
Evaluate whether the data should be visualized at all, and if so, choose between a BAR, PIE, LINE, or SCATTER chart.
You will receive the original question from a user and the data that was retrieved for that query. 
Return your answer in JSON format. If the data cannot be visualized or it is unclear, return {"requires_visuals": false}.
If visualization is required, specify the type of chart and the columns for the x and y axes:
{
    "requires_visuals": true,
    "type": "[BAR, LINE, SCATTER]",
    "x": "[the column name for data to be displayed on the x axis]",
    "y": "[the column name for data to be displayed on the y axis]"
}
'''

def create_visuals(model_response):
    chart_data = generate_visualization(model_response, st.session_state.messages[-1]["content"])
    if chart_data['requires_visuals'] == True:
        type = chart_data['type']
        x_axis = chart_data['x']
        y_axis = chart_data['y']

        if type == 'BAR':
            st.bar_chart(data=model_response, x=f"{chart_data['x']}", y=f"{chart_data['y']}")
        elif type == 'LINE':
            st.line_chart(data=model_response, x=y_axis, y=y_axis)
        elif type == 'SCATTER':
            # For scatter plots, ensure the data is plotted with appropriate axes.
            st.plotly_chart({
                'data': [{'x': model_response[x_axis], 'y': model_response[y_axis], 'type': 'scatter', 'mode': 'markers'}],
                'layout': {'title': 'Scatter Plot', 'xaxis': {'title': x_axis}, 'yaxis': {'title': y_axis}}
            })


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
