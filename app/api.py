# app/api.py
# This file defines the FastAPI routes for the application.
# Author: Yassine Amounane
import shutil
import os
import tempfile
import logging
from app.rag_service import rag_query, summarize_repository_analyses
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.utils.file_validation import validate_file
from app.document import add_documents_to_index, add_texts_to_qdrant
from pydantic import BaseModel
from app.core import get_vectorstore, delete_qdrant_collection, QDRANT_COLLECTION_NAME
from typing import Optional
from app.utils.repo_utils import clone_repository, process_repository_files
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter()

class QueryRequest(BaseModel):
    question: str
    k: int = 100

class GitIngestRequest(BaseModel):
    repo_url: str
    branch: Optional[str] = "main"

async def ingest_repository(request: GitIngestRequest):
    logger.info(f"Starting ingestion for {request.repo_url}, branch {request.branch}")
    repo_url = request.repo_url
    branch = request.branch
    temp_dir = None

    repo_name_full = repo_url.rsplit("/", 1)[-1]
    if repo_name_full.endswith(".git"):
        repo_name = repo_name_full[:-4]
    else:
        repo_name = repo_name_full

    try:
        temp_dir = tempfile.mkdtemp()
        logger.info(f"Created temporary directory for {repo_name}: {temp_dir}")

        if not clone_repository(repo_url, branch, temp_dir):
            raise HTTPException(status_code=500, detail=f"Failed to clone repository: {repo_name}")

        file_analyses = process_repository_files(temp_dir, repo_name)

        repo_summary = summarize_repository_analyses(file_analyses, repo_name)

        logger.info(f"Repository summary for {repo_name} generated.")

        num_added_summary = add_texts_to_qdrant(
            texts=[repo_summary],
            metadatas=[{"repo_name": repo_name, "is_summary": True}]
        )

        if num_added_summary > 0:
            logger.info(f"Attempted to store repository summary for {repo_name} in Qdrant.")
        else:
            logger.warning(f"Call to store repository summary for {repo_name} in Qdrant resulted in 0 texts added.")

        logger.info(f"Successfully completed ingestion for {repo_name}")
        return {
            "message": "Repository ingestion completed",
            "repo_url": repo_url,
            "branch": branch,
            "repo_name": repo_name,
            "files_processed": len(file_analyses),
            "repo_summary": repo_summary
        }
    except Exception as e:
        logger.error(f"Error during repository ingestion for {request.repo_url} (branch {request.branch}): {e}", exc_info=True)
        if isinstance(e, HTTPException):
            raise
        else:
            raise HTTPException(status_code=500, detail=f"Internal server error during repository ingestion: {e}")
    finally:
        if temp_dir and os.path.exists(temp_dir):
            logger.info(f"Cleaning up temporary directory: {temp_dir}")
            shutil.rmtree(temp_dir)

@router.post("/repositories")
async def handle_ingest_repository(request: GitIngestRequest):
    return await ingest_repository(request)

@router.post("/query")
async def query_documents(request: QueryRequest):
    try:
        db = get_vectorstore()
        results = db.similarity_search(request.question, k=request.k)

        answer = rag_query(request.question, results)

        return {
            "status": "ok",
            "question": request.question,
            "answer": answer,
            "raw_results": [doc.page_content for doc in results]
        }
    
    except Exception as e:
        logger.error(f"Error during search: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")
    
@router.post("/files")
async def upload_file(file: UploadFile = File(...)):
    logger.info(f"Starting file upload: {file.filename}")
    
    if not file.filename:
        logger.error("File without a name")
        raise HTTPException(status_code=400, detail="File without a name")

    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
            shutil.copyfileobj(file.file, tmpfile)
            tmpfile_path = tmpfile.name
        
        is_valid, message = validate_file(tmpfile_path)
        if not is_valid:
            logger.error(f"Validation failed: {message}")
            raise HTTPException(status_code=400, detail=message)
        
        logger.info(f"Starting ingestion for {tmpfile_path}")
        nb_chunks = add_documents_to_index([tmpfile_path])
        logger.info(f"Ingestion finished: {nb_chunks} chunks added")
        
        return {
            "status": "ok",
            "filename": file.filename,
            "chunks": nb_chunks,
            "validation": message
        }
    
    except Exception as e:
        logger.error(f"Error during processing: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")
    
    finally:
        if 'tmpfile_path' in locals() and os.path.exists(tmpfile_path):
            os.unlink(tmpfile_path)

@router.delete("/collection")
async def delete_collection_endpoint():
    """
    Deletes the Qdrant collection specified by QDRANT_COLLECTION_NAME.
    """
    logger.info(f"Received request to delete collection: {QDRANT_COLLECTION_NAME}")
    try:
        delete_qdrant_collection(collection_name=QDRANT_COLLECTION_NAME)
        logger.info(f"Successfully initiated deletion of collection '{QDRANT_COLLECTION_NAME}'.")
        return JSONResponse(
            status_code=200,
            content={"message": f"Collection '{QDRANT_COLLECTION_NAME}' scheduled for deletion."}
        )
    except Exception as e:
        logger.error(f"Error during collection deletion endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete collection '{QDRANT_COLLECTION_NAME}': {str(e)}")
