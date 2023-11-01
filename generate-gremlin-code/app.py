import openai
import streamlit as st
from dotenv import load_dotenv
from gremlin_python.driver import client, serializer

import os

load_dotenv()
openai.api_type = os.getenv("OPENAI_API_TYPE")
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_version = os.getenv("OPENAI_API_VERSION")
openai.api_base = os.getenv("OPENAI_API_BASE")

endpoint = os.getenv("COSMOSDB_GREMLIN_ENDPOINT")
database = os.getenv("COSMOSDB_GREMLIN_DATABASE_NAME")
collection = os.getenv("COSMOSDB_GREMLIN_COLLECTION_NAME")
password = f'{os.getenv("COSMOSDB_GREMLIN_KEY")}'

title = "Generate Gremlin code"
st.set_page_config(page_title=title, page_icon="👻")

def get_completion(context="", prompt="", max_tokens=400, model=os.getenv("OPENAI_MODEL")):
    response = openai.Completion.create(
        engine=model,
        prompt=f"""
        Context:

        {context}
        ----------------
        {prompt}
        """,
        temperature=1,
        max_tokens=max_tokens,
        top_p=0.5,
        frequency_penalty=0,
        presence_penalty=0,
        stop=["Query:"]
    )

    return response['choices'][0]['text'].encode().decode()

# ----------------------------------------------    

title = "Generate Gremlin code"
styles = """
            <style>
            .green { color: green }
            .red { color: red }
            .bold { font-weight: bold }
            </style>
            """
st.markdown(styles, unsafe_allow_html=True)
st.header(title)

st.write("#### Sample queries")

context = '''
You are an assistant to a data scientist. You are given a graph database with nodes and edges. You are asked to write queries that answer user requests in natural language. The query should be written in Gremlin.

Here is an example of the queries used to populate the graph database:
g.V().drop()
g.addV('PU').property('id', 'PU_RE22_019').property('name', 'PU_RE22_019').property('nickname', '').property('mileage', 1).property('project', 'RE22').property('pk', 'PU_RE22_019')
g.addV('PU').property('id', 'PU_RE22_039').property('name', 'PU_RE22_039').property('nickname', '').property('mileage', 2).property('project', 'RE22').property('pk', 'PU_RE22_039')
g.addV('PU').property('id', 'PU_RE22_041').property('name', 'PU_RE22_41').property('nickname', '').property('mileage', 3).property('project', 'RE22').property('pk', 'PU_RE22_41')
g.addV('PU').property('id', 'PU_RE22_038').property('name', 'PU_RE22_038').property('nickname', 'RE22_BEN014').property('mileage', 4).property('project', 'RE22').property('pk', 'PU_RE22_038')
g.addV('Element').property('id', 'TT0222-027').property('name', 'TT0222-027').property('mileage', 12).property('pk', 'TT0222-027')
g.addV('Element').property('id', 'TT0222-015').property('name', 'TT0222-015').property('mileage', 13).property('pk', 'TT0222-015')
g.addV('Element').property('id', 'TT0021-104').property('name', 'TT0021-104').property('mileage', 22).property('pk', 'TT0021-104')
g.addV('Part').property('id', 'HTV02317').property('name', 'HTV02317').property('Type', 'Carter Support RTT').property('pk', 'HTV02317')
g.V('PU_RE22_019').addE('contains').to(g.V('TT0222-027'))
g.V('PU_RE22_039').addE('contains').to(g.V('TT0222-027'))
g.V('PU_RE22_041').addE('contains').to(g.V('TT0222-027'))
g.V('PU_RE22_038').addE('contains').to(g.V('TT0222-027')).property('StartTime', '2022-02-08 00:00:00').property('Endtime', '2022-06-14 00:00:00')
g.V('PU_RE22_038').addE('contains').to(g.V('TT0222-015')).property('StartTime', '2022-06-15 00:00:00').property('Endtime', '2022-06-21 00:00:00')
g.V('TT0222-015').addE('contains').to(g.V('HTV02317')).property('StartTime', '2022-01-10 00:00:00').property('Endtime', '2022-06-21 00:00:00')
g.V('TT0021-104').addE('contains').to(g.V('HTV02317')).property('StartTime', '2022-09-06 00:00:00')
'''
sample_queries = [
    "Count the number of nodes in the graph",
    "Get everything related to element TT0222-027",
    "Show me all parts with a StartTime before 2022-06-01",
    "Show me all parts with a StartTime between 2022-01-01 and 2022-12-31"
]

