# app/document.py
# This file handles document processing and indexing.
# Author: Yassine Amounane
import re
from typing import List
from langchain_unstructured import UnstructuredLoader as UnstructuredFileLoader
from qdrant_client import QdrantClient, models
import uuid
from langchain.text_splitter import RecursiveCharacterTextSplitter
from .core import get_embeddings, QDRANT_HOST, QDRANT_PORT, QDRANT_COLLECTION_NAME, get_vectorstore
import logging

logger = logging.getLogger(__name__)

def load_documents(file_paths: List[str]):
    docs = []
    for path in file_paths:
        try:
            logger.info(f"Loading document: {path}")
            loader = UnstructuredFileLoader(path)
            loaded = loader.load()
            if not loaded:
                logger.warning(f"No content extracted from {path}")
                continue
            for doc in loaded:
                if not doc.page_content or not doc.page_content.strip():
                    logger.warning(f"Document {doc.metadata.get('source', 'unknown')} loaded with empty page_content.")
            docs.extend(loaded)
        except Exception as e:
            logger.error(f"Error loading {path}: {e}", exc_info=True)
    return docs

def split_documents(docs, chunk_size: int = 1000, chunk_overlap: int = 100):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    return splitter.split_documents(docs)

def add_documents_to_index(paths: List[str]) -> int:
    docs = load_documents(paths) 
    if not docs:
        logger.warning("No documents to index")
        return 0

    chunks = split_documents(docs)

    valid_chunks = [chunk for chunk in chunks if chunk.page_content and chunk.page_content.strip()]
    logger.info(f"Chunks before filtering: {len(chunks)}, after filtering: {len(valid_chunks)}")

    if not valid_chunks:
        logger.warning("No valid chunks to index after filtering.")
        return 0

    embeddings_model = get_embeddings()
    
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    collection_name = QDRANT_COLLECTION_NAME

    try:
        test_embedding = embeddings_model.embed_query("test")
        vector_size = len(test_embedding)
    except Exception as e:
        logger.error(f"Error getting embedding dimension: {e}", exc_info=True)
        return 0

    try:
        collection_info = client.get_collection(collection_name=collection_name)
        logger.info(f"Using existing collection: '{collection_name}'")
    except Exception as e:
        logger.info(f"Collection '{collection_name}' not found or error checking: {e}. Attempting creation.")
        try:
            client.recreate_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE)
            )
            logger.info(f"Collection '{collection_name}' created.")
        except Exception as create_exc:
            logger.error(f"Could not create collection '{collection_name}': {create_exc}", exc_info=True)
            return 0

    points_to_upsert = []
    for i, chunk in enumerate(valid_chunks):
        try:
            chunk_embedding = embeddings_model.embed_documents([chunk.page_content])[0]

            point = models.PointStruct(
                id=str(uuid.uuid4()),
                payload={
                    "text": chunk.page_content,
                    "metadata": chunk.metadata,
                },
                vector=chunk_embedding
            )
            points_to_upsert.append(point)
        except Exception as e:
            logger.error(f"Error processing chunk {i}: {e}", exc_info=True)

    if not points_to_upsert:
        logger.warning("No points to add to Qdrant.")
        return 0

    try:
        client.upsert(collection_name=collection_name, points=points_to_upsert, wait=True)
        logger.info(f"{len(points_to_upsert)} valid chunks (points) added to Qdrant collection '{collection_name}'")
        return len(points_to_upsert)
    except Exception as e:
        logger.error(f"Error upserting points to Qdrant collection '{collection_name}': {e}", exc_info=True)
        return 0

def clean_text(text):
    text = re.sub(r"[^\S\r\n]+", " ", text)
    text = re.sub(r"[\x7f\x80-\xff]", "", text)
    text = re.sub(r"coordinates.*?\}\}", "", text, flags=re.DOTALL)
    return text.strip()

def add_texts_to_qdrant(texts: List[str], metadatas: List[dict]) -> int:
    """
    Adds a list of texts and their corresponding metadatas to the global Qdrant collection.

    Args:
        texts: A list of strings to be added.
        metadatas: A list of dictionaries, each corresponding to a text.

    Returns:
        The number of texts successfully added.
    """
    if not texts:
        logger.warning("No texts provided to add_texts_to_qdrant.")
        return 0

    try:
        vectorstore = get_vectorstore()

        vectorstore.add_texts(texts=texts, metadatas=metadatas)
        logger.info(f"Successfully added {len(texts)} texts to Qdrant collection '{QDRANT_COLLECTION_NAME}'. Metadata example: {metadatas[0] if metadatas else 'N/A'}")
        return len(texts)
    except Exception as e:
        logger.error(f"Error adding texts to Qdrant collection '{QDRANT_COLLECTION_NAME}': {str(e)}", exc_info=True)
        return 0