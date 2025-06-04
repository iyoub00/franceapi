# app/utils/file_validation.py
# This file contains functions for validating uploaded files.
# Author: Yassine Amounane
import logging
import magic
from pathlib import Path

logger = logging.getLogger(__name__)

SUPPORTED_MIME_TYPES = {
    "application/pdf": ".pdf",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "text/plain": ".txt",
}

def validate_file(file_path: str) -> tuple[bool, str]:
    try:
        p = Path(file_path)
        if not p.exists():
            message = f"File not found: {file_path}"
            logger.warning(message)
            return False, message

        file_size = p.stat().st_size
        if file_size == 0:
            message = "Empty file"
            logger.warning(f"{message}: {file_path}")
            return False, message
        
        mime = magic.from_file(file_path, mime=True)
        if mime not in SUPPORTED_MIME_TYPES:
            message = f"Unsupported MIME type: {mime}"
            logger.warning(f"{message} for file: {file_path}")
            return False, message
        
        success_message = f"Supported type: {mime} ({SUPPORTED_MIME_TYPES[mime]})"
        logger.info(f"File validation successful for {file_path}: {success_message}")
        return True, success_message
    
    except FileNotFoundError:
        message = f"File not found during validation: {file_path}"
        logger.warning(message)
        return False, message
    except magic.MagicException as e:
        message = f"Magic library error during validation for {file_path}: {e}"
        logger.error(message, exc_info=True)
        return False, message
    except IOError as e: # Catching broader I/O errors that might include PermissionError
        message = f"IO error during file validation for {file_path}: {e}"
        logger.error(message, exc_info=True)
        return False, message
    except Exception as e:
        message = f"Unexpected error during file validation for {file_path}: {e}"
        logger.error(message, exc_info=True)
        return False, message
