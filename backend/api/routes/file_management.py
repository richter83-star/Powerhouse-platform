
"""
File Management Routes
Handles upload, download, and management of input/output files
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Depends
from fastapi.responses import FileResponse, JSONResponse
from typing import List, Optional
import os
import json
import shutil
from datetime import datetime
import logging
import mimetypes
import re
from pathlib import Path

from api.auth import get_current_user

router = APIRouter(dependencies=[Depends(get_current_user)])

logger = logging.getLogger(__name__)

# Base directories for file storage
_DEFAULT_ROOT = Path(__file__).resolve().parents[2] / "data_io"
_ENV_ROOT = os.getenv("FILE_STORAGE_ROOT")
_FALLBACK_ROOT = Path(os.getenv("FILE_STORAGE_FALLBACK", "/tmp/powerhouse-data"))


def _init_storage_root() -> Path:
    # Prefer explicit config, then repo data_io, then a safe writable fallback.
    candidates = [Path(_ENV_ROOT)] if _ENV_ROOT else []
    candidates.extend([_DEFAULT_ROOT, _FALLBACK_ROOT])
    for candidate in candidates:
        try:
            (candidate / "uploads").mkdir(parents=True, exist_ok=True)
            (candidate / "outputs").mkdir(parents=True, exist_ok=True)
            (candidate / "templates").mkdir(parents=True, exist_ok=True)
            (candidate / "samples").mkdir(parents=True, exist_ok=True)
            return candidate
        except PermissionError:
            logger.warning("File storage root not writable: %s", candidate)
    raise RuntimeError("No writable file storage root found")


_STORAGE_ROOT = _init_storage_root()
UPLOADS_DIR = str(_STORAGE_ROOT / "uploads")
OUTPUTS_DIR = str(_STORAGE_ROOT / "outputs")
TEMPLATES_DIR = str(_STORAGE_ROOT / "templates")
SAMPLES_DIR = str(_STORAGE_ROOT / "samples")
HISTORY_FILE = str(_STORAGE_ROOT / "file_history.json")

_FILENAME_SAFE_RE = re.compile(r"[^A-Za-z0-9._-]")


def sanitize_filename(filename: str) -> str:
    name = os.path.basename(filename or "")
    name = _FILENAME_SAFE_RE.sub("_", name)
    name = name.strip(" .")
    return name or "file"


def validate_filename(filename: str) -> str:
    safe_name = sanitize_filename(filename)
    if filename != safe_name:
        raise HTTPException(status_code=400, detail="Invalid filename")
    return safe_name


def resolve_safe_path(base_dir: str, filename: str) -> tuple[str, str]:
    safe_name = validate_filename(filename)
    base = os.path.abspath(base_dir)
    path = os.path.abspath(os.path.join(base, safe_name))
    if not path.startswith(base + os.sep):
        raise HTTPException(status_code=400, detail="Invalid filename")
    return path, safe_name


def get_file_history():
    """Load file history from JSON"""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    return {"uploads": [], "outputs": []}


def save_file_history(history):
    """Save file history to JSON"""
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)


def add_to_history(file_type, file_info):
    """Add a file entry to history"""
    history = get_file_history()
    if file_type not in history:
        history[file_type] = []
    history[file_type].insert(0, file_info)
    # Keep only last 100 entries
    history[file_type] = history[file_type][:100]
    save_file_history(history)


@router.post("/upload")
async def upload_file(
    files: List[UploadFile] = File(...),
    category: Optional[str] = "general"
):
    """Upload one or more files"""
    uploaded_files = []
    
    for file in files:
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_original_name = sanitize_filename(file.filename)
        filename = f"{timestamp}_{safe_original_name}"
        filepath = os.path.join(UPLOADS_DIR, filename)
        
        # Save file
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get file info
        file_size = os.path.getsize(filepath)
        file_info = {
            "id": filename,
            "original_name": safe_original_name,
            "stored_name": filename,
            "category": category,
            "size": file_size,
            "uploaded_at": datetime.now().isoformat(),
            "path": filepath
        }
        
        uploaded_files.append(file_info)
        add_to_history("uploads", file_info)
    
    return {
        "success": True,
        "message": f"Successfully uploaded {len(uploaded_files)} file(s)",
        "files": uploaded_files
    }


@router.get("/files")
async def list_files(
    file_type: str = Query("uploads", description="Type: uploads, outputs, templates, samples"),
    limit: int = Query(50, description="Number of files to return")
):
    """List files of a specific type"""
    type_map = {
        "uploads": UPLOADS_DIR,
        "outputs": OUTPUTS_DIR,
        "templates": TEMPLATES_DIR,
        "samples": SAMPLES_DIR
    }
    
    if file_type not in type_map:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    directory = type_map[file_type]
    files = []
    
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            stat = os.stat(filepath)
            files.append({
                "id": filename,
                "name": filename,
                "size": stat.st_size,
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "type": file_type,
                "mime_type": mimetypes.guess_type(filename)[0] or "application/octet-stream"
            })
    
    # Sort by modification time (newest first)
    files.sort(key=lambda x: x["modified_at"], reverse=True)
    
    return {
        "success": True,
        "files": files[:limit],
        "total": len(files)
    }


@router.get("/download/{file_type}/{filename}")
async def download_file(file_type: str, filename: str):
    """Download a specific file"""
    type_map = {
        "uploads": UPLOADS_DIR,
        "outputs": OUTPUTS_DIR,
        "templates": TEMPLATES_DIR,
        "samples": SAMPLES_DIR
    }
    
    if file_type not in type_map:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    filepath, safe_name = resolve_safe_path(type_map[file_type], filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=filepath,
        filename=safe_name,
        media_type="application/octet-stream"
    )


@router.delete("/delete/{file_type}/{filename}")
async def delete_file(file_type: str, filename: str):
    """Delete a specific file"""
    type_map = {
        "uploads": UPLOADS_DIR,
        "outputs": OUTPUTS_DIR,
        "templates": TEMPLATES_DIR,
        "samples": SAMPLES_DIR
    }
    
    if file_type not in type_map:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    filepath, safe_name = resolve_safe_path(type_map[file_type], filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    
    os.remove(filepath)
    
    return {
        "success": True,
        "message": f"File {safe_name} deleted successfully"
    }


@router.get("/history")
async def get_history(limit: int = Query(50)):
    """Get file upload/output history"""
    history = get_file_history()
    
    return {
        "success": True,
        "history": {
            "uploads": history.get("uploads", [])[:limit],
            "outputs": history.get("outputs", [])[:limit]
        }
    }


@router.post("/save-output")
async def save_output(data: dict):
    """Save processing output to file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_name = sanitize_filename(data.get("name", "output"))
    filename = f"{timestamp}_{output_name}.json"
    filepath = os.path.join(OUTPUTS_DIR, filename)
    
    # Save output data
    with open(filepath, 'w') as f:
        json.dump(data.get("content", {}), f, indent=2)
    
    file_info = {
        "id": filename,
        "name": filename,
        "size": os.path.getsize(filepath),
        "created_at": datetime.now().isoformat(),
        "type": "output",
        "path": filepath
    }
    
    add_to_history("outputs", file_info)
    
    return {
        "success": True,
        "message": "Output saved successfully",
        "file": file_info
    }


