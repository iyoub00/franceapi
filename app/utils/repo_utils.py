# app/utils/repo_utils.py
# This file provides utility functions for handling Git repositories.
# Author: Yassine Amounane
import subprocess
import logging
import os
import json
from app.rag_service import analyze_file_content
from app.document import add_texts_to_qdrant
from app.utils.code_analyzer import detect_language, parse_code, calculate_metrics, generate_tags

SKIPPED_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.ico', '.svg',
    '.mp4', '.mov', '.avi', '.mkv', '.webm',
    '.mp3', '.wav', '.ogg', '.aac', '.flac',
    '.zip', '.tar', '.gz', '.rar', '.7z', '.jar', '.war',
    '.exe', '.dll', '.so', '.o', '.class', '.pyc', '.pyo', '.bin', '.dmg', '.app', '.msi',
    '.ttf', '.otf', '.woff', '.woff2', '.eot',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.ds_store', '.env', '.lock',
}

SKIPPED_FILENAMES = {
    'package-lock.json',
    'yarn.lock',
    'gemfile.lock',
    'composer.lock',
    'poetry.lock',
}

logger = logging.getLogger(__name__)

def clone_repository(repo_url: str, branch: str, path: str) -> bool:
    """
    Clones a Git repository from a given URL and branch into a specified path.

    Args:
        repo_url: The URL of the Git repository.
        branch: The branch to clone.
        path: The local path where the repository should be cloned.

    Returns:
        True if the cloning was successful, False otherwise.
    """
    git_command = [
        "git", "clone",
        "--depth", "1",
        "--branch", branch,
        repo_url,
        path
    ]
    command_str = " ".join(git_command)
    logger.info(f"Executing git command: {command_str}")

    try:
        result = subprocess.run(git_command, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            logger.info(f"Successfully cloned {repo_url} (branch: {branch}) to {path}")
            return True
        else:
            logger.error(f"Failed to clone repository {repo_url} branch {branch}. Error: {result.stderr.strip()}")
            return False
    except FileNotFoundError:
        logger.error("Git command not found. Please ensure Git is installed and in PATH.")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred during git clone: {e}", exc_info=True)
        return False

def process_repository_files(repo_path: str, repo_name: str) -> dict[str, str]:
    """
    Processes all files in a given repository path, reads their content, analyzes it, and logs information.

    Args:
        repo_path: The local path of the cloned repository.
        repo_name: The name of the repository (e.g., derived from the URL).

    Returns:
        A dictionary where keys are relative file paths and values are their analyses.
    """
    analyses: dict[str, str] = {}
    for root, dirs, files in os.walk(repo_path):
        if ".git" in dirs:
            dirs.remove(".git")

        for file_name in files:
            file_path = os.path.join(root, file_name)
            relative_file_path = os.path.relpath(file_path, repo_path)

            _, file_ext = os.path.splitext(file_name)
            file_ext_lower = file_ext.lower()
            base_file_name_lower = os.path.basename(file_name).lower()

            if base_file_name_lower in SKIPPED_FILENAMES or file_ext_lower in SKIPPED_EXTENSIONS:
                logger.info(f"Skipping file due to type/name: {relative_file_path}")
                continue

            file_content = None
            try:
                with open(file_path, "r", encoding="utf-8") as f_obj:
                    file_content = f_obj.read()
            except Exception as e:
                logger.warning(f"Could not read file {file_path} in repo {repo_name}: {e}. Skipping.", exc_info=True)
                continue

            language = detect_language(relative_file_path)
            parsed_data = parse_code(file_content, language, relative_file_path)
            metrics = calculate_metrics(file_content, language, parsed_data)
            tags = generate_tags(relative_file_path, language, parsed_data)

            llm_summary = "Error: LLM summary generation failed."
            try:
                llm_summary = analyze_file_content(file_content, relative_file_path)
            except Exception as e:
                logger.error(f"LLM analysis (summary) failed for file {relative_file_path} in {repo_name}: {e}", exc_info=True)

            analysis_json_object = {
                "file_path": relative_file_path,
                "language": language,
                "summary": llm_summary,
                "entities": parsed_data.get("entities", {}),
                "dependencies": parsed_data.get("dependencies", []),
                "imports": parsed_data.get("imports", []),
                "metrics": metrics,
                "tags": tags,
                "raw_content_snippet": parsed_data.get("raw_content")             
            }
            if "error" in parsed_data:
                analysis_json_object["parsing_error"] = parsed_data["error"]

            analysis_to_store = json.dumps(analysis_json_object)
            analyses[relative_file_path] = analysis_to_store

            try:
                num_added = add_texts_to_qdrant(
                    texts=[analysis_to_store],
                    metadatas=[{
                        "repo_name": repo_name,
                        "file_path": relative_file_path,
                        "original_file_path": file_path,
                        "is_summary": False,
                        "language": language
                    }]
                )
                if num_added > 0:
                    logger.info(f"Attempted to store detailed analysis for {relative_file_path} (lang: {language}) from repo {repo_name} in Qdrant.")
                else:
                    logger.warning(f"Call to store detailed analysis for {relative_file_path} from repo {repo_name} resulted in 0 texts added.")
            except Exception as e:
                logger.error(f"Error storing detailed analysis for {relative_file_path} from repo {repo_name} in Qdrant: {e}", exc_info=True)

    return analyses
