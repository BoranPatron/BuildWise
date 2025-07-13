from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
import os

from ..core.database import get_db
from ..api.deps import get_current_user
from ..models import User, DocumentType
from ..schemas.document import DocumentRead, DocumentUpdate, DocumentSummary, DocumentUpload, DocumentCreate
from ..services.document_service import (
    create_document, get_document_by_id, get_documents_for_project,
    update_document, delete_document, search_documents, get_document_statistics,
    save_uploaded_file
)

router = APIRouter(tags=["documents"])


@router.post("/upload", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    project_id: int = Form(...),
    title: str = Form(...),
    description: str = Form(None),
    document_type: DocumentType = Form(DocumentType.OTHER),
    tags: str = Form(None),
    category: str = Form(None),
    is_public: bool = Form(False),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lädt ein neues Dokument hoch"""
    try:
        # Validiere Eingabedaten
        if not title or not title.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dokumententitel ist erforderlich"
            )
        
        if not project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Projekt-ID ist erforderlich"
            )
        
        if not file or file.size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Datei ist erforderlich"
            )
        
        # Prüfe Dateigröße (10MB Limit)
        if file.size and file.size > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Datei ist zu groß. Maximale Größe: 10MB"
            )
        
        # Speichere Datei
        file_content = await file.read()
        filename = file.filename or "unnamed_file"
        file_path, file_size = await save_uploaded_file(file_content, filename, project_id)
        
        # Erstelle Dokument-Eintrag
        document_in = DocumentUpload(
            title=title.strip(),
            description=description.strip() if description else None,
            document_type=document_type,
            tags=tags.strip() if tags else None,
            category=category.strip() if category else None,
            is_public=is_public
        )
        
        document = await create_document(
            db,
            DocumentCreate(
                project_id=project_id,
                file_name=filename,
                file_path=file_path,
                file_size=file_size,
                mime_type=file.content_type or "application/octet-stream",
                **document_in.dict()
            ),
            getattr(current_user, 'id', 0)
        )
        
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error uploading document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Hochladen des Dokuments"
        )


@router.get("/", response_model=List[DocumentSummary])
async def read_documents(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    documents = await get_documents_for_project(db, project_id)
    return documents


@router.get("/{document_id}/download", response_class=FileResponse)
async def download_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lädt ein Dokument herunter"""
    document = await get_document_by_id(db, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dokument nicht gefunden"
        )
    
    # Prüfe ob die Datei existiert
    file_path = str(document.file_path)
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Datei nicht gefunden"
        )
    
    return FileResponse(
        path=file_path,
        filename=str(document.file_name),
        media_type=str(document.mime_type)
    )


@router.get("/{document_id}/view")
async def view_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Zeigt ein Dokument an (für Browser-Vorschau)"""
    document = await get_document_by_id(db, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dokument nicht gefunden"
        )
    
    # Prüfe ob die Datei existiert
    file_path = str(document.file_path)
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Datei nicht gefunden"
        )
    
    try:
        # Lade den Dateiinhalt
        with open(file_path, 'rb') as f:
            content = f.read()
        
        mime_type = str(document.mime_type)
        
        # Für Textdateien: Konvertiere zu String
        if mime_type.startswith('text/') or mime_type in ['application/json', 'application/xml']:
            try:
                text_content = content.decode('utf-8')
                return {
                    "type": "text",
                    "content": text_content,
                    "mime_type": mime_type,
                    "encoding": "utf-8"
                }
            except UnicodeDecodeError:
                # Fallback für andere Encodings
                text_content = content.decode('latin-1')
                return {
                    "type": "text",
                    "content": text_content,
                    "mime_type": mime_type,
                    "encoding": "latin-1"
                }
        
        # Für Bilder: Base64-kodiert
        elif mime_type.startswith('image/'):
            import base64
            encoded_content = base64.b64encode(content).decode('utf-8')
            return {
                "type": "image",
                "content": encoded_content,
                "mime_type": mime_type,
                "encoding": "base64"
            }
        
        # Für PDFs: Base64-kodiert
        elif mime_type == 'application/pdf':
            import base64
            encoded_content = base64.b64encode(content).decode('utf-8')
            return {
                "type": "pdf",
                "content": encoded_content,
                "mime_type": mime_type,
                "encoding": "base64"
            }
        
        # Für andere Dateien: Nicht unterstützt
        else:
            return {
                "type": "unsupported",
                "mime_type": mime_type,
                "message": "Dieser Dateityp wird für die Vorschau nicht unterstützt"
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Lesen der Datei: {str(e)}"
        )


@router.get("/{document_id}", response_model=DocumentRead)
async def read_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    document = await get_document_by_id(db, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dokument nicht gefunden"
        )
    return document


@router.put("/{document_id}", response_model=DocumentRead)
async def update_document_endpoint(
    document_id: int,
    document_update: DocumentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    document = await get_document_by_id(db, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dokument nicht gefunden"
        )
    
    updated_document = await update_document(db, document_id, document_update)
    return updated_document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document_endpoint(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    document = await get_document_by_id(db, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dokument nicht gefunden"
        )
    
    success = await delete_document(db, document_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dokument konnte nicht gelöscht werden"
        )
    
    return None


@router.get("/project/{project_id}/statistics")
async def get_project_document_statistics(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Holt Statistiken für Dokumente eines Projekts"""
    stats = await get_document_statistics(db, project_id)
    return stats


@router.get("/search", response_model=List[DocumentSummary])
async def search_documents_endpoint(
    q: str = Query(..., min_length=2, description="Suchbegriff"),
    project_id: Optional[int] = None,
    document_type: Optional[DocumentType] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Sucht nach Dokumenten"""
    documents = await search_documents(db, q, project_id, document_type)
    return documents


@router.get("/{document_id}/content")
async def get_document_content(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Gibt den Inhalt eines Dokuments als JSON zurück"""
    document = await get_document_by_id(db, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dokument nicht gefunden"
        )
    
    # Prüfe ob die Datei existiert
    file_path = str(document.file_path)
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Datei nicht gefunden"
        )
    
    try:
        # Lade den Dateiinhalt
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # Für Textdateien: Konvertiere zu String
        mime_type = str(document.mime_type)
        if mime_type.startswith('text/') or mime_type in ['application/json', 'application/xml']:
            try:
                text_content = content.decode('utf-8')
                return {
                    "content": text_content,
                    "mime_type": mime_type,
                    "encoding": "utf-8"
                }
            except UnicodeDecodeError:
                # Fallback für andere Encodings
                text_content = content.decode('latin-1')
                return {
                    "content": text_content,
                    "mime_type": mime_type,
                    "encoding": "latin-1"
                }
        else:
            # Für Binärdateien: Base64-kodiert
            import base64
            encoded_content = base64.b64encode(content).decode('utf-8')
            return {
                "content": encoded_content,
                "mime_type": mime_type,
                "encoding": "base64"
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Lesen der Datei: {str(e)}"
        ) 