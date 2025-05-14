import streamlit as st
import boto3
import os
import time
import tempfile
import msal
import requests
from io import BytesIO
from botocore.exceptions import NoCredentialsError, ClientError

# Set page config
st.set_page_config(
    page_title="S3 to OneDrive Transfer",
    page_icon="🔄",
    layout="wide"
)

# App title and description
st.title("S3 to OneDrive File Transfer")
st.markdown("Transfer files from Amazon S3 to Microsoft OneDrive easily.")

# Create sidebar for configuration
st.sidebar.header("Configuration")

# AWS Credentials
st.sidebar.subheader("AWS Configuration")
aws_access_key = st.sidebar.text_input("AWS Access Key ID", type="password")
aws_secret_key = st.sidebar.text_input("AWS Secret Access Key", type="password")
aws_region = st.sidebar.text_input("AWS Region", value="us-east-1")

# Microsoft Graph API Configuration
st.sidebar.subheader("Microsoft Graph API Configuration")
tenant_id = st.sidebar.text_input("Azure AD Tenant ID", type="password")
client_id = st.sidebar.text_input("Application (Client) ID", type="password")
client_secret = st.sidebar.text_input("Client Secret", type="password")

# Connect to S3
def connect_to_s3():
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region
        )
        return s3_client
    except Exception as e:
        st.error(f"Error connecting to S3: {str(e)}")
        return None

# Get all S3 buckets
def get_s3_buckets(s3_client):
    try:
        response = s3_client.list_buckets()
        buckets = [bucket['Name'] for bucket in response['Buckets']]
        return buckets
    except NoCredentialsError:
        st.error("AWS credentials not available")
        return []
    except Exception as e:
        st.error(f"Error listing S3 buckets: {str(e)}")
        return []

# List objects in a bucket
def list_s3_objects(s3_client, bucket_name, prefix=""):
    try:
        objects = []
        continuation_token = None
        while True:
            if continuation_token:
                response = s3_client.list_objects_v2(
                    Bucket=bucket_name,
                    Prefix=prefix,
                    ContinuationToken=continuation_token
                )
            else:
                response = s3_client.list_objects_v2(
                    Bucket=bucket_name,
                    Prefix=prefix
                )
                
            if 'Contents' in response:
                for obj in response['Contents']:
                    if not obj['Key'].endswith('/'):  # Skip folders
                        objects.append({
                            'Key': obj['Key'],
                            'Size': obj['Size'],
                            'LastModified': obj['LastModified']
                        })
            
            if not response.get('IsTruncated'):
                break
            
            continuation_token = response.get('NextContinuationToken')
        
        return objects
    except Exception as e:
        st.error(f"Error listing objects in bucket {bucket_name}: {str(e)}")
        return []

# Generate Microsoft Graph API access token
def get_ms_graph_token():
    try:
        # Define Microsoft Graph API auth parameters
        authority = f"https://login.microsoftonline.com/{tenant_id}"
        scope = ["https://graph.microsoft.com/.default"]
        
        # Create MSAL app
        app = msal.ConfidentialClientApplication(
            client_id=client_id,
            client_credential=client_secret,
            authority=authority
        )
        
        # Get token
        result = app.acquire_token_for_client(scopes=scope)
        
        if "access_token" in result:
            return result["access_token"]
        else:
            st.error(f"Error getting Microsoft Graph token: {result.get('error_description', '')}")
            return None
    except Exception as e:
        st.error(f"Error in Microsoft Graph authentication: {str(e)}")
        return None

# List OneDrive drives
def list_onedrive_drives(token):
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Get the user's drives
        response = requests.get(
            "https://graph.microsoft.com/v1.0/me/drives",
            headers=headers
        )
        
        if response.status_code == 200:
            drives = response.json().get("value", [])
            return drives
        else:
            st.error(f"Error listing OneDrive drives: {response.text}")
            return []
    except Exception as e:
        st.error(f"Error listing OneDrive drives: {str(e)}")
        return []

# List OneDrive folders
def list_onedrive_folders(token, drive_id, item_id="root"):
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Get children of the specified folder
        url = f"https://graph.microsoft.com/v1.0/me/drives/{drive_id}/items/{item_id}/children"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            items = response.json().get("value", [])
            folders = [item for item in items if "folder" in item]
            return folders
        else:
            st.error(f"Error listing OneDrive folders: {response.text}")
            return []
    except Exception as e:
        st.error(f"Error listing OneDrive folders: {str(e)}")
        return []

# Upload file to OneDrive
def upload_to_onedrive(token, drive_id, folder_id, file_name, file_content):
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/octet-stream"
        }
        
        # URL for uploading a file
        url = f"https://graph.microsoft.com/v1.0/me/drives/{drive_id}/items/{folder_id}:/{file_name}:/content"
        
        # Upload the file
        response = requests.put(url, headers=headers, data=file_content)
        
        if response.status_code in [200, 201]:
            return True, response.json()
        else:
            return False, f"Error uploading file: {response.text}"
    except Exception as e:
        return False, f"Error uploading file: {str(e)}"

# S3 to OneDrive transfer function
def transfer_s3_to_onedrive(s3_client, token, bucket_name, object_key, drive_id, folder_id):
    try:
        # Download file from S3
        response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        file_content = response['Body'].read()
        
        # Get the filename from the object key
        file_name = os.path.basename(object_key)
        
        # Upload to OneDrive
        success, result = upload_to_onedrive(token, drive_id, folder_id, file_name, file_content)
        return success, result
    except Exception as e:
        return False, f"Error transferring file: {str(e)}"

