from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, text
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime
import os
import aiofiles
from pathlib import Path
import logging

from ..models import Document
from ..schemas.document import DocumentCreate, DocumentUpdate, DocumentTypeEnum
from ..models.user import User

logger = logging.getLogger(__name__)


async def create_document(db: AsyncSession, document_in: DocumentCreate, uploaded_by: int) -> Document:
    document = Document(
        project_id=document_in.project_id,
        uploaded_by=uploaded_by,
        title=document_in.title,
        description=document_in.description,
        document_type=document_in.document_type.value,  # Enum-Wert verwenden
        file_name=document_in.file_name,
        file_path=document_in.file_path,
        file_size=document_in.file_size,
        mime_type=document_in.mime_type,
        tags=document_in.tags,
        category=document_in.category.value if document_in.category else None,  # Enum-Wert verwenden
        subcategory=document_in.subcategory,
        is_public=document_in.is_public,
        # Neue DMS-Felder mit Standardwerten
        version_number=document_in.version_number or "1.0.0",
        version_major=1,
        version_minor=0,
        version_patch=0,
        is_latest_version=True,
        document_status="DRAFT",
        workflow_stage="UPLOADED",
        approval_status="PENDING",
        review_status="NOT_REVIEWED",
        access_level="INTERNAL"
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)
    
    # Credit-Zuordnung für Bauträger
    try:
        from ..services.credit_service import CreditService
        from ..models.credit_event import CreditEventType
        from ..models.user import UserRole
        
        # Prüfe ob User ein Bauträger ist
        user_result = await db.execute(
            select(User).where(User.id == uploaded_by)
        )
        user = user_result.scalar_one_or_none()
        
        if user and user.user_role == UserRole.BAUTRAEGER:
            # Füge Credits für hochgeladenes Dokument hinzu
            await CreditService.add_credits_for_activity(
                db=db,
                user_id=uploaded_by,
                event_type=CreditEventType.DOCUMENT_UPLOADED,
                description=f"Dokument hochgeladen: {document_in.title}",
                related_entity_type="document",
                related_entity_id=document.id
            )
            print(f"[SUCCESS] Credits für Bauträger {uploaded_by} hinzugefügt: Dokument hochgeladen")
        else:
            print(f"ℹ️  User {uploaded_by} ist kein Bauträger, keine Credits hinzugefügt")
            
    except Exception as e:
        print(f"[ERROR] Fehler bei Credit-Zuordnung: {e}")
        # Fehler bei Credit-Zuordnung sollte nicht die Dokument-Erstellung blockieren
    
    return document


async def get_document_by_id(db: AsyncSession, document_id: int) -> Document | None:
    result = await db.execute(
        select(Document)
        .options(
            selectinload(Document.versions),
            selectinload(Document.status_history),
            selectinload(Document.shares),
            selectinload(Document.access_logs)
        )
        .where(Document.id == document_id)
    )
    return result.scalars().first()


async def get_documents_for_project(db: AsyncSession, project_id: int) -> List[Document]:
    """Robuste Funktion zum Laden von Dokumenten für ein Projekt"""
    try:
        logger.info(f"[DOCUMENT_SERVICE] Lade Dokumente für Projekt {project_id}")
        
        # Prüfe ob Projekt existiert
        from sqlalchemy import text
        project_check = text("SELECT id FROM projects WHERE id = :project_id")
        project_result = await db.execute(project_check, {"project_id": project_id})
        project_exists = project_result.fetchone()
        
        if not project_exists:
            logger.warning(f"[DOCUMENT_SERVICE] Projekt {project_id} existiert nicht")
            return []
        
        # Lade Dokumente mit robuster Fehlerbehandlung
        result = await db.execute(
            select(Document)
            .options(
                selectinload(Document.versions),
                selectinload(Document.status_history),
                selectinload(Document.shares),
                selectinload(Document.access_logs)
            )
            .where(Document.project_id == project_id)
            .order_by(Document.created_at.desc())
        )
        
        documents = list(result.scalars().all())
        logger.info(f"[DOCUMENT_SERVICE] Projekt {project_id}: {len(documents)} Dokumente geladen")
        return documents
        
    except Exception as e:
        logger.error(f"[DOCUMENT_SERVICE] Fehler beim Laden von Dokumenten für Projekt {project_id}: {str(e)}")
        logger.exception(e)
        return []  # Gebe leere Liste zurück statt Exception


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
    
    # Lösche physische Datei (S3 oder lokal)
    try:
        from ..core.storage import is_s3_path
        from ..services.s3_service import S3Service
        
        if is_s3_path(document.file_path):
            # Lösche aus S3
            await S3Service.delete_file(document.file_path)
            print(f"[SUCCESS] Deleted file from S3: {document.file_path}")
        elif os.path.exists(document.file_path):
            # Lösche lokal
            os.remove(document.file_path)
            print(f"[SUCCESS] Deleted local file: {document.file_path}")
    except Exception as e:
        print(f"[WARNING] Failed to delete file {document.file_path}: {e}")
        pass  # Ignoriere Fehler beim Löschen der Datei
    
    # Lösche abhängige Einträge manuell (da nicht alle Cascades definiert sind)
    try:
        # Lösche document_versions
        await db.execute(
            text("DELETE FROM document_versions WHERE document_id = :doc_id"),
            {"doc_id": document_id}
        )
        
        # Lösche document_status_history
        await db.execute(
            text("DELETE FROM document_status_history WHERE document_id = :doc_id"),
            {"doc_id": document_id}
        )
        
        # Lösche document_shares
        await db.execute(
            text("DELETE FROM document_shares WHERE document_id = :doc_id"),
            {"doc_id": document_id}
        )
        
        # Lösche document_access_log
        await db.execute(
            text("DELETE FROM document_access_log WHERE document_id = :doc_id"),
            {"doc_id": document_id}
        )
        
        # Lösche comments (sollte durch cascade funktionieren, aber sicherheitshalber)
        await db.execute(
            text("DELETE FROM comments WHERE document_id = :doc_id"),
            {"doc_id": document_id}
        )
        
        # Jetzt das Hauptdokument löschen
        await db.delete(document)
        await db.commit()
        
        return True
        
    except Exception as e:
        await db.rollback()
        print(f"Error deleting document {document_id}: {e}")
        return False


