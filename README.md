# Silicon Shoring - API AI Agent

## Overview
Silicon Shoring - API AI Agent is an agent that allows you to interact with your documents and Git repositories using natural language. It leverages a Retrieval Augmented Generation (RAG) pipeline, local Large Language Models (LLM) via Mistral, and a Qdrant vector database to provide insightful answers and summaries from your data.

## Key Features
*   Query documents using natural language.
*   Ingest and analyze Git repositories.
*   Retrieve information from source code (summaries and details).
*   File upload and processing for various document types (PDF, DOC, DOCX, TXT).
*   Utilizes local LLM (Ollama) and Vector DB (Qdrant).

## How it Works

### Document Querying
1.  **Upload:** Files are uploaded via the API.
2.  **Process:** Documents are loaded, chunked into smaller pieces, and processed to generate embeddings (numerical representations).
3.  **Store:** These embeddings and their corresponding text chunks are stored in a Qdrant vector database.
4.  **Query:** When a question is asked, it's also converted into an embedding.
5.  **Retrieve:** Qdrant searches for the most similar document chunks based on the query embedding.
6.  **Generate:** The retrieved chunks, along with the original question, are fed to an LLM (Ollama) which generates a comprehensive answer.

### Repository Ingestion
1.  **Clone:** Git repositories are cloned locally.
2.  **Analyze:** Each relevant source file is analyzed:
    *   Language detection.
    *   Basic code structure parsing (classes, functions, imports for Python).
    *   Calculation of simple code metrics.
    *   Generation of descriptive tags.
3.  **Summarize (File-level):** An LLM generates a summary for each analyzed file.
4.  **Store (File-level):** The detailed analysis and LLM summary for each file are stored as distinct documents in Qdrant.
5.  **Summarize (Repo-level):** After processing all files, an LLM generates an overall summary of the entire repository based on the individual file analyses.
6.  **Store (Repo-level):** This repository summary is also stored in Qdrant, allowing for queries about the repository as a whole or its specific components.

## Technologies Used
*   **FastAPI:** For building the API.
*   **Langchain:** For RAG pipeline orchestration and LLM interaction.
*   **Mistral:** For running Large Language Models.
*   **Qdrant:** Vector database for storing and retrieving embeddings.
*   **Mistral Embeddings:** For generating text embeddings.
*   **python-magic:** For MIME type detection of uploaded files.
*   **UnstructuredFileLoader:** For loading various document types.

## Key Components

*   `main.py`: Initializes and runs the FastAPI application.
*   `app/api.py`: Defines API endpoints for file upload, repository ingestion, and querying.
*   `app/core.py`: Manages core components like LLM , embedding models, and the Qdrant vector store connection. Handles dynamic Qdrant collection creation.
*   `app/document.py`: Handles document loading (using Unstructured), chunking, embedding, and indexing into Qdrant. Also provides utilities for adding generic texts to Qdrant.
*   `app/rag_service.py`: Implements the core RAG logic for answering questions and provides services for LLM-based analysis of file content and summarization of repository analyses.
*   `app/rag_prompt.py`: Contains the French prompt template for the RAG model.
*   `app/utils/code_analyzer.py`: Provides tools for detecting language, parsing basic code structures (classes, functions, imports for Python), calculating simple code metrics, and generating tags.
*   `app/utils/document_utils.py`: Contains utility functions for document handling, like text cleaning, and lists of supported extensions/ignored folders for repository processing.
*   `app/utils/file_validation.py`: Validates uploaded files based on MIME type (using `python-magic`) and size. Supports PDF, DOC, DOCX, TXT.
*   `app/utils/repo_utils.py`: Handles cloning of Git repositories, iterating through files (skipping irrelevant ones), orchestrating file analysis with `code_analyzer.py` and `rag_service.py`, and storing individual file analyses in Qdrant.
*   `app/settings.py`: Placeholder for application settings.

## Getting Started

### Prerequisites
*   Python 3.8+
*   Docker Engine
*   Mistral API Key

### Installation
1.  Clone the repository:
    ```bash
    git clone <your-repo-url>
    ```
2.  Navigate to the project directory:
    ```bash
    cd <project-directory>
    ```
3.  Create a virtual environment:
    ```bash
    python -m venv agent_api
    ```