@router.get("/templates/list")
async def list_templates():
    """Get available templates"""
    templates = []
    
    for filename in os.listdir(TEMPLATES_DIR):
        filepath = os.path.join(TEMPLATES_DIR, filename)
        if os.path.isfile(filepath):
            with open(filepath, 'r') as f:
                try:
                    content = json.load(f)
                    templates.append({
                        "id": filename,
                        "name": content.get("name", filename),
                        "description": content.get("description", ""),
                        "category": content.get("category", "general"),
                        "filename": filename
                    })
                except:
                    pass
    
    return {
        "success": True,
        "templates": templates
    }


@router.get("/templates/{filename}")
async def get_template(filename: str):
    """Get a specific template"""
    filepath, safe_name = resolve_safe_path(TEMPLATES_DIR, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Template not found")
    
    with open(filepath, 'r') as f:
        content = json.load(f)
    
    return {
        "success": True,
        "template": content
    }


@router.get("/samples/list")
async def list_samples():
    """Get available sample files"""
    samples = []
    
    for filename in os.listdir(SAMPLES_DIR):
        filepath = os.path.join(SAMPLES_DIR, filename)
        if os.path.isfile(filepath):
            stat = os.stat(filepath)
            samples.append({
                "id": filename,
                "name": filename,
                "size": stat.st_size,
                "type": mimetypes.guess_type(filename)[0] or "application/octet-stream"
            })
    
    return {
        "success": True,
        "samples": samples
    }


@router.get("/stats")
async def get_file_stats():
    """Get file storage statistics"""
    def get_dir_size(directory):
        total = 0
        count = 0
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            if os.path.isfile(filepath):
                total += os.path.getsize(filepath)
                count += 1
        return total, count
    
    uploads_size, uploads_count = get_dir_size(UPLOADS_DIR)
    outputs_size, outputs_count = get_dir_size(OUTPUTS_DIR)
    templates_size, templates_count = get_dir_size(TEMPLATES_DIR)
    samples_size, samples_count = get_dir_size(SAMPLES_DIR)
    
    return {
        "success": True,
        "stats": {
            "uploads": {"size": uploads_size, "count": uploads_count},
            "outputs": {"size": outputs_size, "count": outputs_count},
            "templates": {"size": templates_size, "count": templates_count},
            "samples": {"size": samples_size, "count": samples_count},
            "total_size": uploads_size + outputs_size + templates_size + samples_size,
            "total_count": uploads_count + outputs_count + templates_count + samples_count
        }
    }