async def create_document_version(db: AsyncSession, document_id: int, new_file_path: str, new_file_size: int, uploaded_by: int) -> Document | None:
    """Erstellt eine neue Version eines Dokuments"""
    original_document = await get_document_by_id(db, document_id)
    if not original_document:
        return None
    
    # Markiere alle vorherigen Versionen als nicht-latest (falls is_latest Spalte existiert)
    try:
        await db.execute(
            update(Document)
            .where(Document.parent_document_id == document_id)
            .values(is_latest=False)
        )
    except Exception:
        # Ignoriere Fehler falls is_latest Spalte nicht existiert
        pass
    
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
        parent_document_id=document_id,
        tags=original_document.tags,
        category=original_document.category,
        is_public=original_document.is_public
    )
    
    db.add(new_version)
    await db.commit()
    await db.refresh(new_version)
    return new_version


async def search_documents(db: AsyncSession, search_term: str, project_id: Optional[int] = None, document_type: Optional[DocumentTypeEnum] = None) -> List[Document]:
    query = select(Document).options(
        selectinload(Document.versions),
        selectinload(Document.status_history),
        selectinload(Document.shares),
        selectinload(Document.access_logs)
    )
    
    if project_id:
        query = query.where(Document.project_id == project_id)
    
    if document_type:
        query = query.where(Document.document_type == document_type.value) # Enum-Wert verwenden
    
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
            func.count(Document.id).filter(Document.document_type == DocumentTypeEnum.PLAN).label('plans'),
            func.count(Document.id).filter(Document.document_type == DocumentTypeEnum.PERMIT).label('permits'),
            func.count(Document.id).filter(Document.document_type == DocumentTypeEnum.QUOTE).label('quotes'),
            func.count(Document.id).filter(Document.document_type == DocumentTypeEnum.INVOICE).label('invoices'),
            func.count(Document.id).filter(Document.document_type == DocumentTypeEnum.CONTRACT).label('contracts')
        ).where(Document.project_id == project_id)
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


async def save_uploaded_file(file_content: bytes, filename: str, project_id: int, mime_type: str = "application/octet-stream") -> tuple[str, int]:
    """
    Speichert eine hochgeladene Datei in S3 oder lokal und gibt den Pfad/Key und die Größe zurück
    
    Args:
        file_content: File content as bytes
        filename: Original filename
        project_id: Project ID
        mime_type: MIME type of the file
        
    Returns:
        tuple[str, int]: (file_path or s3_key, file_size)
    """
    from ..core.storage import should_use_s3, get_project_upload_path, get_relative_path
    from ..services.s3_service import S3Service
    
    # Check if S3 should be used
    if should_use_s3("upload"):
        # S3 Upload
        try:
            s3_key = f"project_{project_id}/uploads/{filename}"
            s3_url = await S3Service.upload_file(file_content, s3_key, mime_type)
            print(f"[SUCCESS] File uploaded to S3: {s3_key}")
            return s3_key, len(file_content)  # Return S3 key instead of local path
        except Exception as e:
            print(f"[ERROR] S3 upload failed, falling back to local storage: {e}")
            # Fallback to local storage if S3 fails
    
    # Local Upload (original logic or fallback)
    upload_dir = get_project_upload_path(project_id)
    file_path = upload_dir / filename
    
    # Save file locally
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(file_content)
    
    # Return relative path for database storage
    relative_path = get_relative_path(file_path)
    print(f"[SUCCESS] File saved locally: {relative_path}")
    
    return relative_path, len(file_content) 