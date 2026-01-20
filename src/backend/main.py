from fastapi import FastAPI, File, UploadFile,HTTPException
from data_validation_utils import QueryInput,QueryResponse, DocumentInfo ,DeleteFileRequest
from query_translation_utils import get_rag_chain, get_summarization_chain , get_field_extraction_chain
from vector_db_utils import index_document_to_chroma,delete_doc_from_chroma,get_relevant_chunks_from_chroma
from db_utils import insert_application_logs,get_chat_history,get_all_documents,insert_document_record,delete_document_record
import optparse
import uuid
import logging
import shutil
import os
from fastapi import Body
import json 

logging.basicConfig(filename='app.log',level=logging.INFO)

app=FastAPI()

@app.get("/status")
async def checking_status():
    return {"status":"ok"}

@app.post("/chat",response_model=QueryResponse)
def chat(query_input: QueryInput):
    session_id = query_input.session_id
    logging.info(f"Session ID: {session_id}, User Query: {query_input.question}, Model: {query_input.model.value}")
    if not session_id:
        session_id = str(uuid.uuid4())

    

    chat_history = get_chat_history(session_id)
    rag_chain = get_rag_chain(query_input.model.value)
    result = rag_chain.invoke({
        "input": query_input.question,
        "chat_history": chat_history
    })

    answer = result["answer"]
    


    
    # insert_application_logs(session_id, query_input.question, answer, query_input.model.value)
    # logging.info(f"Session ID: {session_id}, AI Response: {answer}")
    # return QueryResponse(answer=answer, session_id=session_id, model=query_input.model)
    
    source_docs = result.get("context", [])  # context contains retrieved docs

    sources = []
    for d in source_docs:
        meta = d.metadata or {}
        sources.append({
            "source": meta.get("source"),
            "page_number": meta.get("page_number") or meta.get("page"),
            "chunk_preview": d.page_content[:300]  # small preview
        })


    insert_application_logs(session_id, query_input.question, answer, query_input.model.value)
    logging.info(f"Session ID: {session_id}, AI Response: {answer}")

    return QueryResponse(
        answer=answer,
        session_id=session_id,
        model=query_input.model.value,
        sources=sources
    )


@app.post("/upload-doc")
def upload_and_index_document(file: UploadFile = File(...)):
    allowed_extensions = ['.pdf', '.docx', '.html', '.jpg', '.jpeg', '.png', '.tiff', '.tif']
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed types are: {', '.join(allowed_extensions)}")
    
    temp_file_path = f"temp_{file.filename}"
    
    try:
        # Save the uploaded file to a temporary file
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        file_id = insert_document_record(file.filename)
        success = index_document_to_chroma(temp_file_path, file_id)
        
        if success:
            return {"message": f"File {file.filename} has been successfully uploaded and indexed.", "file_id": file_id}
        else:
            delete_document_record(file_id)
            raise HTTPException(status_code=500, detail=f"Failed to index {file.filename}.")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.get("/list-docs", response_model=list[DocumentInfo])
def list_documents():
    return get_all_documents()

@app.post("/delete-doc")
def delete_document(request: DeleteFileRequest):
    # Delete from Chroma
    chroma_delete_success = delete_doc_from_chroma(request.file_id)

    if chroma_delete_success:
        # If successfully deleted from Chroma, delete from our database
        db_delete_success = delete_document_record(request.file_id)
        if db_delete_success:
            return {"message": f"Successfully deleted document with file_id {request.file_id} from the system."}
        else:
            return {"error": f"Deleted from Chroma but failed to delete document with file_id {request.file_id} from the database."}
    else:
        return {"error": f"Failed to delete document with file_id {request.file_id} from Chroma."}


