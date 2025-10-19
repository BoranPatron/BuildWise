"""
Storage Path Management for BuildWise
Handles dynamic storage paths for local development and production (Render persistent disk)
"""
import os
from pathlib import Path
from typing import Optional


def is_production() -> bool:
    """Check if running in production environment (Render)"""
    return os.getenv("RENDER") == "true" or os.getenv("ENVIRONMENT") == "production"


def get_storage_base_path() -> Path:
    """
    Get the base storage path based on environment.
    
    Returns:
        Path: Storage base path
            - Production (Render with persistent disk): /storage
            - Production (Render without persistent disk): /tmp/storage (ephemeral)
            - Development: ./storage
    """
    if is_production():
        # Try persistent disk first
        persistent_disk = Path("/storage")
        
        # Check if persistent disk is available and writable
        if persistent_disk.exists() and os.access(persistent_disk, os.W_OK):
            base_path = persistent_disk
        else:
            # Fallback to temporary storage (ephemeral, lost on restart)
            base_path = Path("/tmp/storage")
            print("[WARNING] Persistent disk not available - using temporary storage")
            print("[WARNING] Files will be LOST on service restart!")
    else:
        # Development: use local storage directory
        base_path = Path("storage")
    
    # Ensure directory exists (but don't create parent directories in production)
    if is_production() and str(base_path).startswith("/storage"):
        # In production, only create if mount point exists
        if base_path.exists():
            base_path.mkdir(parents=True, exist_ok=True)
        else:
            # Fallback to temporary storage
            base_path = Path("/tmp/storage")
            base_path.mkdir(parents=True, exist_ok=True)
    else:
        # In development or for /tmp paths, create normally
        base_path.mkdir(parents=True, exist_ok=True)
    
    return base_path


def get_uploads_path() -> Path:
    """Get the uploads directory path"""
    uploads_path = get_storage_base_path() / "uploads"
    uploads_path.mkdir(exist_ok=True)
    return uploads_path


def get_project_upload_path(project_id: int) -> Path:
    """
    Get upload path for a specific project.
    
    Args:
        project_id: Project ID
        
    Returns:
        Path: Project-specific upload directory
    """
    project_path = get_uploads_path() / f"project_{project_id}"
    project_path.mkdir(exist_ok=True)
    return project_path


def get_temp_path() -> Path:
    """Get temporary files directory"""
    temp_path = get_storage_base_path() / "temp"
    temp_path.mkdir(exist_ok=True)
    return temp_path


def get_pdf_path() -> Path:
    """Get PDF output directory"""
    pdf_path = get_storage_base_path() / "pdfs"
    pdf_path.mkdir(exist_ok=True)
    return pdf_path


def get_invoice_path() -> Path:
    """Get invoice PDF directory"""
    invoice_path = get_pdf_path() / "invoices"
    invoice_path.mkdir(exist_ok=True)
    return invoice_path


def get_cache_path() -> Path:
    """Get cache directory"""
    cache_path = get_storage_base_path() / "cache"
    cache_path.mkdir(exist_ok=True)
    return cache_path


def get_relative_path(absolute_path: Path) -> str:
    """
    Convert absolute storage path to relative path for database storage.
    
    Args:
        absolute_path: Absolute path to file
        
    Returns:
        str: Relative path from storage base
    """
    try:
        base_path = get_storage_base_path()
        relative = absolute_path.relative_to(base_path)
        return str(relative)
    except ValueError:
        # Path is not relative to base, return as-is
        return str(absolute_path)


def resolve_storage_path(relative_path: str) -> Path:
    """
    Resolve relative storage path to absolute path.
    
    Args:
        relative_path: Relative path from storage base
        
    Returns:
        Path: Absolute path to file
    """
    # Clean up the path
    clean_path = relative_path.replace("\\", "/").lstrip("/")
    
    # Remove 'storage/' prefix if present
    if clean_path.startswith("storage/"):
        clean_path = clean_path[8:]
    
    # Resolve to absolute path
    absolute_path = get_storage_base_path() / clean_path
    return absolute_path


def ensure_storage_structure():
    """
    Ensure all required storage directories exist.
    Should be called on application startup.
    """
    directories = [
        get_storage_base_path(),
        get_uploads_path(),
        get_temp_path(),
        get_pdf_path(),
        get_invoice_path(),
        get_cache_path(),
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    
    print(f"[SUCCESS] Storage structure initialized at: {get_storage_base_path()}")
    
    # Log storage information
    if is_production():
        print("[INFO] Running in PRODUCTION mode - using Render persistent disk")
    else:
        print("[INFO] Running in DEVELOPMENT mode - using local storage")
    
    return True


def get_file_url(file_path: str, token: Optional[str] = None) -> str:
    """
    Generate URL for accessing a file through the API.
    
    Args:
        file_path: Relative file path from storage base
        token: Optional JWT token for authentication
        
    Returns:
        str: URL to access the file
    """
    # Clean path
    clean_path = file_path.replace("\\", "/").lstrip("/")
    if clean_path.startswith("storage/"):
        clean_path = clean_path[8:]
    
    # Build URL
    if token:
        return f"/api/v1/files/serve/{clean_path}?token={token}"
    else:
        return f"/storage/{clean_path}"


# Export all functions
__all__ = [
    "is_production",
    "get_storage_base_path",
    "get_uploads_path",
    "get_project_upload_path",
    "get_temp_path",
    "get_pdf_path",
    "get_invoice_path",
    "get_cache_path",
    "get_relative_path",
    "resolve_storage_path",
    "ensure_storage_structure",
    "get_file_url",
]

