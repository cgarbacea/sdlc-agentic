import os
from langchain_core.tools import tool
from config import ALLOWED_ROOTS


@tool
def list_directory(directory_path: str) -> str:
    """Lists all files and folders in a given directory."""
    try:
        files = os.listdir(directory_path)
        return f"Contents of {directory_path}: {', '.join(files)}"
    except Exception as e:
        return f"Error reading directory: {str(e)}"


@tool
def read_file(file_path: str) -> str:
    """Reads the contents of a specific file."""
    try:
        with open(file_path, "r") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"


@tool
def write_file(file_path: str, content: str) -> str:
    """Writes new code or updates to a specific file."""
    resolved = os.path.realpath(file_path)
    if not any(resolved.startswith(root) for root in ALLOWED_ROOTS):
        return f"Error: path '{file_path}' is outside the allowed workspace. Write only to FE or BE repo folders."
    try:
        dir_name = os.path.dirname(resolved)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        with open(resolved, "w") as f:
            f.write(content)
        print(f"💾 [FILE SYSTEM] Wrote to {resolved}")
        return f"Successfully wrote to {resolved}"
    except Exception as e:
        return f"Error writing file: {str(e)}"
