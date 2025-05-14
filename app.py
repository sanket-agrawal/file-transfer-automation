import streamlit as st
from auth import authenticate_onedrive
from onedrive_handler import list_onedrive_files, download_onedrive_file
from aws_handler import get_s3_client, upload_stream_to_s3
import os

st.title("📤 Move Files from OneDrive to AWS S3")

access_token = authenticate_onedrive()
onedrive_files = list_onedrive_files(access_token)
s3_client = get_s3_client()
bucket = os.getenv("S3_BUCKET")

file_names = [f["name"] for f in onedrive_files]
selected = st.multiselect("Select files to transfer", file_names)

if st.button("Transfer Selected Files"):
    for file in onedrive_files:
        if file["name"] in selected:
            st.write(f"📥 Downloading `{file['name']}` from OneDrive...")
            stream = download_onedrive_file(access_token, file["id"]).raw

            st.write(f"☁️ Uploading to S3 `{file['name']}`...")
            upload_stream_to_s3(s3_client, bucket, file["name"], stream)
            st.success(f"✅ `{file['name']}` uploaded successfully.")
