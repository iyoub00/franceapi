#app/settings.py
# This file defines application settings and configurations.
# Author: Yassine Amounane
import os
from dotenv import load_dotenv

load_dotenv()

# Mistral AI Configuration
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_LLM_RAG_MODEL = os.getenv("MISTRAL_LLM_MODEL", "mistral-small-latest")
MISTRAL_LLM_ANALYZE_CODE_MODEL = os.getenv("MISTRAL_LLM_MODEL", "devstral-small-2505")
MISTRAL_LLM_QUERY_MODEL = os.getenv("MISTRAL_LLM_MODEL", "mistral-small-latest")
MISTRAL_EMBEDDINGS_MODEL = os.getenv("MISTRAL_EMBEDDING_MODEL", "mistral-embed")