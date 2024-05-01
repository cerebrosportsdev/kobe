import streamlit as st
import openai
import json

QUALIFIED_TABLE_NAME = "NIKE_TEST.SCHEMA_NIKE_TEST.PLAYER_STATS_WITH_YEAR"

METADATA_QUERY = None # "SELECT VARIABLE_NAME, DEFINITION FROM NBA.PUBLIC.DEFINITIONS;"

TABLE_DESCRIPTION = """
This table has basketball statistics.
"""

NO_RESPONSE_TEXT = """\n
*I couldn't come up with a response, sorry!*\n

Some reasons could be: \n
```
1. The player you searched for didn't match the names in our database. Maybe try their legal full name? \n
2. The event you searched for either doesn't exist or is specified differently in our database. Try asking if the event exists or rewording the event title. \n
3. Maybe you are trying to do analysis that I can't quite complete myself yet! I really do apologize, and hope to be improve. In the meantime, please create a supprt ticket [here](https://beacons.ai/hoops_dojo)! \n\n
```
*How about you try again, or use some additional context that might help me sift through our database better.*
"""

WELCOME_MESSAGE_PROMPT = """
Hello there! I am Cerebro AI! \n

I'm an intelligence built by RAN to dive deep into any basketball statistics you'd like to know about. 
Right now, I can answer questions about Nike Youth Tournaments. \n

If you're here for deep insights about hoops, try a few queries. Here are some examples of what you can ask me: \n\n

1. How many threes did Cooper Flagg make throughout all his 16U tournaments?, \n
2. Who averaged the most steals in the 2023 Nike EYBL Tournament\n
3. How did Bronny play in the Peach Jam in 2022?\n
"""

GENERATE_SQL_PROMPT ="""

Let's play a game. You are a basketball intelligence machine named Cerebro AI (AKA KOBE). Your goal is to give context around the numbers provided in the tables. .

I will ask you basketball related questions that can be answered using data from the provided basketball tables, or manipulating data within the tables.

Your goal is to return useful basketball information, scouting reports and evaluations.
You will be replying to users who will be confused if you don't respond in the character of CerebroAI. 

You are given one or more tables, with their Name in the <tableName> tag, the columns are in <columns> tag.

The user will ask questions; for each question, you should respond and include a SQL query based on the question and the tables you have access to. 

You may need to access multiple tables in a query if the question asks like a player's percentage of turnovers for a team.

{context}

Here are 13 critical rules for the interaction you must abide:

<rules>
1. You MUST wrap the generated SQL queries within ``` sql code markdown in this format e.g
```sql
(select 1) union (select 2)
```
2. Text / string where clauses must be fuzzy match e.g ilike %keyword%
3. Make sure to generate a single Snowflake SQL code snippet, not multiple. 
4. You should only use the table columns given in <columns>, and the table given in <tableName>, you MUST NOT hallucinate about the table names or columns.
5. DO NOT put numerical at the very front of SQL variable if numerical at the front, put the variable in quotes. 
6. if column name is 3PE use "3PE" column
7. if column name is TO use "TO"
8. When returning the sql query, include in the SELECT the relevant columns to the user's request. This should be ALL RELEVANT STATS they might want to see. 
  For instance if the user requests highest scorers, SELECT PLAYER and PTS columns, and maybe the season or event as well for relevance to make it clear to interpret.
  Do not forget to keep the event or the season column if the user requests about a specific season or a specific event.
9. Use RAM to decide who had the better performance, but only if RAM exists as a column..
10. Make sure to combine everything into one query.
11. If a user asks for a specific event, use "ilike %keyword%" on the EVENT col (for instance “ilike %NIKE EYBL%”). Do not include the year, instead query the column called "YEAR" for the year the user is asking.
12. In case of no limit, use LIMIT 4999.

</rules>

Don't forget to use "ilike %keyword%" for fuzzy match queries (especially for variable_name column)
and wrap the generated sql code with ``` sql code markdown in this format e.g:
```sql
(select 1) union (select 2)
```

If asked about the "top" or "total" number of stats over a singular event, you should run an aggregation 
of all of the specific stats for each player for ALL games in the event. 

For example, if the user asks something like "Who are the top [#] Players in [STATISTIC S] for [EVENT E]?” 
Like Who are the top 10 players in 3 pointers made in 2022 Nike EYBL.
You should, for each game in that event, sum up all the 3 pointers for each specific player.
You should be using a query similar to:
    ```sql
    SELECT PLAYER, SUM(THREE_POINTS_MADE) AS TOTAL_THREE_POINTS_MADE
    FROM [relevant table]
    GROUP BY PLAYER;
    LIMIT [#]
    ```

For each question from the user, include only the query as formatted and described above in your response. No other text, description, or nonsense please

Don't forget there is no position column, use the criterion defined above in the prompt.

DO NOT FORGET: if the column starts with a number, surround it with quotes when querying.
"""

