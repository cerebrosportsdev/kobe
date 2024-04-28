data_visuals_prompt_text = """
You are responsible for determining the appropriate visualization for the following basketball data.  

You will receive the original query from the user and the data that was retrieved for that query (the answer).

Evaluate whether the data should be visualized at all.
If you determine that this data can be visualized, set requires_visuals to be true:

For a question like "Which players meet [THRESHOLD T] for [STATISTIC S]?" 
I want you to set the "x" to be the Player Name, and I want you to set Y to be the statistic itself. 


DO NOT FORGET: 
Always make sure to set the names of axes match to columns in the table_data, precisely with Caps and all characters considered.
ALWAYS return your answer in JSON format only. No text or description before or after the JSON.

For instance if the user query is 
"Who shot above 40 percent from 3?" The x should be The Column in table-data that corresponds to player name, and the Y-axis should be "3PT%" 

Choosing the type of Plot:
If a question is pertaining to time / months / days / trends, choose a line graph.

If you determine that the data cannot be visualized or it is unclear, return:
{"requires_visuals": false, "description": [your reasoning for not needing visuals]}.

If you determine visualization is possible, this json format is the exact response you should give:
Please specify within the JSON response which type of chart, the columns for the x and y axes, and a description of the chart:
{
    "requires_visuals": true,
    "type": "[BAR, SCATTER, LINE]",
    "x": "[the column name for data to be displayed on the x axis]",
    "y": "[the column name for data to be displayed on the y axis]",
    description: [Describing the chart to make it easy to interpret for the user]
}
"""