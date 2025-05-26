import os
import sys
from typing import Optional

def setup_imports(current_file: str) -> None:
    """
    Set up import paths for the project structure.
    
    This function should be called at the top of any module that needs to import
    from the src/ or backend/ directories.
    
    Args:
        current_file (str): The __file__ variable from the calling module
    """
    # Get the directory of the current file
    current_dir = os.path.dirname(os.path.abspath(current_file))
    
    # Find the src directory
    src_path = _find_src_directory(current_dir)
    if src_path and src_path not in sys.path:
        sys.path.insert(0, src_path)
    
    # Find the backend directory (project root)
    backend_path = _find_backend_directory(current_dir)
    if backend_path and backend_path not in sys.path:
        sys.path.insert(0, backend_path)


def _find_src_directory(start_path: str) -> Optional[str]:
    """
    Find the src directory by walking up the directory tree.
    
    Args:
        start_path (str): Starting directory path
        
    Returns:
        Optional[str]: Path to src directory if found
    """
    current = start_path
    max_levels = 5  # Prevent infinite loops
    
    for _ in range(max_levels):
        # Check if we're already in src or if src exists as a sibling
        if os.path.basename(current) == "src":
            return current
        
        src_candidate = os.path.join(current, "src")
        if os.path.isdir(src_candidate):
            return src_candidate
        
        # Move up one level
        parent = os.path.dirname(current)
        if parent == current:  # Reached root
            break
        current = parent
    
    return None


def _find_backend_directory(start_path: str) -> Optional[str]:
    """
    Find the backend directory (project root) by walking up the directory tree.
    
    Args:
        start_path (str): Starting directory path
        
    Returns:
        Optional[str]: Path to backend directory if found
    """
    current = start_path
    max_levels = 5  # Prevent infinite loops
    
    for _ in range(max_levels):
        # Check for backend indicators (config directory, specific files)
        if (os.path.isdir(os.path.join(current, "config")) and 
            os.path.isdir(os.path.join(current, "src"))):
            return current
        
        # Check if we're in a directory named "backend"
        if os.path.basename(current) == "backend":
            return current
        
        # Move up one level
        parent = os.path.dirname(current)
        if parent == current:  # Reached root
            break
        current = parent
    
    return None


def get_project_paths(current_file: str) -> dict:
    """
    Get all relevant project paths.
    
    Args:
        current_file (str): The __file__ variable from the calling module
        
    Returns:
        dict: Dictionary containing project paths
    """
    current_dir = os.path.dirname(os.path.abspath(current_file))
    
    return {
        "current_dir": current_dir,
        "src_path": _find_src_directory(current_dir),
        "backend_path": _find_backend_directory(current_dir),
    } 