CHOOSE_TABLE_PROMPT = """
Given the following user query about basketball statistics, decide which tables from the database should be used to answer the query. The possible tables are:
1. Youth Event Stats: NIKE_TEST.SCHEMA_NIKE_TEST.PLAYER_STATS_WITH_YEAR
2. NBA Box Score Stats: NBA.PUBLIC.REGULAR_SZN

Please return the names of the relevant tables in a list based on the content of the query.
Do not include any additional words or characters besides the brackets, quotes, and the name of the table.

User Query: "{query}"

Example:
If the query is about an NBA player, you should return: ["NBA.PUBLIC.REGULAR_SZN"]
If the query is about a youth event like peach jam: ["NIKE_TEST.SCHEMA_NIKE_TEST.PLAYER_STATS_WITH_YEAR"]
"""


@st.cache_data(show_spinner=False)
def get_table_context(table_name: str, table_description: str, metadata_query: str = None):
    table = table_name.split(".")
    conn = st.experimental_connection("snowpark")
    columns = conn.query(f"""
        SELECT COLUMN_NAME, DATA_TYPE FROM {table[0].upper()}.INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = '{table[1].upper()}' AND TABLE_NAME = '{table[2].upper()}'
        """,
    )
    columns = "\n".join(
        [
            f"- **{columns['COLUMN_NAME'][i]}**: {columns['DATA_TYPE'][i]}"
            for i in range(len(columns["COLUMN_NAME"]))
        ]
    )
    context = f"""
        Here is the table name <tableName> {'.'.join(table)} </tableName>

        <tableDescription>{table_description}</tableDescription>

        Here are the columns of the {'.'.join(table)}

        <columns>\n\n{columns}\n\n</columns>
    """
    if metadata_query:
        metadata = conn.query(metadata_query)
        metadata = "\n".join(
            [
                f"- **{metadata['VARIABLE_NAME'][i]}**: {metadata['DEFINITION'][i]}"
                for i in range(len(metadata["VARIABLE_NAME"]))
            ]
        )
        context = context + f"\n\nAvailable variables by VARIABLE_NAME:\n\n{metadata}"

    return context

def get_system_prompt(user_query):

    # commenting to save on extra openai call for choosing table
    # get_table_response = openai.Completion.create(
    #         model="gpt-3.5-turbo-instruct",
    #         prompt=CHOOSE_TABLE_PROMPT.format(query=user_query),
    #         max_tokens=150
    # )

    # for debugging - save API calls
    # get_table_response_text = get_table_response['choices'][0]['text']
    get_table_response_text = '["NIKE_TEST.SCHEMA_NIKE_TEST.PLAYER_STATS_WITH_YEAR"]'
    
    table_names = json.loads(get_table_response_text)
    
    table_context = []
    for table_name in table_names:
        table_context.append(
            get_table_context(
                table_name=table_name,
                table_description=TABLE_DESCRIPTION,
                metadata_query=METADATA_QUERY
            )
        )

    
    FINAL_SQL_PROMPT = GENERATE_SQL_PROMPT.format(context=table_context)

    return FINAL_SQL_PROMPT

# do `streamlit run prompts.py` to view the initial system prompt in a Streamlit app
if __name__ == "__main__":
    st.header("System prompt for Frosty")
    st.markdown(get_system_prompt())
