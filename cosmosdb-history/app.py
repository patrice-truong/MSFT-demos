from bing import BingSearchTool, run_agent
from callbacks import StdOutCallbackHandler
from langchain.memory import ConversationBufferMemory
from langchain.memory.chat_message_histories import StreamlitChatMessageHistory
from langchain.chat_models import AzureChatOpenAI
from langchain.memory import CosmosDBChatMessageHistory
from langchain.callbacks.manager import CallbackManager
from langchain.agents import ConversationalChatAgent, AgentExecutor, Tool
from langchain.memory import ConversationBufferWindowMemory

import openai, os, random
import streamlit as st
from dotenv import load_dotenv
from datetime import datetime
from prompts import CUSTOM_CHATBOT_PREFIX, CUSTOM_CHATBOT_SUFFIX
from utils import get_token
from base64 import b64decode

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_base = os.getenv("OPENAI_API_BASE")
openai.api_type  = os.getenv("OPENAI_API_TYPE")
openai.api_version = os.getenv("OPENAI_API_VERSION")

st.set_page_config(page_title="Bing Chat with Cosmos DB history", page_icon="📖")
st.title("Bing Chat with Cosmos DB history")

"""
An example of using the Bing search API with Langchain.
Conversation history is stored in Cosmos DB for NoSQL database.
"""

cosmos_endpoint = f"https://{os.getenv('AZURE_COSMOSDB_ACCOUNT')}.documents.azure.com:443/"
cosmos_key = os.getenv('AZURE_COSMOSDB_KEY')
cosmos_database = os.getenv('AZURE_COSMOSDB_NAME')
cosmos_container = os.getenv('AZURE_COSMOSDB_CONTAINER_NAME')
cosmos_connection_string = f"AccountEndpoint={cosmos_endpoint};AccountKey={cosmos_key}"

# st.write(cosmos_endpoint )
# st.write(cosmos_key)
# st.write(cosmos_database )
# st.write(cosmos_container)
# st.write(cosmos_connection_string)

if "langchain_messages" not in st.session_state:
    st.session_state.langchain_messages = []
    
login_token = get_token()
if login_token is not None:
    username = login_token["account"]["name"]
    email = login_token["account"]["username"]
    st.write(f"Welcome, {username} ({email}) !")

    current_dt = str(datetime.now().strftime("%Y%m%d_%H%M%S"))

    cosmos = CosmosDBChatMessageHistory(
        cosmos_endpoint=cosmos_endpoint,
        cosmos_database=cosmos_database,
        cosmos_container=cosmos_container,
        connection_string=cosmos_connection_string,
        session_id=current_dt,
        user_id=email
        )
    # prepare the cosmosdb instance
    cosmos.prepare_cosmos()

    # Set up memory
    msgs = StreamlitChatMessageHistory(key="langchain_messages")

    view_messages = st.expander("View the message contents in session state")

    questions = [
        "Tell me about important events in October 2023",
        "Who won the Rugby World Cup in 2023?"
    ]

    questions

    llm = AzureChatOpenAI(
        deployment_name=os.getenv("OPENAI_API_MODEL"), 
        temperature=0, 
        max_tokens=500
    )

    # BingSearchAPIWrapper is a langchain Tool class to use the Bing Search API (https://www.microsoft.com/en-us/bing/apis/bing-web-search-api)
    cb_handler = StdOutCallbackHandler()
    cb_manager = CallbackManager(handlers=[cb_handler])

    bing_search = BingSearchTool(
        llm=llm, 
        k=5, 
        callback_manager=cb_manager, 
        return_direct=True
    )

    tools = [bing_search]

    agent = ConversationalChatAgent.from_llm_and_tools(
        llm=llm, 
        tools=tools, 
        system_message=CUSTOM_CHATBOT_PREFIX, 
        human_message=CUSTOM_CHATBOT_SUFFIX
    )

    memory = ConversationBufferWindowMemory(
        memory_key="chat_history", 
        return_messages=True, 
        k=10, 
        chat_memory=cosmos
    )

    agent_chain = AgentExecutor.from_agent_and_tools(
        agent=agent, 
        tools=tools, 
        memory=memory
    )

    # Render current messages from StreamlitChatMessageHistory
    memory.chat_memory.messages = msgs.messages
    for msg in msgs.messages:
        st.chat_message(msg.type).markdown(msg.content, unsafe_allow_html=True)

    # If user inputs a new prompt, generate and draw a new response
    if prompt := st.chat_input():
        st.chat_message("human").markdown(prompt, unsafe_allow_html=True)

        with st.spinner("Please wait.."):
            response = run_agent(prompt, agent_chain)
            st.chat_message("ai").markdown(response, unsafe_allow_html=True)

    # Draw the messages at the end, so newly generated ones show up immediately
    with view_messages:
        """
        Memory initialized with:
        ```python
        msgs = StreamlitChatMessageHistory(key="langchain_messages")
        memory = ConversationBufferMemory(chat_memory=msgs)
        ```

        Contents of `st.session_state.langchain_messages`:
        """
        view_messages.json(st.session_state.langchain_messages)