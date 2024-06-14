import streamlit as st
import os, time
from dotenv import load_dotenv
from openai import AzureOpenAI
from tenacity import retry, wait_random_exponential, stop_after_attempt

@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(10))
def generate_embeddings(text):
    """
    Generates embeddings for a given text using the OpenAI API v1.x
    """
    openai_client = AzureOpenAI(
        api_key = os.getenv("AZURE_OPENAI_API_KEY"),  
        api_version = os.getenv("AZURE_OPENAI_API_VERSION"),  
        azure_endpoint =os.getenv("AZURE_OPENAI_ENDPOINT") 
    )

    response = openai_client.embeddings.create(
        input = text,
        model= os.getenv("AZURE_OPENAI_EMBEDDING_MODEL")
    )
    
    embeddings = response.data[0].embedding
    return embeddings

def get_completion(model, prompt: str):
    openai_client = AzureOpenAI(
        api_key = os.getenv("AZURE_OPENAI_API_KEY"),  
        api_version = os.getenv("AZURE_OPENAI_API_VERSION"),  
        azure_endpoint =os.getenv("AZURE_OPENAI_ENDPOINT") 
    )

    start_time = time.time()
    response = openai_client.chat.completions.create(
        model = model,
        messages = [{"role": "user", "content": prompt}]
    )   
    end_time = time.time()
    elapsed_time = end_time - start_time
    return response.choices[0].message.content, elapsed_time

def vector_search(query_text, limit):
    from cosmosdb_nosql import CosmosDBNoSQLService

    opts = dict()
    opts['url'] = os.getenv('AZURE_COSMOSDB_NOSQL_ENDPOINT')
    opts['key'] = os.getenv('AZURE_COSMOSDB_NOSQL_KEY')
    c = CosmosDBNoSQLService(opts)
    c.set_db(os.getenv('AZURE_COSMOSDB_NOSQL_DATABASE'))
    c.set_container(os.getenv('AZURE_COSMOSDB_NOSQL_CONTAINER'))

    # get similar docs from Cosmos DB for NoSQL
    query_vector = generate_embeddings(query_text)
    recipes = c.vector_search(query_vector, limit)
    return recipes

def main():      
    title = "Cosmos DB for NoSQL Vector Search"
    st.set_page_config(page_title=title, layout="wide")

    st.header(title)

    load_dotenv()

    # Names of models that are deployed in the Azure OpenAI accounts
    models = [
        "gpt-35-turbo-16k",
        "gpt-4o",
        "gpt-4"
    ]

    model = st.sidebar.selectbox(
        'Chat model',
        (models))
    
    st.sidebar.write("Recipes dataset: https://www.kaggle.com/datasets/wilmerarltstrmberg/recipe-dataset-over-2m")
    
    questions = [
"Suggest 3 French recipes that use garlic",
"Suggest 4 cookie recipes",
"Suggest 3 recipes that I can cook with flour and sugar",
    ]

    questions    

    query = st.text_input("What would you like to cook?")
    top_k = st.sidebar.slider('Number of docs to consider', 0, 50, 20)
    st.sidebar.write("top k:", top_k)

    if st.button("Find recipes"):
        with st.spinner("Please wait.."):
            docs, elapsed_time = vector_search(query, top_k)
            st.markdown(f"### {top_k} docs retrieved from Cosmos DB for NoSQL in {elapsed_time:.2f} seconds")
            docs

            # add docs to user prompt and use GPT model to generate response
            st.markdown("### Generating answer with AOAI..")
            user_prompt = f"""
        Using the following CONTEXT, answer the user's question as best as possible. 
        - Answer in English
        - Answer in markdown format

        CONTEXT:
        {docs}

        USER QUESTION:
        {query}

        ANSWER:
        **{{ title }}**
        
        **Ingredients:**
        {{ ingredients}}

        **Instructions*:*
        {{ instructions }}

        """            
            response, completion_time = get_completion(model, user_prompt)
            st.markdown(f"### Answer: in {completion_time:.2f} seconds")
            response
    



if __name__ == "__main__":
    main()

