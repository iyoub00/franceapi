# app/rag_service.py
# This file implements the RAG service for querying and summarization.
# Author: Yassine Amounane
import logging
import json
from app.core import get_llm_code, get_llm_query
from app.rag_prompt import RAG_PROMPT

logger = logging.getLogger(__name__)

def rag_query(question: str, chunks: list):
    context = "\n\n".join([chunk.page_content for chunk in chunks])
    prompt = RAG_PROMPT.format(context=context, question=question)
    
    llm = get_llm_query()
    response = llm.invoke(prompt)
    
    return response.strip()

def analyze_file_content(content: str, filename: str) -> str:
    """
    Analyzes the content of a single file using the LLM.
    """
    llm = get_llm_code()
    prompt = f"Analyze the following file content from '{filename}' and provide a concise summary of its purpose, functionality, and key components: \n\n{content}\n\nAnalysis:"
    try:
        response = llm.invoke(prompt)
        return response.strip()
    except Exception as e:
        logger.error(f"LLM invocation failed for analyze_file_content (filename: {filename}): {e}", exc_info=True)
        return f"Error: LLM analysis failed for file {filename}."

def summarize_repository_analyses(analyses: dict[str, str], repo_name: str) -> str:
    """
    Summarizes a collection of file analyses for a repository using the LLM.
    The 'analyses' dict now contains JSON strings as values.
    """
    llm = get_llm_query()

    text_summaries = []
    for file_path, json_string_analysis in analyses.items():
        try:
            analysis_obj = json.loads(json_string_analysis)
            summary = analysis_obj.get("summary", f"Summary not available for {file_path}")
            text_summaries.append(f"File: {file_path}\nSummary: {summary}")
        except json.JSONDecodeError:
            logger.warning(f"Could not parse JSON analysis for {file_path} in summarize_repository_analyses. Raw data: '{json_string_analysis[:100]}...'")
            text_summaries.append(f"File: {file_path}\nSummary: Could not parse analysis data.")

    context_for_summary = "\n\n".join(text_summaries)

    prompt = f"The following are file summaries from the repository '{repo_name}':\n\n{context_for_summary}\n\nProvide a concise overall summary of the repository's purpose and architecture based on these file summaries.\n\nOverall Repository Summary:"
    try:
        response = llm.invoke(prompt)
        return response.strip()
    except Exception as e:
        logger.error(f"LLM invocation failed for summarize_repository_analyses (repo_name: {repo_name}): {e}", exc_info=True)
        return f"Error: LLM summary generation failed for repository {repo_name}."