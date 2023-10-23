from msal_streamlit_authentication import msal_authentication
import os
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

def get_token():
    tenant_id = os.getenv('TENANT_ID')
    client_id = os.getenv('APP_CLIENT_ID')
    login_token = msal_authentication(
        auth={
            "clientId": client_id,
            "authority": f"https://login.microsoftonline.com/{tenant_id}",
            "redirectUri": "/",
            "postLogoutRedirectUri": "/"
        }, # Corresponds to the 'auth' configuration for an MSAL Instance
        cache={
            "cacheLocation": "sessionStorage",
            "storeAuthStateInCookie": False
        }, # Corresponds to the 'cache' configuration for an MSAL Instance
        login_request={
            "scopes": ["openid"]
        }, # Optional
        logout_request={}, # Optional
        login_button_text="Login", # Optional, defaults to "Login"
        logout_button_text="Logout", # Optional, defaults to "Logout"
    )
    # st.write("token=", login_token)
    return login_token