import os
from dotenv import load_dotenv
import streamlit as st
import modules.msal_auth as msal_auth
import modules.llm as llm
import modules.sqldb as sqldb
import modules.prompts as prompts

load_dotenv()

def main():

    with st.sidebar:
        st.header("Azure SQL Database configuration")
        
        # checkbox to enable/disable the my connection
        use_my_connection = st.checkbox("Use my connection")
        if use_my_connection:
            my_endpoint = st.text_input("Azure SQL endpoint", "xxxxxx.database.windows.net")
            my_database = st.text_input("Azure SQL database", "database_name")
            my_user = st.text_input("SQL User", "user_name")
            my_password = st.text_input("SQL Password", "password", type="password")

            endpoint = my_endpoint
            database = my_database
            user = my_user
            password = my_password
        
    # ---------------------------------- #
    if "login_token" not in st.session_state:	 	 	 	 
        st.session_state.login_token = None

    st.session_state.login_token = msal_auth.get_token()
    if st.session_state.login_token is not None:
        username = st.session_state.login_token["account"]["name"]
        email = st.session_state.login_token["account"]["username"]
        st.write(f"Welcome, {username} ({email}) !")

        endpoint = os.getenv("AZURE_SQL_ENDPOINT")
        database = os.getenv("AZURE_SQL_DATABASE")
        user = os.getenv("AZURE_SQL_USER")
        password = os.getenv("AZURE_SQL_PASSWORD")

        # some sample questions that can be asked
        questions = [
            "What are the top 5 selling products? Display quantity sold and revenue",
            "How many products are there in each category?",
            "What is the total sales for each product category, ordered by total sales?",
            "Give me a list of the top 5 categories (id, name and count) where there are more than 10 products, from larger to smaller",
            "Affiche le top 10 des produits les plus vendus (catégorie, produit, quantité vendue et chiffre d'affaires)",

        ]

        questions

        user_prompt = st.text_input("1. Type something...")        
        
        if st.button("Submit query"):
                
            # connect to Azure SQL database 
            with sqldb.AzureSQLDatabase(
                server=endpoint, 
                database=database, 
                username=user, 
                password=password) as db:
                result = db.connect()

                if(result != "OK"):
                    st.write(result)
                    return

                # get table definitions from database
                table_definitions = db.get_table_definitions_for_prompt()

                # create capitalized references to table definitions and response format
                user_prompt = llm.add_cap_ref(
                    user_prompt,
                    prompts.SQL_TABLE_DEFINITIONS_CAP_REF_PROMPT, 
                    prompts.SQL_TABLE_DEFINITIONS_CAP_REF,
                    table_definitions,
                )

                user_prompt = llm.add_cap_ref(
                    user_prompt, 
                    prompts.RESPONSE_FORMAT_CAP_REF_PROMPT, 
                    prompts.RESPONSE_FORMAT_CAP_REF, 
    f"""
    \nExplanation: <explanation of the query>
    \n{prompts.SQL_DELIMITER}
    \n<sql query exclusively as raw text>
    """

                )
                st.write("### Prompt sent to Azure OpenAI:\n", user_prompt)

                # Send prompt to Azure OpenAI and get a response
                prompt_response = llm.prompt(user_prompt)
                st.write("### Prompt response:\n", prompt_response)

                # extract sql query code from prompt_response 
                st.write("### SQL Query that was generated:\n\n")
                sql_query = prompt_response.split(prompts.SQL_DELIMITER)[1].strip()

                # display sql query as code
                st.code(sql_query, language="sql")

                # run the query
                json_results = db.run_sql(sql_query)

                # display results
                st.table(json_results)

if __name__ == "__main__":

    page_title="Query any SQL database using NLP"
    st.set_page_config(page_title=page_title, page_icon="💡")
    st.write(f"## 💡{page_title}")

    main()
