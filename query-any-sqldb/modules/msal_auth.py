from msal_streamlit_authentication import msal_authentication
import os

def get_token():
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
    return login_token