@app.post("/summarize-docs")
def summarize_documents(payload: dict = Body(...)):

    file_ids = payload.get("file_ids", [])
    model = payload.get("model", "gpt-4o-mini")

    if not file_ids:
        raise HTTPException(status_code=400, detail="file_ids is required")

    summary_chain = get_summarization_chain(model=model)
    field_chain = get_field_extraction_chain(model=model)

    results = []

    for file_id in file_ids:

        # 1) Get broad context from the document
        seed_query = "Give all major sections and fields present in this form."
        seed_docs = get_relevant_chunks_from_chroma(seed_query, file_id=file_id, k=25)

        if not seed_docs:
            results.append({"file_id": file_id, "summary": "No content found."})
            continue

        seed_context = "\n\n".join([d.page_content for d in seed_docs])

        # 2) Extract sections/field groups (LLM)
        raw_fields = field_chain.invoke({"context": seed_context}).content

        try:
            fields = json.loads(raw_fields)
            if not isinstance(fields, list):
                fields = []
        except:
            fields = []

        if not fields:
            fields = ["General Form Details"]  # fallback

        # 3) Summarize each field/section separately
        section_summaries = []
        for field_name in fields:
            docs = get_relevant_chunks_from_chroma(
                query=f"Extract details for section: {field_name}",
                file_id=file_id,
                k=10
            )

            if not docs:
                continue

            context = "\n\n".join([d.page_content for d in docs])

            section_summary = summary_chain.invoke({
                "context": context
            })

            # if your chain returns dict or string handle both
            if isinstance(section_summary, dict):
                section_summary = section_summary.get("text") or section_summary.get("output_text") or str(section_summary)

            section_summaries.append(f"### {field_name}\n{section_summary}")

        # 4) Final merged summary (1 per document)
        final_context = "\n\n".join(section_summaries)

        final_summary = summary_chain.invoke({
            "context": final_context
        })

        if isinstance(final_summary, dict):
            final_summary = final_summary.get("text") or final_summary.get("output_text") or str(final_summary)

        results.append({
            "file_id": file_id,
            "summary": final_summary,
            "sections_found": fields,
            "section_summaries": section_summaries
        })

    return {"summaries": results}


from fastapi import Body, HTTPException
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from vector_db_utils import get_relevant_chunks_from_chroma

@app.post("/insights")
def generate_insights(payload: dict = Body(...)):
    """
    payload:
    {
      "file_ids": [1,2,3],
      "question": "Which forms are missing phone number?"
    }
    """
    file_ids = payload.get("file_ids", [])
    question = payload.get("question", "")

    if not file_ids:
        raise HTTPException(status_code=400, detail="file_ids is required")

    if not question.strip():
        raise HTTPException(status_code=400, detail="question is required")

    # Collect evidence from each document separately
    per_doc = []
    for file_id in file_ids:
        docs = get_relevant_chunks_from_chroma(question, file_id=file_id, k=6)
        context = "\n\n".join([d.page_content for d in docs])

        per_doc.append({
            "file_id": file_id,
            "context": context if context.strip() else "Not Found"
        })

    combined_context = "\n\n".join(
        [f"[DOC file_id={x['file_id']}]\n{x['context']}" for x in per_doc]
    )

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    prompt = ChatPromptTemplate.from_messages([
        ("system",
        "You are an Intelligent Form Agent. Answer using ONLY the provided document contexts. "
        "Do not guess. If info is missing, say 'Not Found'. "
        "Return ONLY valid JSON (no markdown)."
        ),
        ("human",
        "Question: {question}\n\n"
        "Document Contexts:\n{context}\n\n"
        "Return JSON with these keys exactly:\n"
        "answer, per_document, stats, recommendations.\n\n"
        "Rules:\n"
        "- per_document must be a list of objects with keys: file_id and finding\n"
        "- stats must be a JSON object (can be empty)\n"
        "- recommendations must be a list\n"
        )
    ])

    chain = LLMChain(llm=llm, prompt=prompt)
    result = chain.run({"question": question, "context": combined_context})

    return {"result": result}
