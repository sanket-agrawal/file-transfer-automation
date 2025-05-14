import requests

GRAPH_URL = "https://graph.microsoft.com/v1.0"

def list_onedrive_files(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"{GRAPH_URL}/me/drive/root/children"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json().get("value", [])

def download_onedrive_file(access_token, item_id):
    headers = {"Authorization": f"Bearer {access_token}"}
    download_url = f"{GRAPH_URL}/me/drive/items/{item_id}/content"
    return requests.get(download_url, headers=headers, stream=True)
