from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import mimetypes

from ..core.database import get_db
from ..api.deps import get_current_user
from ..models import User
from ..services.google_drive_service import GoogleDriveService, GoogleDriveUnavailable

router = APIRouter(prefix="/visualizations", tags=["visualizations"])


@router.get("/")
async def list_visualizations(
    project_id: int,
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Liefert verfügbare Visualisierungs-Dateien zurück.

    Lokaler Speicherort (Fallback) wurde vereinheitlicht auf:
    storage/projects/project_<id>/visualization_results/<category>/
    Kategorien: interior | exterior | individual
    Google-Drive-Liste kann optional später ergänzt werden.
    """
    import os

    base_results = os.path.join("storage", "projects", f"project_{project_id}", "visualization_results")
    base_docs = os.path.join("storage", "projects", f"project_{project_id}", "uploaded_documents")
    os.makedirs(base_results, exist_ok=True)
    os.makedirs(base_docs, exist_ok=True)
    results: List[Dict[str, Any]] = []

    if category:
        categories = [category]
        # Stelle sicher, dass die Kategorieordner existieren
        os.makedirs(os.path.join(base_results, category), exist_ok=True)
        os.makedirs(os.path.join(base_docs, category), exist_ok=True)
    else:
        # alle Unterordner
        default_cats = ["interior", "exterior", "individual"]
        for dc in default_cats:
            os.makedirs(os.path.join(base_results, dc), exist_ok=True)
            os.makedirs(os.path.join(base_docs, dc), exist_ok=True)
        # Sammle Kategorien aus beiden Bäumen
        cats_results = [d for d in os.listdir(base_results) if os.path.isdir(os.path.join(base_results, d))]
        cats_docs = [d for d in os.listdir(base_docs) if os.path.isdir(os.path.join(base_docs, d))]
        categories = sorted(list(set(cats_results + cats_docs)))

    idx = 1
    for cat in categories:
        # Hochgeladene Dokumente
        docs_folder = os.path.join(base_docs, cat)
        if os.path.isdir(docs_folder):
            for name in sorted(os.listdir(docs_folder)):
                path = os.path.join(docs_folder, name)
                if not os.path.isfile(path):
                    continue
                url = f"/storage/projects/project_{project_id}/uploaded_documents/{cat}/{name}"
                results.append(
                    {
                        "id": idx,
                        "project_id": project_id,
                        "category": cat,
                        "title": name,
                        "description": None,
                        # UI erwartet plan_url für hochgeladene Dokumente
                        "plan_url": url,
                        "status": "COMPLETED",
                    }
                )
                idx += 1

        # Visualisierungsergebnisse
        res_folder = os.path.join(base_results, cat)
        if os.path.isdir(res_folder):
            for name in sorted(os.listdir(res_folder)):
                path = os.path.join(res_folder, name)
                if not os.path.isfile(path):
                    continue
                url = f"/storage/projects/project_{project_id}/visualization_results/{cat}/{name}"
                results.append(
                    {
                        "id": idx,
                        "project_id": project_id,
                        "category": cat,
                        "title": name,
                        "description": None,
                        # UI erwartet result_url
                        "result_url": url,
                        "status": "COMPLETED",
                    }
                )
                idx += 1

    return results


@router.post("/upload-plan")
async def upload_plan(
    project_id: int = Form(...),
    category: str = Form(...),
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Nimmt eine Datei entgegen und lädt sie nach Google Drive in den bereitgestellten Ordnerbaum.
    Fällt automatisch auf lokalen Storage (storage/projects/.../visualization_results/...) zurück, wenn Drive nicht verfügbar ist.
    """
    try:
        content = await file.read()
        filename = file.filename or "upload"
        mimetype = file.content_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"

        # Erst versuchen wir Google Drive
        try:
            gds = GoogleDriveService()
            file_id, web_link = gds.upload_bytes(
                data=content,
                filename=filename,
                project_id=project_id,
                category=category,
                mimetype=mimetype,
            )
            return {
                "storage": "gdrive",
                "file_id": file_id,
                "url": web_link,
                "filename": filename,
                "project_id": project_id,
                "category": category,
                "title": title,
                "description": description,
            }
        except GoogleDriveUnavailable as exc:
            # Fallback auf lokalen Storage
            import os
            # standardisiere Kategorie (falls leer) auf 'interior' und speichere unter uploaded_documents
            safe_category = category or "interior"
            base_up = os.path.join("storage", "projects", f"project_{project_id}", "uploaded_documents", safe_category)
            os.makedirs(base_up, exist_ok=True)
            path = os.path.join(base_up, filename)
            with open(path, "wb") as f:
                f.write(content)
            # baue URL über StaticFiles-Mount
            url = f"/storage/projects/project_{project_id}/uploaded_documents/{safe_category}/{filename}"
            return {
                "storage": "local",
                "url": url,
                "filename": filename,
                "project_id": project_id,
                "category": safe_category,
                "title": title,
                "description": description,
                "note": str(exc),
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


