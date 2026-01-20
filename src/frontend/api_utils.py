import requests
import streamlit as st
import os
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost/api").rstrip("/")


def get_api_response(question, session_id, model):
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }
    data = {
        "question": question,
        "model": model
    }
    if session_id:
        data["session_id"] = session_id

    try:
        response = requests.post(f"{API_BASE_URL}/chat", headers=headers, json=data)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API request failed with status code {response.status_code}: {response.text}")
            return None
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return None

def upload_document(file):
    print("Uploading file...")
    try:
        files = {"file": (file.name, file, file.type)}
        response = requests.post(f"{API_BASE_URL}/upload-doc", files=files)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to upload file. Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"An error occurred while uploading the file: {str(e)}")
        return None

def list_documents():
    try:
        response = requests.get(f"{API_BASE_URL}/list-docs")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch document list. Error: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        st.error(f"An error occurred while fetching the document list: {str(e)}")
        return []

def delete_document(file_id):
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }
    data = {"file_id": file_id}

    try:
        response = requests.post(f"{API_BASE_URL}/delete-doc", headers=headers, json=data)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to delete document. Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"An error occurred while deleting the document: {str(e)}")
        return None 
    
    
def summarize_documents(file_ids):
    try:
        data = {"file_ids": file_ids, "model": "gpt-4o-mini"}

        response = requests.post(f"{API_BASE_URL}/summarize-docs", json=data)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to summarize documents. Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"An error occurred while summarizing the documents: {str(e)}")
        return None
    

import requests

def generate_insights(file_ids, question):
    try:
        data = {"file_ids": file_ids, "question": question}
        response = requests.post(f"{API_BASE_URL}/insights", json=data)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"An error occurred while generating insights: {str(e)}")
        return None