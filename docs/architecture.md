# AI Powered Form Agent — Architecture Workflow

## 1) Document Ingestion + Indexing Workflow
User uploads a file (PDF / DOCX / HTML / Image)  
→ Backend validates file type  
→ File saved temporarily on server  
→ Parsing pipeline extracts text/content  
→ Chunking pipeline splits content into smaller chunks  
→ Embedding model generates vectors for chunks  
→ Chunks + metadata stored in ChromaDB (vector store)  
→ Document record stored in SQLite (file_id, filename, timestamp)

---

## 2) QA (Chat + RAG) Workflow
User question + optional session_id  
→ Fetch chat history from SQLite  
→ History-aware retriever rewrites query (contextualized question)  
→ Retrieve top-k relevant chunks from ChromaDB  
→ Stuff retrieved chunks into QA prompt  
→ LLM generates answer using retrieved context  
→ Extract sources from retrieved chunks (file/page/chunk preview)  
→ Store conversation logs in SQLite  
→ Return response:
- answer  
- session_id  
- model  
- sources  

---

## 3) Summarization Workflow (Hierarchical Summary)
User selects file_ids  
→ For each file_id:
  → Seed query retrieves broad context from ChromaDB  
  → Field/Section extraction chain identifies major sections  
  → For each section:
     → Retrieve section-specific chunks from ChromaDB  
     → Generate section summary using summarization chain  
  → Merge all section summaries  
  → Generate final combined summary per document  
→ Return:
- final summary  
- sections found  
- section summaries  

---

## 4) Insights Workflow (Cross-Document Reasoning)
User selects multiple file_ids + insight question  
→ For each file_id:
  → Retrieve top-k evidence chunks from ChromaDB  
  → Store per-document context  
→ Combine all document contexts into one structured input  
→ LLM generates insights using only provided contexts  
→ Return JSON output:
- answer  
- per_document findings  
- stats  
- recommendations  
