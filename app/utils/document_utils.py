# app/utils/document_utils.py
# This file provides utility functions for document manipulation.
# Author: Yassine Amounane

SUPPORTED_EXTENSIONS = [
    ".py", ".java", ".js", ".ts", ".go", ".rb", ".php", ".rs",
    ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".xml", ".html", ".css" , "mts", ".mjs", ".c", ".cpp", ".h", ".hpp", ".sh", ".bash", ".sql"
]
IGNORED_FOLDERS = ["node_modules", "__pycache__", ".git", "vendor"]

def clean_text(text: str) -> str:
    text = text.replace("\x00", "")
    return text.strip()