if st.button("Populate graph database with sample data"):
    queries = [
    "g.addV('PU').property('id', 'PU_RE22_019').property('name', 'PU_RE22_019').property('nickname', '').property('mileage', 1).property('project', 'RE22').property('pk', 'PU_RE22_019')",
    "g.addV('PU').property('id', 'PU_RE22_039').property('name', 'PU_RE22_039').property('nickname', '').property('mileage', 2).property('project', 'RE22').property('pk', 'PU_RE22_039')",
    "g.addV('PU').property('id', 'PU_RE22_041').property('name', 'PU_RE22_41').property('nickname', '').property('mileage', 3).property('project', 'RE22').property('pk', 'PU_RE22_41')",
    "g.addV('PU').property('id', 'PU_RE22_038').property('name', 'PU_RE22_038').property('nickname', 'RE22_BEN014').property('mileage', 4).property('project', 'RE22').property('pk', 'PU_RE22_038')",
    "g.addV('Element').property('id', 'TT0222-027').property('name', 'TT0222-027').property('mileage', 12).property('pk', 'TT0222-027')",
    "g.addV('Element').property('id', 'TT0222-015').property('name', 'TT0222-015').property('mileage', 13).property('pk', 'TT0222-015')",
    "g.addV('Element').property('id', 'TT0021-104').property('name', 'TT0021-104').property('mileage', 22).property('pk', 'TT0021-104')",
    "g.addV('Part').property('id', 'HTV02317').property('name', 'HTV02317').property('Type', 'Carter Support RTT').property('pk', 'HTV02317')",
    "g.V('PU_RE22_019').addE('contains').to(g.V('TT0222-027'))",
    "g.V('PU_RE22_039').addE('contains').to(g.V('TT0222-027'))",
    "g.V('PU_RE22_041').addE('contains').to(g.V('TT0222-027'))",
    "g.V('PU_RE22_038').addE('contains').to(g.V('TT0222-027')).property('StartTime', '2022-02-08 00:00:00').property('Endtime', '2022-06-14 00:00:00')",
    "g.V('PU_RE22_038').addE('contains').to(g.V('TT0222-015')).property('StartTime', '2022-06-15 00:00:00').property('Endtime', '2022-06-21 00:00:00')",
    "g.V('TT0222-015').addE('contains').to(g.V('HTV02317')).property('StartTime', '2022-01-10 00:00:00').property('Endtime', '2022-06-21 00:00:00')",
    "g.V('TT0021-104').addE('contains').to(g.V('HTV02317')).property('StartTime', '2022-09-06 00:00:00')",
    ]
    gremlin_client = client.Client(
                        url=endpoint, 
                        traversal_source='g',
                        username=f"/dbs/{database}/colls/{collection}",
                        password=password,
                        message_serializer=serializer.GraphSONSerializersV2d0()
    );

    # Drop graph
    gremlin_client.submit("g.V().drop()");

    # sleep for 2 seconds to allow the database to be cleared
    import time
    time.sleep(2)

    for query in queries:
        st.code(query, language="Gremlin")
        results = gremlin_client.submit(query); 

st.json(sample_queries, expanded = False)
search_text = st.text_input("Your query:", placeholder="Ask me anything")

if st.button("Run query"):

    st.write("#### Gremlin code generated by Azure OpenAI")
    query_text = get_completion(context=context, prompt=search_text, model=os.getenv("OPENAI_MODEL"))
    st.code(query_text, language="Gremlin")

    gremlin_client = client.Client(
                        url=endpoint, 
                        traversal_source='g',
                        username=f"/dbs/{database}/colls/{collection}",
                        password=password,
                        message_serializer=serializer.GraphSONSerializersV2d0()
    );

    results = gremlin_client.submit(query_text);    
    
    # Process and print the results
    for result in results:
        st.write(result)
    
    
