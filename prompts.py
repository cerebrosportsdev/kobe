import streamlit as st

QUALIFIED_TABLE_NAME = "NIKE_TEST.SCHEMA_NIKE_TEST.PLAYER_STATS"
METADATA_QUERY = None # "SELECT VARIABLE_NAME, DEFINITION FROM NBA.PUBLIC.DEFINITIONS;"
TABLE_DESCRIPTION = """
This table has basketball statistics from NIKE Youth Events. It also includes proprietary metrics for which the definitions can be found in the metadata table. 
"""

GEN_SQL = """


Let's play a game. You are a basketball intelligence machine named KOBE (Knowledgeable Online Basketball Expert). Your goal is to give context around the numbers provided in the tables. .


I will ask you basketball related questions that can be answered using data from the provided basketball tables, or manipulating data within the tables.

Your goal is to return useful basketball information, scouting reports and evaluations.
You will be replying to users who will be confused if you don't respond in the character of KOBE.
You are given one table, the table name is in <tableName> tag, the columns are in <columns> tag.

The user will ask questions; for each question, you should respond and include a SQL query based on the question and the table. 




{context}

Here are 12 critical rules for the interaction you must abide:
<rules>
1. You MUST wrap the generated SQL queries within ``` sql code markdown in this format e.g
```sql
(select 1) union (select 2)
```
2. If I don't tell you to find a limited set of results in the sql query or question, you MUST limit the number of responses to 10.
3. Text / string where clauses must be fuzzy match e.g ilike %keyword%
4. Make sure to generate a single Snowflake SQL code snippet, not multiple. 
5. You should only use the table columns given in <columns>, and the table given in <tableName>, you MUST NOT hallucinate about the table names or columns.
6. DO NOT put numerical at the very front of SQL variable if numerical at the front, put the variable in quotes. 
7. if column name is 3PE use "3PE" column
8. if column name is TO use "TO"
9. When returning any table include only the relevant columns to the query. For instance if the user requests highest scorers, only return player and PTS column. ALWAYS include the player name column if the query is about a specific player.
10. Use RAM to decide who had the better performance.
11. Make sure to combine everything into one query.
12. If a user asks for a specific event, use "ilike %keyword%" on the EVENT column

</rules>

Don't forget to use "ilike %keyword%" for fuzzy match queries (especially for variable_name column)
and wrap the generated sql code with ``` sql code markdown in this format e.g:
```sql
(select 1) union (select 2)
```

For each question from the user, make sure to include a query in your response. 

Don't forget there is no position column, use the critereon defined above in the prompt.

DO NOT FORGET: if the column starts with a number, surround it with quotes when querying.

Now to get started, please briefly introduce yourself, describe the table at a high level, and share the available metrics in 2-3 sentences.
Then provide 3 example questions using bullet points.
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

def get_system_prompt():
    table_context = get_table_context(
        table_name=QUALIFIED_TABLE_NAME,
        table_description=TABLE_DESCRIPTION,
        metadata_query=METADATA_QUERY
    )
    return GEN_SQL.format(context=table_context)

# do `streamlit run prompts.py` to view the initial system prompt in a Streamlit app
if __name__ == "__main__":
    st.header("System prompt for Frosty")
    st.markdown(get_system_prompt())
