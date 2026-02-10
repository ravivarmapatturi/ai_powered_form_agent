# AI Powered Form Agent

This is a end-to-end working prototype that you can **upload forms**, **extract information**, get **answers from questions** ,**summarization** and **insights** from them.

Live Demo link: http://34.202.126.236/

## Demo Video
[▶ Watch Demo](https://raw.githubusercontent.com/ravivarmapatturi/ai_powered_form_agent/main/docs/Demo.mp4)


It supports:
- **QA Chat (RAG)** over uploaded forms
- **Summarization** of one or more forms
- **Insights** across multiple forms (cross-document analysis)

The goal of this project is to show a working prototype of an “Intelligent Form Agent” that can handle both structured and unstructured documents.

---

## What this app can do

### 1) Upload + Index Forms
You can upload:
- PDF (`.pdf`)
- Word (`.docx`)
- HTML (`.html`)
- Images (`.jpg`, `.jpeg`, `.png`, `.tiff`, `.tif`)

Uploaded documents are:
1. parsed
2. chunked
3. embedded
4. stored in ChromaDB

---

### 2) Chat (RAG Question Answering)
Ask questions like:
- “What is the patient name?”
- “What is the total amount?”
- “Which phone number is mentioned?”
- “What is missing in this form?”

The backend retrieves the most relevant chunks from ChromaDB and uses an LLM to answer.

The response also includes **sources** (chunk preview + page number) so the user can trust the answer.

---

### 3) Summarization (Hierarchical)
Instead of doing one-shot summarization, this app follows a hierarchical approach:

1. Retrieve broad context
2. Identify major form sections / fields
3. Summarize each section separately
4. Merge into a final summary

This reduces missing important details from long forms.

---

### 4) Insights Across Multiple Forms
You can ask cross-document questions like:
- “Which forms are missing phone number?”
- “List all forms where email is not filled”
- “How many forms have cashless insurance?”

The system collects evidence per document and then generates a combined JSON result.

---

## Tech Stack

**Backend**
- FastAPI
- LangChain
- OpenAI models
- ChromaDB

**Frontend**
- Streamlit

**Deployment**
- Docker / Docker Compose
- AWS EC2 (demo deployment)

---

## Project Structure

```
ai_powered_form_agent/
├── README.md
├── data/
│   └── sample_forms/
├── docs/
│   └── architecture.md
├── docker-compose.yml
├── deploy.sh
└── src/
    ├── backend/
    │   ├── main.py
    │   ├── parsing_utils.py
    │   ├── chunking_utils.py
    │   ├── vector_db_utils.py
    │   ├── query_translation_utils.py
    │   ├── db_utils.py
    │   ├── data_validation_utils.py
    │   ├── requirements.txt
    │   └── Dockerfile
    └── frontend/
        ├── streamlit_app.py
        ├── sidebar.py
        ├── chat_interface.py
        ├── api_utils.py
        ├── requirements.txt
        └── Dockerfile
```

---

## Setup (Local)

### 1) Clone repo
```bash
git clone https://github.com/ravivarmapatturi/ai_powered_form_agent.git
cd ai_powered_form_agent
```

### 2) Add environment variables
Create a backend `.env` file:

`src/backend/.env`
```bash
OPENAI_API_KEY=your_key_here
```

(Optional) Create a frontend `.env` file:

`src/frontend/.env`
```bash
API_BASE_URL=http://localhost:8000
```

---

## Run with Docker Compose 

```bash
docker compose up --build -d
```

or 

```bash
./deploy.sh
```

Open:
- Frontend: `http://localhost:8501`
- Backend: `http://localhost:8000/status`

---

## Run Without Docker 

### Backend
```bash
cd src/backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd src/frontend
pip install -r requirements.txt
streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0
```

---

## API Endpoints

Backend exposes:

- `GET /status` → health check
- `POST /upload-doc` → upload + index a document
- `GET /list-docs` → list uploaded documents
- `POST /delete-doc` → delete a document
- `POST /chat` → ask questions (RAG)
- `POST /summarize-docs` → summarize selected docs
- `POST /insights` → cross-document insights

---


## Demo Data
Sample PDFs are included in:
```
data/sample_forms/
```

---

## Author
Built by **Ravivarma**.