4.  Activate the environment:
    *   Linux/macOS:
        ```bash
        source agent_api/bin/activate
        ```
    *   Windows:
        ```bash
        agent_api\Scripts\activate
        ```
5.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

### Qdrant Setup (Vector Database)
1.  Pull the Qdrant Docker image:
    ```bash
    docker pull qdrant/qdrant
    ```
2.  Run the Qdrant container:
    ```sh
    docker run -p 6333:6333 -p 6334:6334 \
        -v $(pwd)/qdrant_storage:/qdrant/storage:z \
        qdrant/qdrant
    ```
    *(Note: `$(pwd)/qdrant_storage` creates a directory in your current project folder to persist Qdrant data. Adjust path if needed. The `:z` option is for SELinux systems, remove if not applicable.)*
3.  Access Qdrant dashboard: [http://localhost:6333/dashboard](http://localhost:6333/dashboard)

#### Only for local - Ollama Setup (Local LLM)
1.  Ensure Ollama is installed and running.
2.  Pull the required model (this is the default, can be changed in `app/core.py`):
    ```bash
    ollama pull cogito:3b
    ```

### Environment Variables (Optional)
Create a `.env` file in the project root to customize settings. Defaults are used if not set.
```env
# QDRANT_HOST=127.0.0.1
# QDRANT_PORT=6333
# QDRANT_COLLECTION_NAME=document_collection
# MISTRAL_API_KEY=
```

### Running the Application
```sh
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
The API will be accessible at `http://localhost:8000`.

## API Endpoints

### **POST /files**
*   **Purpose:** Uploads a document for processing and indexing.
*   **Request:** `multipart/form-data` with a `file` field.
*   **Supported Types:** PDF, DOC, DOCX, TXT.
*   **Response (Success):**
    ```json
    {
        "status": "ok",
        "filename": "example.txt",
        "chunks": 10,
        "validation": "Supported type: text/plain (.txt)"
    }
    ```
*   **Example (curl):**
    ```sh
    curl -X POST -F "file=@/path/to/your/document.txt" http://localhost:8000/files
    ```

### **POST /repositories**
*   **Purpose:** Ingests and analyzes a Git repository.
*   **Request (JSON):**
    ```json
    {
        "repo_url": "https://github.com/user/repo.git",
        "branch": "main" // Optional, defaults to "main"
    }
    ```
*   **Response (Success):**
    ```json
    {
        "message": "Repository ingestion completed",
        "repo_url": "https://github.com/user/repo.git",
        "branch": "main",
        "repo_name": "repo",
        "files_processed": 50,
        "repo_summary": "This repository contains..." // LLM-generated summary
    }
    ```
*   **Example (curl):**
    ```sh
    curl -X POST -H "Content-Type: application/json" \
         -d '{"repo_url": "https://github.com/user/repo.git", "branch": "develop"}' \
         http://localhost:8000/repositories
    ```

### **POST /query**
*   **Purpose:** Queries the indexed documents and repositories.
*   **Request (JSON):**
    ```json
    {
        "question": "What is the main purpose of this project?",
        "k": 5 // Optional, number of chunks to retrieve, default is 100
    }
    ```
*   **Response (Success):**
    ```json
    {
        "status": "ok",
        "question": "What is the main purpose of this project?",
        "answer": "The main purpose of this project is to...", // LLM-generated answer
        "raw_results": [
            "chunk content 1...",
            "chunk content 2..."
        ]
    }
    ```
*   **Example (curl):**
    ```sh
    curl -X POST -H "Content-Type: application/json" \
         -d '{"question": "Describe the authentication module"}' \
         http://localhost:8000/query
    ```

## Deployment
*   **Application:** The FastAPI application can be containerized using Docker. A `Dockerfile` would be needed. For production, run with a production-grade ASGI server like Gunicorn behind a reverse proxy (e.g., Nginx).
*   **Qdrant:** For production, ensure Qdrant's storage volume is properly managed and backed up. Refer to official Qdrant documentation for clustering and scaling.
*   **Mistral:** Specify the apiKey on the `.env` file.
*   **huggingface:** Specify the apiKey on the `.env` file. The user that will generate the token have to first agree to the terms on the page : https://huggingface.co/mistralai/Mixtral-8x7B-v0.1

### .env File
```sh
MISTRAL_API_KEY=XXXXXXX
HF_TOKEN=hf_XXXXXX
```