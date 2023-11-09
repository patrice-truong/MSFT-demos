from bing import BingSearchTool
from callbacks import StdOutCallbackHandler
from langchain.memory import ConversationBufferMemory
from langchain.memory.chat_message_histories import StreamlitChatMessageHistory
from langchain.chat_models import AzureChatOpenAI
from langchain.callbacks.manager import CallbackManager

import openai, os, requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_base = os.getenv("OPENAI_API_BASE")
openai.api_type  = os.getenv("OPENAI_API_TYPE")
openai.api_version = os.getenv("OPENAI_API_VERSION")

def get_token():

    from msal_streamlit_authentication import msal_authentication
    from dotenv import load_dotenv

    load_dotenv()

    login_token = msal_authentication(
        auth={
            "clientId": os.getenv("AZURE_CLIENT_ID"),
            "authority": f"https://login.microsoftonline.com/common",
            "redirectUri": "/",
            "postLogoutRedirectUri": "/"
        }, 
        cache={
            "cacheLocation": "sessionStorage",
            "storeAuthStateInCookie": False
        }, 
        login_request={
            "scopes": ["openid"]
        }
    )
    # st.write("token=", login_token)
    return login_token

if __name__ == "__main__":
    title = "Langchain with Bing"
    st.set_page_config(page_title=title, page_icon="📖")
    st.title(title)

    """
    An example of using the  Bing search API with Langchain
    """

    if "login_token" not in st.session_state:	 	 	 	 
        st.session_state.login_token = None
    
    st.session_state.login_token = get_token()
        
    # ---------------------------------- #
    if st.session_state.login_token is not None:
        username = st.session_state.login_token["account"]["name"]
        email = st.session_state.login_token["account"]["username"]
        st.write(f"Welcome, {username} ({email}) !")    
    
        # Set up memory
        msgs = StreamlitChatMessageHistory(key="langchain_messages")
        memory = ConversationBufferMemory(chat_memory=msgs)

        view_messages = st.expander("View the message contents in session state")


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


        # Render current messages from StreamlitChatMessageHistory
        for msg in msgs.messages:
            st.chat_message(msg.type).markdown(msg.content)

        # If user inputs a new prompt, generate and draw a new response
        if prompt := st.chat_input():
            st.chat_message("human").markdown(prompt)
            msgs.add_user_message(prompt)

            with st.spinner("Generating response..."):
                response = bing_search.run(prompt)
                
                st.chat_message("ai").markdown(response, unsafe_allow_html=True)
                msgs.add_ai_message(response)

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