# app/rag_prompt.py
# This file defines the RAG (Retrieval Augmented Generation) prompt template.
# Author: Yassine Amounane
RAG_PROMPT = """Vous êtes un assistant IA chargé de répondre à des questions basées sur des extraits de documents fournis.

Voici les extraits pertinents trouvés dans les documents :

{context}

Votre mission : Répondre à la question suivante de manière concise, claire et en français :

{question}
"""