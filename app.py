import os

import streamlit as st
from langchain_core.tools import tool
from langchain.agents import create_agent

# from langchain_openrouter import ChatOpenRouter
from langchain.chat_models import init_chat_model

import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


@tool
def list_tables() -> str:
    """Lists all the tables in PostgreSQL database."""
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
""")
        tables = cursor.fetchall()
        if not tables:
            return "No tables found in the database"
        return "\n".join(table[0] for table in tables)

    except Exception as e:
        return f"Error while listing tables: {e}"
    finally:
        if connection:
            connection.close()
        if cursor:
            cursor.close()


@tool
def get_schema(table_name: str) -> str:
    """Get the column and data types of a PostgreSQL table"""
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = %s
        ORDER BY ordinal_position

""",
            (table_name,),
        )
        columns = cursor.fetchall()
        if not columns:
            return f"Table '{table_name}' doesn't exists."

        result = []
        for column in columns:
            column_name = column[0]
            column_datatype = column[1]
            column_nullable = column[2]
            result.append(
                f"Column: {column_name}, Type: {column_datatype}, Nullable: {column_nullable}"
            )
        return "\n".join(result)

    except Exception as e:
        return f"Error while getting schema: {e}"
    finally:
        if connection:
            connection.close()
        if cursor:
            cursor.close()


@tool
def execute_query(query: str) -> str:
    """Execute a read-only SQL query using PostgreSQL only SELECT query is allowed."""
    query = query.strip()

    if query.startswith("```sql"):
        query = query[6:]
    elif query.startswith("```"):
        query = query[3:]
    elif query.endswith("```"):
        query = query[:-3]
    query = query.strip()

    query_lower = query.lower()

    if not query_lower.startswith("select"):
        return """Error: Only SELECT  queries are allowed"""

    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        col_names = (
            [desc[0] for desc in cursor.description] if cursor.description else []
        )

        if not rows:
            return "Query executed successfully. No rows found"

        lines = [" | ".join(col_names)] if col_names else []
        for row in rows:
            for val in row:
                lines.append(" | ".join(str(val)))
        return "\n".join(lines)

    except Exception as e:
        return f"SQL execution error: {e}"
    finally:
        if connection:
            connection.close()
        if cursor:
            cursor.close()


tools = [list_tables, get_schema, execute_query]


llm = init_chat_model(model="groq:qwen/qwen3.8-27b")

system_prompt = """
You are a PostgreSQL database assistant.
Your job is to answer queries using the PostgreSQL database

Follow this process:
1. Use list_tables to discover available tables.
2. Identify the table relevant to the user's question
3. Use get_schema to inspect relevant tables.
4. Generate valid PostgreSQL SQL queries.
5. Use execute_query to execute the SQL queries.
6. Use the returned return to answer user.

IMPORTANT RULES:
- Only retrieve data.
- Only SELECT query is allowed.
- Never INSERT.
- Never UPDATE.
- Never DELETE.
- Never DROP.
- Never TRUNCATE.
- Never ALTER.
- Never CREATE.
- Never GRANT.
- Never REVOKE.
- Never invent table names.
- Never invent column names.
- Always inspect the schema before generating SQL when necessary.
- If SQL execution fails, analyze the error and correct the SQL.
- Do not make up the database results.
- Answer based only on the actual database result.
- Keep answers concise and clear.

"""
agent = create_agent(model=llm, tools=tools, system_prompt=system_prompt)

st.set_page_config(page_title="PostgreSQL AI Assistant", page_icon="🤖", layout="wide")

st.title("PostgreSQL AI Assistant")
st.caption("Ask queries about your PostgreSQL database using natural language.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

question = st.chat_input("Ask something about your database.")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking and quering database"):
            try:
                response = agent.invoke(
                    {"messages": [{"role": "user", "content": question}]}
                )
                answer = response["messages"][-1].content
            except Exception as e:
                answer = f"Error: {e}"
        st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})
