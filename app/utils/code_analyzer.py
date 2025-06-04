# app/utils/code_analyzer.py
# This file contains functions for analyzing source code files.
# Author: Yassine Amounane
import logging
import os
import re

logger = logging.getLogger(__name__)

LANGUAGE_EXTENSIONS_MAP = {
    ".py": "python", ".java": "java", ".js": "javascript", ".ts": "typescript",
    ".go": "go", ".rb": "ruby", ".php": "php", ".cs": "csharp",
    ".c": "c", ".cpp": "cpp", ".h": "c_header", ".hpp": "cpp_header",
    ".rs": "rust", ".kt": "kotlin", ".scala": "scala", ".swift": "swift",
    ".md": "markdown", ".json": "json", ".yaml": "yaml", ".yml": "yaml",
    ".html": "html", ".css": "css", ".txt": "text", ".sh": "shell",
}

def detect_language(file_path: str) -> str:
    """Detects the programming language of a file based on its extension."""
    _, ext = os.path.splitext(file_path)
    return LANGUAGE_EXTENSIONS_MAP.get(ext.lower(), "unknown")

def parse_code(file_content: str, language: str, file_path: str) -> dict:
    """
    Parses code to extract basic entities. Simplified version.
    For Python, it attempts to find classes and functions using regex.
    For other languages, it currently returns a raw content snippet.
    """
    if language == "python":
        try:
            classes = [{"name": m.group(1), "methods": []} for m in re.finditer(r"^\s*class\s+(\w+)(?:\(|:)", file_content, re.MULTILINE)]
            functions = [{"name": m.group(1)} for m in re.finditer(r"^\s*def\s+(\w+)\s*\(", file_content, re.MULTILINE)]
            imports = [{"name": m.group(1)} for m in re.finditer(r"^\s*import\s+([\w.]+)", file_content, re.MULTILINE)]
            imports.extend([{"name": m.group(1)} for m in re.finditer(r"^\s*from\s+([\w.]+)\s+import", file_content, re.MULTILINE)])

            return {"entities": {"classes": classes, "functions": functions}, "dependencies": [], "imports": imports}
        except Exception as e:
            logger.error(f"Error parsing Python file {file_path} with regex: {e}", exc_info=True)
            return {"entities": {}, "dependencies": [], "imports": [], "raw_content": file_content[:2000], "error": str(e)}
    else:
        return {"entities": {}, "dependencies": [], "imports": [], "raw_content": file_content[:2000]}

def calculate_metrics(file_content: str, language: str, parsed_data: dict) -> dict:
    """Calculates basic code metrics."""
    lines_of_code = len(file_content.splitlines())

    entities = parsed_data.get("entities", {})
    number_of_classes = len(entities.get("classes", []))
    number_of_functions = len(entities.get("functions", []))

    if language == "python" and "classes" in entities:
        total_methods = number_of_functions
        for cls_info in entities["classes"]:
            total_methods += len(cls_info.get("methods", []))
        number_of_methods = total_methods
    else:
        number_of_methods = number_of_functions


    number_of_imports = len(parsed_data.get("imports", []))

    comment_density = 0.0 
    cyclomatic_complexity = 0 

    return {
        "lines_of_code": lines_of_code,
        "number_of_classes": number_of_classes,
        "number_of_functions_or_methods": number_of_methods,
        "comment_density": comment_density,
        "cyclomatic_complexity": cyclomatic_complexity,
        "number_of_imports": number_of_imports,
    }

def generate_tags(file_path: str, language: str, parsed_data: dict) -> list[str]:
    """Generates tags for a file based on its path, language, and entities."""
    tags = [language]

    try:
        normalized_path = os.path.normpath(file_path)
        parts = normalized_path.split(os.sep)
        tags.extend(p for p in parts[:-1] if p and p != '.')
    except Exception as e:
        logger.warning(f"Could not generate directory tags for {file_path}: {e}", exc_info=True)

    return list(set(tags))