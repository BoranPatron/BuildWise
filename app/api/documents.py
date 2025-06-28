from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..api.deps import get_current_user
from ..models import User, DocumentType
from ..schemas.document import DocumentRead, DocumentUpdate, DocumentSummary, DocumentUpload, DocumentCreate
from ..services.document_service import (
    create_document, get_document_by_id, get_documents_for_project,
    update_document, delete_document, search_documents, get_document_statistics,
    save_uploaded_file
)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    project_id: int,
    title: str,
    description: str = None,
    document_type: DocumentType = DocumentType.OTHER,
    tags: str = None,
    category: str = None,
    is_public: bool = False,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lädt ein neues Dokument hoch"""
    # Speichere Datei
    file_content = await file.read()
    file_path, file_size = await save_uploaded_file(file_content, file.filename, project_id)
    
    # Erstelle Dokument-Eintrag
    document_in = DocumentUpload(
        title=title,
        description=description,
        document_type=document_type,
        tags=tags,
        category=category,
        is_public=is_public
    )
    
    document = await create_document(
        db,
        DocumentCreate(
            project_id=project_id,
            file_name=file.filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=file.content_type or "application/octet-stream",
            **document_in.dict()
        ),
        current_user.id
    )
    
    return document


@router.get("/", response_model=List[DocumentSummary])
async def read_documents(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    documents = await get_documents_for_project(db, project_id)
    return documents


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
    project_id: int = None,
    document_type: DocumentType = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Sucht nach Dokumenten"""
    documents = await search_documents(db, q, project_id, document_type)
    return documents 