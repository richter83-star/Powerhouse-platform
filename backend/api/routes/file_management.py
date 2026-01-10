
"""
File Management Routes
Handles upload, download, and management of input/output files
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Depends
from fastapi.responses import FileResponse, JSONResponse
from typing import List, Optional, Dict, Any
import os
import json
import shutil
from datetime import datetime
import logging
import mimetypes
import re
from pathlib import Path

from api.auth import get_current_user
from api.models import User

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
            candidate.mkdir(parents=True, exist_ok=True)
            return candidate
        except PermissionError:
            logger.warning("File storage root not writable: %s", candidate)
    raise RuntimeError("No writable file storage root found")


_BASE_STORAGE_ROOT = _init_storage_root()

_FILENAME_SAFE_RE = re.compile(r"[^A-Za-z0-9._-]")
_TENANT_SAFE_RE = re.compile(r"[^A-Za-z0-9._-]")


def _sanitize_tenant_id(tenant_id: Optional[str]) -> str:
    safe = _TENANT_SAFE_RE.sub("_", tenant_id or "default")
    safe = safe.strip(" .")
    return safe or "default"


def _get_tenant_paths(tenant_id: Optional[str]) -> Dict[str, Path]:
    safe_tenant = _sanitize_tenant_id(tenant_id)
    tenant_root = _BASE_STORAGE_ROOT / "tenants" / safe_tenant
    paths = {
        "uploads": tenant_root / "uploads",
        "outputs": tenant_root / "outputs",
        "templates": tenant_root / "templates",
        "samples": tenant_root / "samples",
        "history": tenant_root / "file_history.json",
    }
    for path in paths.values():
        if path.suffix:
            path.parent.mkdir(parents=True, exist_ok=True)
        else:
            path.mkdir(parents=True, exist_ok=True)
    return paths


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


def get_file_history(history_file: Path) -> Dict[str, Any]:
    """Load file history from JSON"""
    if history_file.exists():
        with history_file.open("r") as handle:
            return json.load(handle)
    return {"uploads": [], "outputs": []}


def save_file_history(history_file: Path, history: Dict[str, Any]) -> None:
    """Save file history to JSON"""
    with history_file.open("w") as handle:
        json.dump(history, handle, indent=2)


def add_to_history(history_file: Path, file_type: str, file_info: Dict[str, Any]) -> None:
    """Add a file entry to history"""
    history = get_file_history(history_file)
    if file_type not in history:
        history[file_type] = []
    history[file_type].insert(0, file_info)
    # Keep only last 100 entries
    history[file_type] = history[file_type][:100]
    save_file_history(history_file, history)


@router.post("/upload")
async def upload_file(
    files: List[UploadFile] = File(...),
    category: Optional[str] = "general",
    current_user: User = Depends(get_current_user)
):
    """Upload one or more files"""
    paths = _get_tenant_paths(current_user.tenant_id)
    uploads_dir = paths["uploads"]
    history_file = paths["history"]
    uploaded_files = []
    
    for file in files:
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_original_name = sanitize_filename(file.filename)
        filename = f"{timestamp}_{safe_original_name}"
        filepath = uploads_dir / filename
        
        # Save file
        with filepath.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get file info
        file_size = filepath.stat().st_size
        file_info = {
            "id": filename,
            "original_name": safe_original_name,
            "stored_name": filename,
            "category": category,
            "size": file_size,
            "uploaded_at": datetime.now().isoformat(),
            "path": str(filepath)
        }
        
        uploaded_files.append(file_info)
        add_to_history(history_file, "uploads", file_info)
    
    return {
        "success": True,
        "message": f"Successfully uploaded {len(uploaded_files)} file(s)",
        "files": uploaded_files
    }


@router.get("/files")
async def list_files(
    file_type: str = Query("uploads", description="Type: uploads, outputs, templates, samples"),
    limit: int = Query(50, description="Number of files to return"),
    current_user: User = Depends(get_current_user)
):
    """List files of a specific type"""
    paths = _get_tenant_paths(current_user.tenant_id)
    type_map = {
        "uploads": paths["uploads"],
        "outputs": paths["outputs"],
        "templates": paths["templates"],
        "samples": paths["samples"]
    }
    
    if file_type not in type_map:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    directory = type_map[file_type]
    files = []
    
    for entry in directory.iterdir():
        if entry.is_file():
            stat = entry.stat()
            filename = entry.name
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