# Main application logic
def main():
    # Initialize session state for storing selected values
    if 'selected_bucket' not in st.session_state:
        st.session_state.selected_bucket = None
    if 'selected_drive' not in st.session_state:
        st.session_state.selected_drive = None
    if 'selected_folder' not in st.session_state:
        st.session_state.selected_folder = None
    if 'transferred_files' not in st.session_state:
        st.session_state.transferred_files = []
    
    # Connect to S3 if credentials are provided
    s3_client = None
    if aws_access_key and aws_secret_key:
        s3_client = connect_to_s3()
    
    # Get Microsoft Graph token if credentials are provided
    ms_token = None
    if tenant_id and client_id and client_secret:
        ms_token = get_ms_graph_token()
    
    # Create two columns for S3 and OneDrive
    col1, col2 = st.columns(2)
    
    # S3 Section
    with col1:
        st.header("Amazon S3")
        
        if s3_client:
            # List S3 buckets
            buckets = get_s3_buckets(s3_client)
            if buckets:
                selected_bucket = st.selectbox("Select S3 Bucket", buckets)
                st.session_state.selected_bucket = selected_bucket
                
                # List objects in the selected bucket
                if st.session_state.selected_bucket:
                    prefix = st.text_input("Prefix (optional)", value="")
                    s3_objects = list_s3_objects(s3_client, st.session_state.selected_bucket, prefix)
                    
                    if s3_objects:
                        # Create a table to display objects
                        object_df = {
                            "File": [obj['Key'] for obj in s3_objects],
                            "Size (KB)": [f"{obj['Size']/1024:.2f}" for obj in s3_objects],
                            "Last Modified": [obj['LastModified'].strftime("%Y-%m-%d %H:%M:%S") for obj in s3_objects]
                        }
                        
                        # Allow selection of files
                        selected_objects = st.multiselect(
                            "Select files to transfer",
                            object_df["File"]
                        )
                    else:
                        st.info("No objects found in this bucket with the specified prefix.")
                        selected_objects = []
                else:
                    selected_objects = []
            else:
                st.warning("No S3 buckets found. Check your credentials or create a bucket.")
                selected_objects = []
        else:
            st.warning("Enter AWS credentials to connect to S3.")
            selected_objects = []
    
    # OneDrive Section
    with col2:
        st.header("Microsoft OneDrive")
        
        if ms_token:
            # List OneDrive drives
            drives = list_onedrive_drives(ms_token)
            if drives:
                drive_options = {f"{drive['name']} ({drive['id']})": drive['id'] for drive in drives}
                selected_drive_name = st.selectbox("Select OneDrive", list(drive_options.keys()))
                selected_drive_id = drive_options[selected_drive_name]
                st.session_state.selected_drive = selected_drive_id
                
                # List folders in the selected drive
                if st.session_state.selected_drive:
                    folders = list_onedrive_folders(ms_token, st.session_state.selected_drive)
                    
                    # Add the root folder option
                    folder_options = {"Root": "root"}
                    folder_options.update({f"{folder['name']} ({folder['id']})": folder['id'] for folder in folders})
                    
                    selected_folder_name = st.selectbox("Select destination folder", list(folder_options.keys()))
                    selected_folder_id = folder_options[selected_folder_name]
                    st.session_state.selected_folder = selected_folder_id
                else:
                    st.info("Select a drive to see available folders.")
            else:
                st.warning("No OneDrive drives found. Check your Microsoft credentials.")
        else:
            st.warning("Enter Microsoft Graph API credentials to connect to OneDrive.")
    
    # Transfer section
    st.header("Transfer Files")
    
    transfer_button = st.button("Transfer Selected Files")
    
    if transfer_button and selected_objects and st.session_state.selected_bucket and st.session_state.selected_drive and st.session_state.selected_folder:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        st.session_state.transferred_files = []
        total_files = len(selected_objects)
        
        for i, obj_key in enumerate(selected_objects):
            status_text.text(f"Transferring {i+1}/{total_files}: {obj_key}")
            
            # Transfer the file
            success, result = transfer_s3_to_onedrive(
                s3_client, 
                ms_token, 
                st.session_state.selected_bucket, 
                obj_key, 
                st.session_state.selected_drive, 
                st.session_state.selected_folder
            )
            
            if success:
                st.session_state.transferred_files.append({
                    "file": obj_key,
                    "status": "Success",
                    "details": "File transferred successfully"
                })
            else:
                st.session_state.transferred_files.append({
                    "file": obj_key,
                    "status": "Failed",
                    "details": result
                })
            
            # Update progress
            progress_bar.progress((i + 1) / total_files)
            
        status_text.text(f"Transfer completed. {len([f for f in st.session_state.transferred_files if f['status'] == 'Success'])}/{total_files} files transferred successfully.")
    
    # Transfer history/results
    if st.session_state.transferred_files:
        st.header("Transfer Results")
        
        for file_result in st.session_state.transferred_files:
            if file_result["status"] == "Success":
                st.success(f"✅ {file_result['file']}: {file_result['details']}")
            else:
                st.error(f"❌ {file_result['file']}: {file_result['details']}")

if __name__ == "__main__":
    main()