#app/core.py
# This file defines core functionalities like LLM and vector store initialization.
# Author: Yassine Amounane
import os
import logging
from dotenv import load_dotenv
from langchain_mistralai.chat_models import ChatMistralAI
from langchain_mistralai.embeddings import MistralAIEmbeddings
from qdrant_client import QdrantClient, models
from langchain_qdrant import QdrantVectorStore
from app.settings import (
    MISTRAL_API_KEY,
    MISTRAL_LLM_ANALYZE_CODE_MODEL,
    MISTRAL_LLM_QUERY_MODEL,
    MISTRAL_EMBEDDINGS_MODEL,
    QDRANT_HOST,
    QDRANT_PORT,
    QDRANT_COLLECTION_NAME
)

load_dotenv()

logger = logging.getLogger(__name__)

def get_embeddings():
    return MistralAIEmbeddings(api_key=MISTRAL_API_KEY, model=MISTRAL_EMBEDDINGS_MODEL)

def get_llm_code():
    return ChatMistralAI(model=MISTRAL_LLM_ANALYZE_CODE_MODEL, api_key=MISTRAL_API_KEY)

def get_llm_query():
    return ChatMistralAI(model=MISTRAL_LLM_QUERY_MODEL, api_key=MISTRAL_API_KEY)

def get_vectorstore():
    """
    Initializes and returns a Qdrant vector store client.
    Checks if the collection exists and creates it if not.
    """
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    embeddings = get_embeddings()

    try:
        client.get_collection(collection_name=QDRANT_COLLECTION_NAME)
        logger.info(f"Collection '{QDRANT_COLLECTION_NAME}' already exists.")
    except Exception as e:
        logger.warning(f"Collection '{QDRANT_COLLECTION_NAME}' not found or error checking: {e}. Attempting to create it.")

        embedding_dim = 0
        if hasattr(embeddings, 'embed_query'):
            try:
                test_embedding = embeddings.embed_query("test")
                embedding_dim = len(test_embedding)
                logger.info(f"Determined embedding dimension: {embedding_dim}")
            except Exception as emb_ex:
                logger.error(f"Could not determine embedding dimension dynamically via embed_query: {emb_ex}")
        elif hasattr(embeddings, 'client') and hasattr(embeddings.client, 'get_sentence_embedding_dimension'):
            try:
                embedding_dim = embeddings.client.get_sentence_embedding_dimension()
                logger.info(f"Determined embedding dimension via get_sentence_embedding_dimension: {embedding_dim}")
            except Exception as emb_ex_alt:
                 logger.error(f"Could not determine embedding dimension dynamically via get_sentence_embedding_dimension: {emb_ex_alt}")

        if embedding_dim == 0:
            default_dim = 512
            logger.info(f"Could not determine embedding dimension programmatically, using default {default_dim}.")
            embedding_dim = default_dim

        try:
            client.create_collection(
                collection_name=QDRANT_COLLECTION_NAME,
                vectors_config=models.VectorParams(size=embedding_dim, distance=models.Distance.COSINE)
            )
            logger.info(f"Successfully created collection '{QDRANT_COLLECTION_NAME}' with vector size {embedding_dim}.")
        except Exception as create_ex:
            logger.error(f"Failed to create collection '{QDRANT_COLLECTION_NAME}': {create_ex}", exc_info=True)
            raise create_ex

    vectorstore = QdrantVectorStore(
        client=client,
        collection_name=QDRANT_COLLECTION_NAME,
        embedding=embeddings,
        content_payload_key="text",
        metadata_payload_key="metadata"
    )
    return vectorstore

def delete_qdrant_collection(collection_name: str):
    """
    Deletes a Qdrant collection.

    Args:
        collection_name: The name of the collection to delete.
    """
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    try:
        client.delete_collection(collection_name=collection_name)
        logger.info(f"Collection '{collection_name}' deleted successfully.")
    except Exception as e:
        logger.error(f"Failed to delete collection '{collection_name}': {e}", exc_info=True)
