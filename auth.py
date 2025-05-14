import os
from msal import PublicClientApplication
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

CLIENT_ID = os.getenv("ONEDRIVE_CLIENT_ID")
TENANT_ID = os.getenv("ONEDRIVE_TENANT_ID")
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPES = ["Files.Read.All", "offline_access"]

@st.cache_resource
def authenticate_onedrive():
    app = PublicClientApplication(CLIENT_ID, authority=AUTHORITY)
    flow = app.initiate_device_flow(scopes=SCOPES)
    if "user_code" not in flow:
        raise Exception("Device code flow initiation failed")

    st.info(f"👉 Visit [https://microsoft.com/devicelogin](https://microsoft.com/devicelogin) and enter code: `{flow['user_code']}`")
    result = app.acquire_token_by_device_flow(flow)
    return result["access_token"]
