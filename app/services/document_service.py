from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from typing import List, Optional
from datetime import datetime
import os
import aiofiles
from pathlib import Path

from ..models import Document, DocumentType
from ..schemas.document import DocumentCreate, DocumentUpdate


async def create_document(db: AsyncSession, document_in: DocumentCreate, uploaded_by: int) -> Document:
    document = Document(
        project_id=document_in.project_id,
        uploaded_by=uploaded_by,
        title=document_in.title,
        description=document_in.description,
        document_type=document_in.document_type,
        file_name=document_in.file_name,
        file_path=document_in.file_path,
        file_size=document_in.file_size,
        mime_type=document_in.mime_type,
        tags=document_in.tags,
        category=document_in.category,
        is_public=document_in.is_public
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)
    return document


async def get_document_by_id(db: AsyncSession, document_id: int) -> Document | None:
    result = await db.execute(select(Document).where(Document.id == document_id))
    return result.scalars().first()


async def get_documents_for_project(db: AsyncSession, project_id: int) -> List[Document]:
    result = await db.execute(
        select(Document)
        .where(Document.project_id == project_id, Document.is_latest == True)
        .order_by(Document.created_at.desc())
    )
    return list(result.scalars().all())


async def update_document(db: AsyncSession, document_id: int, document_update: DocumentUpdate) -> Document | None:
    document = await get_document_by_id(db, document_id)
    if not document:
        return None
    
    update_data = document_update.dict(exclude_unset=True)
    if update_data:
        await db.execute(
            update(Document)
            .where(Document.id == document_id)
            .values(**update_data, updated_at=datetime.utcnow())
        )
        await db.commit()
        await db.refresh(document)
    
    return document


async def delete_document(db: AsyncSession, document_id: int) -> bool:
    document = await get_document_by_id(db, document_id)
    if not document:
        return False
    
    # Lösche physische Datei
    try:
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
    except Exception:
        pass  # Ignoriere Fehler beim Löschen der Datei
    
    await db.delete(document)
    await db.commit()
    return True


async def create_document_version(db: AsyncSession, document_id: int, new_file_path: str, new_file_size: int, uploaded_by: int) -> Document | None:
    """Erstellt eine neue Version eines Dokuments"""
    original_document = await get_document_by_id(db, document_id)
    if not original_document:
        return None
    
    # Markiere alle vorherigen Versionen als nicht-latest
    await db.execute(
        update(Document)
        .where(Document.parent_document_id == document_id)
        .values(is_latest=False)
    )
    
    # Erstelle neue Version
    new_version = Document(
        project_id=original_document.project_id,
        uploaded_by=uploaded_by,
        title=original_document.title,
        description=original_document.description,
        document_type=original_document.document_type,
        file_name=original_document.file_name,
        file_path=new_file_path,
        file_size=new_file_size,
        mime_type=original_document.mime_type,
        version=original_document.version + 1,
        is_latest=True,
        parent_document_id=document_id,
        tags=original_document.tags,
        category=original_document.category,
        is_public=original_document.is_public
    )
    
    db.add(new_version)
    await db.commit()
    await db.refresh(new_version)
    return new_version


async def search_documents(db: AsyncSession, search_term: str, project_id: Optional[int] = None, document_type: Optional[DocumentType] = None) -> List[Document]:
    query = select(Document).where(Document.is_latest == True)
    
    if project_id:
        query = query.where(Document.project_id == project_id)
    
    if document_type:
        query = query.where(Document.document_type == document_type)
    
    # Suche in Titel, Beschreibung und Tags
    search_filter = (
        Document.title.ilike(f"%{search_term}%") |
        Document.description.ilike(f"%{search_term}%") |
        Document.tags.ilike(f"%{search_term}%")
    )
    
    query = query.where(search_filter)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_document_statistics(db: AsyncSession, project_id: int) -> dict:
    """Holt Statistiken für Dokumente eines Projekts"""
    result = await db.execute(
        select(
            func.count(Document.id).label('total'),
            func.sum(Document.file_size).label('total_size'),
            func.count(Document.id).filter(Document.document_type == DocumentType.PLAN).label('plans'),
            func.count(Document.id).filter(Document.document_type == DocumentType.PERMIT).label('permits'),
            func.count(Document.id).filter(Document.document_type == DocumentType.QUOTE).label('quotes'),
            func.count(Document.id).filter(Document.document_type == DocumentType.INVOICE).label('invoices'),
            func.count(Document.id).filter(Document.document_type == DocumentType.CONTRACT).label('contracts')
        ).where(Document.project_id == project_id, Document.is_latest == True)
    )
    
    stats = result.first()
    if not stats:
        return {
            "total": 0,
            "total_size": 0,
            "plans": 0,
            "permits": 0,
            "quotes": 0,
            "invoices": 0,
            "contracts": 0
        }
    
    return {
        "total": stats.total or 0,
        "total_size": stats.total_size or 0,
        "plans": stats.plans or 0,
        "permits": stats.permits or 0,
        "quotes": stats.quotes or 0,
        "invoices": stats.invoices or 0,
        "contracts": stats.contracts or 0
    }


async def save_uploaded_file(file_content: bytes, filename: str, project_id: int) -> tuple[str, int]:
    """Speichert eine hochgeladene Datei und gibt den Pfad und die Größe zurück"""
    # Erstelle Projektordner
    upload_dir = Path(f"storage/uploads/project_{project_id}")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generiere eindeutigen Dateinamen
    file_path = upload_dir / filename
    
    # Speichere Datei
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(file_content)
    
    return str(file_path), len(file_content) 