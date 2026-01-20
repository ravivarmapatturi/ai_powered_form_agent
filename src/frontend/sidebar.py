import streamlit as st
from api_utils import upload_document, list_documents, delete_document ,summarize_documents

def display_sidebar():
    st.sidebar.header("Upload Forms")

    uploaded_files = st.sidebar.file_uploader(
        "Choose files",
        type=["pdf", "docx", "html", "jpg", "jpeg", "png", "tiff", "tif"],
        accept_multiple_files=True
    )

    # Initialize document list if not present
    if "documents" not in st.session_state:
        st.session_state.documents = list_documents()

    documents = st.session_state.documents

    if uploaded_files:
        st.sidebar.write(f"Selected {len(uploaded_files)} file(s)")

        if st.sidebar.button("Upload All"):
            with st.spinner("Uploading..."):
                for uploaded_file in uploaded_files:
                    existing_doc = next(
                        (doc for doc in documents if doc["filename"] == uploaded_file.name),
                        None
                    )

                    if existing_doc:
                        st.sidebar.info(
                            f"'{uploaded_file.name}' already uploaded. Using existing ID: {existing_doc['id']}"
                        )
                        continue

                    upload_response = upload_document(uploaded_file)
                    if upload_response:
                        st.sidebar.success(
                            f"Uploaded '{uploaded_file.name}' (ID: {upload_response['file_id']})"
                        )
                    else:
                        st.sidebar.error(f"Failed to upload '{uploaded_file.name}'")

                # Refresh list after all uploads
                st.session_state.documents = list_documents()

            st.rerun()


    # Sidebar: List Documents
    st.sidebar.header("Summarize")

    if "summary_results" not in st.session_state:
        st.session_state.summary_results = {}

    if documents:
        selected_doc_ids = st.sidebar.select(
            "Select documents to summarize",
            options=[doc["id"] for doc in documents],
            format_func=lambda x: next(doc["filename"] for doc in documents if doc["id"] == x)
        )

        if st.sidebar.button("Summarize Uploaded Documents.."):
            if not selected_doc_ids:
                st.sidebar.warning("Please select a document.")
            else:
                with st.spinner("Summarizing..."):
                    summary_response = summarize_documents(selected_doc_ids)  # pass list
                    st.session_state.summary_results = summary_response

                st.sidebar.success("Summaries generated!")

    else:
        st.sidebar.info("No documents uploaded yet.")
    #######################
    from api_utils import generate_insights

    st.sidebar.header("Insights")

    if "insights_result" not in st.session_state:
        st.session_state.insights_result = None

    if documents:
        insight_doc_ids = st.sidebar.multiselect(
            "Select documents for insights",
            options=[doc["id"] for doc in documents],
            format_func=lambda x: next(doc["filename"] for doc in documents if doc["id"] == x)
        )

        insight_question = st.sidebar.text_input(
            "Insight question",
            value="Which forms are missing phone number or email?"
        )

        if st.sidebar.button("Generate Insights"):
            if not insight_doc_ids:
                st.sidebar.warning("Select at least one document.")
            else:
                with st.spinner("Generating insights..."):
                    result = generate_insights(insight_doc_ids, insight_question)
                    st.session_state.insights_result = result

                st.sidebar.success("Insights generated!")
    else:
        st.sidebar.info("No documents uploaded yet.")


    # st.sidebar.header("Uploaded Documents")
    # if st.sidebar.button("Refresh Document List"):
    #     with st.spinner("Refreshing..."):
    #         st.session_state.documents = list_documents()
            
            
    

    documents = st.session_state.documents
    if documents:
        # for doc in documents:
        #     st.sidebar.text(
        #         f"{doc['filename']} (ID: {doc['id']}, Uploaded: {doc['upload_timestamp']})"
        #     )

        selected_file_id = st.sidebar.selectbox(
            "Select a document to delete",
            options=[doc["id"] for doc in documents],
            format_func=lambda x: next(doc["filename"] for doc in documents if doc["id"] == x)
        )

        if st.sidebar.button("Delete Selected Document"):
            with st.spinner("Deleting..."):
                delete_response = delete_document(selected_file_id)
                if delete_response:
                    st.sidebar.success(f"Document with ID {selected_file_id} deleted successfully.")
                    st.session_state.documents = list_documents()
                else:
                    st.sidebar.error(f"Failed to delete document with ID {selected_file_id}.")
