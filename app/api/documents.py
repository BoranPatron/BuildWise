from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, func, and_, or_
import os
import uuid
from datetime import datetime
import json

from ..core.database import get_db
from ..api.deps import get_current_user
from ..models import User, Milestone, Project, Document
from ..schemas.document import (
    Document, DocumentUpdate, DocumentSummary, DocumentUploadResponse, DocumentCreate,
    DocumentTypeEnum, DocumentCategoryEnum, DocumentStatusEnum
)
from ..services.document_service import (
    create_document, get_document_by_id, get_documents_for_project,
    update_document, delete_document, search_documents, get_document_statistics,
    save_uploaded_file
)

from app.schemas.comment import Comment as CommentSchema, CommentCreate, CommentUpdate, CommentBase
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models import Comment
from pathlib import Path
import mimetypes
from fastapi import Response
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])


async def add_milestone_info_to_documents(db: AsyncSession, project_id: int, documents: List[Document], user_id: int) -> List[Document]:
    """Erweitert Dokumente um Ausschreibungsinformationen"""
    if not documents:
        return documents
    
    try:
        # Hole alle Milestones für das Projekt
        from sqlalchemy import text
        import json
        
        milestone_query = text("""
            SELECT id, title, description, status, category, shared_document_ids, documents 
            FROM milestones 
            WHERE project_id = :project_id 
            AND created_by = :user_id
        """)
        
        result = await db.execute(milestone_query, {
            "project_id": project_id,
            "user_id": user_id
        })
        
        milestones = result.fetchall()
        
        # Erstelle Mapping von Dokument-ID zu Milestone-Informationen
        doc_to_milestone = {}
        
        for milestone in milestones:
            milestone_id = milestone.id
            milestone_title = milestone.title
            milestone_status = milestone.status
            milestone_category = milestone.category
            
            # Verarbeite shared_document_ids
            if milestone.shared_document_ids:
                try:
                    doc_ids = json.loads(milestone.shared_document_ids)
                    if isinstance(doc_ids, list):
                        for doc_id in doc_ids:
                            doc_to_milestone[str(doc_id)] = {
                                'milestone_id': milestone_id,
                                'milestone_title': milestone_title,
                                'milestone_status': milestone_status,
                                'milestone_category': milestone_category
                            }
                except (json.JSONDecodeError, TypeError):
                    pass
            
            # Verarbeite documents (falls vorhanden)
            if milestone.documents:
                try:
                    docs_raw = milestone.documents
                    if isinstance(docs_raw, str) and docs_raw.startswith('"') and docs_raw.endswith('"'):
                        docs_raw = docs_raw[1:-1]
                    
                    docs = json.loads(docs_raw)
                    if isinstance(docs, list):
                        for doc_id in docs:
                            doc_to_milestone[str(doc_id)] = {
                                'milestone_id': milestone_id,
                                'milestone_title': milestone_title,
                                'milestone_status': milestone_status,
                                'milestone_category': milestone_category
                            }
                except (json.JSONDecodeError, TypeError):
                    pass
        
        # Erweitere Dokumente um Milestone-Informationen
        for doc in documents:
            doc_id_str = str(doc.id)
            if doc_id_str in doc_to_milestone:
                milestone_info = doc_to_milestone[doc_id_str]
                # Füge Milestone-Informationen als Attribute hinzu
                doc.milestone_id = milestone_info['milestone_id']
                doc.milestone_title = milestone_info['milestone_title']
                doc.milestone_status = milestone_info['milestone_status']
                doc.milestone_category = milestone_info['milestone_category']
            else:
                # Dokument gehört zu keiner Ausschreibung
                doc.milestone_id = None
                doc.milestone_title = None
                doc.milestone_status = None
                doc.milestone_category = None
        
        return documents
        
    except Exception as e:
        logger.error(f"Fehler beim Hinzufügen der Milestone-Informationen: {e}")
        # Bei Fehler: Dokumente ohne Milestone-Info zurückgeben
        for doc in documents:
            doc.milestone_id = None
            doc.milestone_title = None
            doc.milestone_status = None
            doc.milestone_category = None
        return documents


@router.delete("/debug/delete-all-documents")
async def delete_all_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Debug-Endpoint zum Löschen aller Dokumente"""
    try:
        # Prüfe ob User ein Admin oder Bauträger ist
        from ..models.user import UserRole
        if not (current_user.user_role == UserRole.ADMIN or current_user.user_role == UserRole.BAUTRAEGER):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Nur Admins und Bauträger können alle Dokumente löschen"
            )
        
        # Lösche alle Dokumente und zugehörige Daten
        from sqlalchemy import text
        
        # Lösche zuerst die Kommentare
        await db.execute(text("DELETE FROM comments"))
        
        # Lösche die Dokumenten-Versionen
        await db.execute(text("DELETE FROM document_versions"))
        
        # Lösche die Dokumenten-Status-Historie
        await db.execute(text("DELETE FROM document_status_history"))
        
        # Lösche die Dokumenten-Freigaben
        await db.execute(text("DELETE FROM document_shares"))
        
        # Lösche die Dokumenten-Zugriffe
        await db.execute(text("DELETE FROM document_access_log"))
        
        # Dann lösche die Dokumente selbst
        await db.execute(text("DELETE FROM documents"))
        
        await db.commit()
        
        # Lösche auch die physischen Dateien
        import shutil
        storage_dir = Path("storage/uploads")
        if storage_dir.exists():
            for item in storage_dir.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
        
        return {"message": "Alle Dokumente und zugehörige Daten wurden gelöscht"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Löschen der Dokumente: {str(e)}"
        )


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    project_id: int = Form(...),
    title: str = Form(...),
    description: str = Form(None),
    document_type: str = Form("other"),  # String statt Enum
    category: str = Form("documentation"),  # String statt Enum
    subcategory: str = Form(None),
    tags: str = Form(None),
    is_public: bool = Form(False),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lädt ein neues Dokument mit erweiterten DMS-Features hoch"""
    try:
        # Debug-Logging
        logger.info(f"📤 Upload-Request erhalten:")
        logger.info(f"   - project_id: {project_id}")
        logger.info(f"   - title: {title}")
        logger.info(f"   - document_type: {document_type} (type: {type(document_type)})")
        logger.info(f"   - category: {category} (type: {type(category)})")
        logger.info(f"   - subcategory: {subcategory}")
        logger.info(f"   - file: {file.filename if file else 'None'}")
        
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
        
        # Prüfe Dateigröße (50MB Limit für DMS)
        if file.size and file.size > 50 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Datei ist zu groß. Maximale Größe: 50MB"
            )
        
        # Speichere Datei
        file_content = await file.read()
        filename = file.filename or "unnamed_file"
        file_path, file_size = await save_uploaded_file(file_content, filename, project_id)
        
        # Erstelle Dokument-Eintrag - Validierung erfolgt im Schema
        logger.info("🔧 Erstelle DocumentCreate Schema...")
        try:
            document_in = DocumentCreate(
                title=title.strip(),
                description=description.strip() if description else None,
                document_type=document_type,  # Schema normalisiert automatisch
                category=category,  # Schema normalisiert automatisch
                subcategory=subcategory.strip() if subcategory else None,
                project_id=project_id,
                tags=tags.strip() if tags else None,
                is_public=is_public,
                # Datei-Informationen hinzufügen
                file_name=filename,
                file_path=file_path,
                file_size=file_size,
                mime_type=file.content_type or "application/octet-stream"
            )
        except Exception as e:
            logger.error(f"Fehler beim Erstellen des DocumentCreate Schemas: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Fehler beim Validieren des Dokument-Eintrags"
            )
        
        document = await create_document(
            db,
            document_in,
            getattr(current_user, 'id', 0)
        )
        
        # Erstelle korrekte Upload-Response
        upload_response = DocumentUploadResponse(
            id=document.id,
            title=document.title,
            file_name=document.file_name or filename,
            file_size=document.file_size or file_size,
            version_number=document.version_number or "1.0.0",
            document_status=document.document_status or "DRAFT",
            workflow_stage=document.workflow_stage or "UPLOADED",
            upload_success=True,
            message="Dokument erfolgreich hochgeladen"
        )
        
        return upload_response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error uploading document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Hochladen des Dokuments"
        )


@router.post("/upload-milestone-documents/{milestone_id}")
async def upload_milestone_documents(
    milestone_id: int,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload von Dokumenten für ein Milestone"""
    
    # Prüfe ob Milestone existiert und Nutzer berechtigt ist
    milestone = await db.get(Milestone, milestone_id)
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone nicht gefunden")
    
    # Prüfe Berechtigung (nur Ersteller oder Projektinhaber)
    project = await db.get(Project, milestone.project_id)
    if not project or (project.owner_id != current_user.id and milestone.created_by != current_user.id):
        raise HTTPException(status_code=403, detail="Keine Berechtigung")
    
    uploaded_documents = []
    
    for file in files:
        # Validiere Dateityp
        allowed_types = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-powerpoint',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'image/jpeg', 'image/png', 'image/gif',  # Bilder für DMS
            'video/mp4', 'video/avi'  # Videos für DMS
        ]
        
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Dateityp {file.content_type} nicht unterstützt"
            )
        
        # Validiere Dateigröße (50MB für DMS)
        content = await file.read()
        if len(content) > 50 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail=f"Datei {file.filename} ist zu groß (max. 50MB)"
            )
        
        # Erstelle Speicherpfad
        upload_dir = f"storage/uploads/project_{project.id}"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generiere sicheren Dateinamen
        file_extension = os.path.splitext(file.filename)[1]
        safe_filename = f"milestone_{milestone_id}_{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(upload_dir, safe_filename)
        
        # Speichere Datei
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        # Erstelle Dokument-Metadaten
        document_data = {
            "id": str(uuid.uuid4()),
            "name": file.filename,
            "url": f"/{file_path}",
            "type": file.content_type,
            "size": len(content),
            "uploaded_at": datetime.now().isoformat()
        }
        
        uploaded_documents.append(document_data)
    
    # Aktualisiere Milestone mit neuen Dokumenten
    existing_docs = milestone.documents if milestone.documents else []
    if isinstance(existing_docs, str):
        existing_docs = json.loads(existing_docs)
    
    all_documents = existing_docs + uploaded_documents
    milestone.documents = all_documents
    
    await db.commit()
    await db.refresh(milestone)
    
    return {
        "message": f"{len(uploaded_documents)} Dokumente erfolgreich hochgeladen",
        "documents": uploaded_documents
    }


@router.get("/", response_model=List[DocumentSummary])
async def read_documents(
    project_id: int,
    category: Optional[DocumentCategoryEnum] = None,
    subcategory: Optional[str] = None,
    document_type: Optional[DocumentTypeEnum] = None,
    status_filter: Optional[DocumentStatusEnum] = None,
    is_favorite: Optional[bool] = None,
    search: Optional[str] = None,
    sort_by: str = Query("created_at", regex="^(title|created_at|file_size|accessed_at)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    milestone_id: Optional[int] = Query(None, description="Filter nach spezifischer Ausschreibung (Milestone)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Erweiterte Dokumentensuche mit Filtern und Sortierung"""
    
    # Für jetzt verwenden wir die bestehende Funktion und filtern nachträglich
    documents = await get_documents_for_project(db, project_id)
    
    # Erweitere Dokumente um Ausschreibungsinformationen
    documents = await add_milestone_info_to_documents(db, project_id, documents, current_user.id)
    
    # Filter für spezifische Ausschreibung (Milestone)
    if milestone_id:
        from sqlalchemy import text
        import json
        
        # Query für spezifisches Milestone mit shared_document_ids und documents
        milestone_query = text("""
            SELECT shared_document_ids, documents 
            FROM milestones 
            WHERE id = :milestone_id 
            AND project_id = :project_id 
            AND created_by = :user_id
        """)
        
        result = await db.execute(milestone_query, {
            "milestone_id": milestone_id,
            "project_id": project_id,
            "user_id": current_user.id
        })
        
        milestone_row = result.fetchone()
        
        if milestone_row:
            shared_document_ids = set()
            milestone_documents = set()
            
            # Verarbeite shared_document_ids
            if milestone_row.shared_document_ids:
                try:
                    doc_ids = json.loads(milestone_row.shared_document_ids)
                    if isinstance(doc_ids, list):
                        shared_document_ids.update(str(doc_id) for doc_id in doc_ids)
                except (json.JSONDecodeError, TypeError):
                    pass
            
            # Verarbeite documents (falls vorhanden)
            if milestone_row.documents:
                try:
                    # Handle doppelt kodiertes JSON (falls vorhanden)
                    docs_raw = milestone_row.documents
                    if isinstance(docs_raw, str) and docs_raw.startswith('"') and docs_raw.endswith('"'):
                        # Entferne äußere Anführungszeichen
                        docs_raw = docs_raw[1:-1]
                    
                    docs = json.loads(docs_raw)
                    if isinstance(docs, list):
                        # Die documents Spalte enthält direkt die Dokument-IDs als Array
                        milestone_documents.update(str(doc_id) for doc_id in docs)
                except (json.JSONDecodeError, TypeError):
                    pass
            
            # Kombiniere beide Dokument-Quellen
            all_milestone_doc_ids = shared_document_ids.union(milestone_documents)
            
            # Filtere Dokumente nach den Milestone-Dokument-IDs
            if all_milestone_doc_ids:
                documents = [doc for doc in documents if str(doc.id) in all_milestone_doc_ids]
            else:
                # Keine Dokumente für diese Ausschreibung gefunden
                documents = []
        else:
            # Milestone nicht gefunden oder keine Berechtigung
            documents = []
    
    # Filter anwenden
    if category:
        def category_matches(doc_category):
            if doc_category is None:
                return False
            # Vergleiche sowohl Enum-Wert als auch String-Repräsentation
            return (doc_category == category or 
                    doc_category == category.value or
                    str(doc_category) == str(category) or
                    str(doc_category) == category.value)
        
        documents = [doc for doc in documents if category_matches(getattr(doc, 'category', None))]
    
    if subcategory:
        documents = [doc for doc in documents if getattr(doc, 'subcategory', None) == subcategory]
    
    if document_type:
        documents = [doc for doc in documents if doc.document_type == document_type]
    
    if status_filter:
        def status_matches(doc_status):
            if doc_status is None:
                doc_status = 'draft'
            # Vergleiche sowohl Enum-Wert als auch String-Repräsentation
            return (doc_status == status_filter or 
                    doc_status == status_filter.value or
                    str(doc_status) == str(status_filter) or
                    str(doc_status) == status_filter.value)
        
        documents = [doc for doc in documents if status_matches(getattr(doc, 'status', 'draft'))]
    
    if is_favorite is not None:
        documents = [doc for doc in documents if getattr(doc, 'is_favorite', False) == is_favorite]
    
    # Volltextsuche
    if search:
        search_term = search.lower()
        documents = [doc for doc in documents if 
                    search_term in doc.title.lower() or
                    search_term in (doc.description or '').lower() or
                    search_term in (doc.tags or '').lower() or
                    search_term in doc.file_name.lower()]
    
    # Sortierung
    if sort_by == 'title':
        documents = sorted(documents, key=lambda x: x.title, reverse=(sort_order == 'desc'))
    elif sort_by == 'file_size':
        documents = sorted(documents, key=lambda x: x.file_size, reverse=(sort_order == 'desc'))
    elif sort_by == 'accessed_at':
        documents = sorted(documents, key=lambda x: getattr(x, 'accessed_at', None) or x.created_at, reverse=(sort_order == 'desc'))
    else:  # created_at
        documents = sorted(documents, key=lambda x: x.created_at, reverse=(sort_order == 'desc'))
    
    # Paginierung
    documents = documents[offset:offset + limit]
    return documents


@router.get("/search/fulltext", response_model=List[DocumentSummary])
async def fulltext_search(
    q: str = Query(..., min_length=2, description="Suchbegriff für Volltextsuche"),
    project_id: Optional[int] = None,
    category: Optional[DocumentCategoryEnum] = None,
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Erweiterte Volltextsuche mit PostgreSQL Full-Text Search"""
    
    # PostgreSQL Volltextsuche Query
    search_query = """
    SELECT d.*, ts_rank(
        to_tsvector('german', d.title || ' ' || COALESCE(d.description, '') || ' ' || COALESCE(d.tags, '')),
        plainto_tsquery('german', :search_term)
    ) as rank
    FROM documents d
    WHERE to_tsvector('german', d.title || ' ' || COALESCE(d.description, '') || ' ' || COALESCE(d.tags, ''))
          @@ plainto_tsquery('german', :search_term)
    """
    
    # Filter hinzufügen
    if project_id:
        search_query += " AND d.project_id = :project_id"
    
    if category:
        search_query += " AND d.category = :category"
    
    search_query += " ORDER BY rank DESC, d.created_at DESC LIMIT :limit"
    
    # Parameter vorbereiten
    params = {"search_term": q, "limit": limit}
    if project_id:
        params["project_id"] = project_id
    if category:
        params["category"] = category.value
    
    # Query ausführen
    result = await db.execute(text(search_query), params)
    documents = result.fetchall()
    
    return [DocumentSummary.from_orm(doc) for doc in documents]


@router.post("/{document_id}/favorite")
async def toggle_favorite(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Togglet den Favoriten-Status eines Dokuments"""
    
    document = await get_document_by_id(db, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dokument nicht gefunden"
        )
    
    # Toggle Favoriten-Status
    document.is_favorite = not document.is_favorite
    await db.commit()
    await db.refresh(document)
    
    return {
        "document_id": document_id,
        "is_favorite": document.is_favorite,
        "message": "Zu Favoriten hinzugefügt" if document.is_favorite else "Aus Favoriten entfernt"
    }


@router.put("/{document_id}/status")
async def update_document_status(
    document_id: int,
    new_status: DocumentStatusEnum,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Aktualisiert den Status eines Dokuments"""
    
    document = await get_document_by_id(db, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dokument nicht gefunden"
        )
    
    old_status = document.status
    document.status = new_status
    await db.commit()
    await db.refresh(document)
    
    return {
        "document_id": document_id,
        "old_status": old_status,
        "new_status": new_status,
        "message": f"Status von {old_status.value} zu {new_status.value} geändert"
    }


@router.get("/categories/stats")
async def get_category_statistics(
    project_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Holt Statistiken für Dokumentenkategorien"""
    
    # Basis-Query für Kategorien-Statistiken
    query = """
    SELECT 
        category,
        subcategory,
        COUNT(*) as document_count,
        SUM(file_size) as total_size,
        AVG(file_size) as avg_size,
        COUNT(CASE WHEN is_favorite = true THEN 1 END) as favorite_count
    FROM documents
    """
    
    params = {}
    if project_id:
        query += " WHERE project_id = :project_id"
        params["project_id"] = project_id
    
    query += " GROUP BY category, subcategory ORDER BY category, subcategory"
    
    result = await db.execute(text(query), params)
    stats = result.fetchall()
    
    # Strukturiere die Ergebnisse
    category_stats = {}
    for row in stats:
        category = row.category
        if category not in category_stats:
            category_stats[category] = {
                "total_documents": 0,
                "total_size": 0,
                "favorite_count": 0,
                "subcategories": {}
            }
        
        category_stats[category]["total_documents"] += row.document_count
        category_stats[category]["total_size"] += row.total_size or 0
        category_stats[category]["favorite_count"] += row.favorite_count or 0
        
        if row.subcategory:
            category_stats[category]["subcategories"][row.subcategory] = {
                "document_count": row.document_count,
                "total_size": row.total_size or 0,
                "avg_size": row.avg_size or 0,
                "favorite_count": row.favorite_count or 0
            }
    
    return category_stats


@router.get("/{document_id}/access")
async def track_document_access(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Trackt den Zugriff auf ein Dokument"""
    
    document = await get_document_by_id(db, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dokument nicht gefunden"
        )
    
    # Aktualisiere accessed_at Timestamp
    document.accessed_at = datetime.utcnow()
    await db.commit()
    
    return {
        "document_id": document_id,
        "accessed_at": document.accessed_at,
        "message": "Zugriff erfolgreich getrackt"
    }


@router.get("/recent")
async def get_recent_documents(
    project_id: Optional[int] = None,
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Holt die zuletzt aufgerufenen Dokumente"""
    
    # Für SQLite verwenden wir eine einfachere Implementierung
    try:
        if project_id:
            documents = await get_documents_for_project(db, project_id)
        else:
            # Alle Dokumente laden (nur für Demo)
            documents = []
        
        # Filter nur Dokumente mit accessed_at
        recent_docs = [doc for doc in documents if getattr(doc, 'accessed_at', None) is not None]
        
        # Sortieren nach accessed_at
        recent_docs = sorted(recent_docs, key=lambda x: getattr(x, 'accessed_at'), reverse=True)
        
        # Limit anwenden
        recent_docs = recent_docs[:limit]
        
        return [DocumentSummary.from_orm(doc) for doc in recent_docs]
    except Exception as e:
        print(f"Error in get_recent_documents: {e}")
        return []


@router.get("/{document_id}/download", response_class=FileResponse)
async def download_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lädt ein Dokument herunter und trackt den Zugriff"""
    document = await get_document_by_id(db, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dokument nicht gefunden"
        )
    
    # Tracke Zugriff
    document.accessed_at = datetime.utcnow()
    await db.commit()
    
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


@router.get("/{document_id}", response_model=Document)
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


@router.get("/{document_id}/info")
async def get_document_info(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lightweight endpoint für Dokumentennamen ohne file_path Probleme"""
    document = await get_document_by_id(db, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dokument nicht gefunden"
        )
    
    return {
        "id": document.id,
        "title": document.title,
        "file_name": document.file_name,
        "mime_type": document.mime_type,
        "file_size": document.file_size,
        "category": document.category,
        "subcategory": document.subcategory,
        "created_at": document.created_at
    }


@router.put("/{document_id}", response_model=Document)
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


@router.get("/project/{project_id}/milestones")
async def get_project_milestones_for_filter(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Holt alle Milestones (Ausschreibungen) des aktuellen Benutzers für ein Projekt"""
    from sqlalchemy import text
    
    try:
        # Query für Milestones des aktuellen Users für das Projekt
        milestone_query = text("""
            SELECT id, title, description, status, category, planned_date, created_at
            FROM milestones 
            WHERE project_id = :project_id 
            AND created_by = :user_id
            ORDER BY created_at DESC
        """)
        
        result = await db.execute(milestone_query, {
            "project_id": project_id,
            "user_id": current_user.id
        })
        
        milestones = result.fetchall()
        
        # Konvertiere zu Dictionary-Format für Frontend
        milestone_list = []
        for milestone in milestones:
            milestone_list.append({
                "id": milestone.id,
                "title": milestone.title,
                "description": milestone.description,
                "status": milestone.status,
                "category": milestone.category,
                "planned_date": milestone.planned_date.isoformat() if milestone.planned_date and hasattr(milestone.planned_date, 'isoformat') else milestone.planned_date,
                "created_at": milestone.created_at.isoformat() if milestone.created_at and hasattr(milestone.created_at, 'isoformat') else milestone.created_at
            })
        
        return milestone_list
        
    except Exception as e:
        print(f"Fehler beim Laden der Milestones: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Laden der Ausschreibungen: {str(e)}"
        )


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
    document_type: Optional[DocumentTypeEnum] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Sucht nach Dokumenten"""
    documents = await search_documents(db, q, project_id, document_type)
    return documents


@router.get("/{document_id}/comments", response_model=List[CommentSchema])
async def get_document_comments(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lade alle Kommentare für ein Dokument"""
    try:
        # Prüfe ob Dokument existiert und User Zugriff hat
        document = await get_document_by_id(db, document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Dokument nicht gefunden")
        
        # Lade Kommentare mit User-Informationen
        result = await db.execute(
            select(Comment, User.first_name, User.last_name)
            .join(User, Comment.user_id == User.id)
            .where(Comment.document_id == document_id)
            .order_by(Comment.created_at.asc())
        )
        
        comments = []
        for comment, first_name, last_name in result.all():
            comment_dict = {
                "id": comment.id,
                "document_id": comment.document_id,
                "user_id": comment.user_id,
                "user_name": f"{first_name} {last_name}".strip(),
                "content": comment.content,
                "page_number": comment.page_number,
                "position_x": comment.position_x,
                "position_y": comment.position_y,
                "created_at": comment.created_at,
                "updated_at": comment.updated_at
            }
            comments.append(CommentSchema(**comment_dict))
        
        return comments
        
    except Exception as e:
        logger.error(f"Fehler beim Laden der Kommentare für Dokument {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Fehler beim Laden der Kommentare")

@router.post("/{document_id}/comments", response_model=CommentSchema)
async def create_comment(
    document_id: int,
    comment_data: CommentBase,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Erstelle einen neuen Kommentar für ein Dokument"""
    try:
        # Prüfe ob Dokument existiert und User Zugriff hat
        document = await get_document_by_id(db, document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Dokument nicht gefunden")
        
        # Erstelle neuen Kommentar
        comment = Comment(
            document_id=document_id,
            user_id=current_user.id,
            content=comment_data.content,
            page_number=comment_data.page_number,
            position_x=comment_data.position_x,
            position_y=comment_data.position_y
        )
        
        db.add(comment)
        await db.commit()
        await db.refresh(comment)
        
        # Lade User-Informationen für Response
        user_name = f"{current_user.first_name} {current_user.last_name}".strip()
        
        comment_dict = {
            "id": comment.id,
            "document_id": comment.document_id,
            "user_id": comment.user_id,
            "user_name": user_name,
            "content": comment.content,
            "page_number": comment.page_number,
            "position_x": comment.position_x,
            "position_y": comment.position_y,
            "created_at": comment.created_at,
            "updated_at": comment.updated_at
        }
        
        return CommentSchema(**comment_dict)
        
    except Exception as e:
        logger.error(f"Fehler beim Erstellen des Kommentars: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Fehler beim Erstellen des Kommentars")

@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lösche einen Kommentar"""
    try:
        # Lade Kommentar
        result = await db.execute(
            select(Comment).where(Comment.id == comment_id)
        )
        comment = result.scalar_one_or_none()
        
        if not comment:
            raise HTTPException(status_code=404, detail="Kommentar nicht gefunden")
        
        # Prüfe Berechtigung (nur eigene Kommentare löschen)
        if comment.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Keine Berechtigung zum Löschen dieses Kommentars")
        
        # Lösche Kommentar
        await db.delete(comment)
        await db.commit()
        
        return {"detail": "Kommentar erfolgreich gelöscht"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fehler beim Löschen des Kommentars {comment_id}: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Fehler beim Löschen des Kommentars")

@router.get("/{document_id}/content")
async def get_document_content(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lade Dokument-Inhalt für Inline-Anzeige"""
    try:
        # Prüfe ob Dokument existiert und User Zugriff hat
        document = await get_document_by_id(db, document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Dokument nicht gefunden")
        
        # Lade Datei-Inhalt
        file_path = Path(document.file_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Datei nicht gefunden")
        
        # Bestimme MIME-Type
        mime_type = mimetypes.guess_type(str(file_path))[0] or 'application/octet-stream'
        
        # Lade und return Datei-Inhalt
        with open(file_path, 'rb') as file:
            content = file.read()
        
        return Response(
            content=content,
            media_type=mime_type,
            headers={
                "Content-Disposition": f"inline; filename={document.file_name}",
                "Cache-Control": "private, max-age=3600"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fehler beim Laden des Dokument-Inhalts {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Fehler beim Laden des Dokument-Inhalts")


# Dienstleister-spezifische Endpunkte
@router.get("/service-provider", response_model=List[DocumentSummary])
async def read_service_provider_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lade Dokumente für Dienstleister (Rechnungen, etc.)"""
    logger.info(f"🔍 Service provider documents request - User: {current_user.email}, Type: {current_user.user_type}, Role: {current_user.user_role}")
    try:
        # Prüfe ob User ein Dienstleister ist
        is_service_provider = (
            current_user.user_type == "service_provider" or
            current_user.user_role == "DIENSTLEISTER"
        )
        
        if not is_service_provider:
            raise HTTPException(
                status_code=403,
                detail="Nur Dienstleister können ihre Dokumente einsehen"
            )
        
        # Lade Dienstleister-spezifische Dokumente (vereinfacht)
        stmt = select(Document).options(
            selectinload(Document.versions),
            selectinload(Document.status_history),
            selectinload(Document.shares),
            selectinload(Document.access_logs)
        ).where(
            Document.uploaded_by == current_user.id
        ).order_by(Document.created_at.desc()).limit(100)
        
        result = await db.execute(stmt)
        documents = result.scalars().all()
        
        # Erweitere Dokumente um Ausschreibungsinformationen (falls sie zu einem Projekt gehören)
        documents_with_milestone_info = []
        for doc in documents:
            if doc.project_id:
                # Versuche Milestone-Informationen für dieses Dokument zu finden
                try:
                    from sqlalchemy import text
                    import json
                    
                    milestone_query = text("""
                        SELECT id, title, description, status, category, shared_document_ids, documents 
                        FROM milestones 
                        WHERE project_id = :project_id 
                        AND (shared_document_ids LIKE :doc_id_pattern OR documents LIKE :doc_id_pattern)
                    """)
                    
                    doc_id_pattern = f'%{doc.id}%'
                    milestone_result = await db.execute(milestone_query, {
                        "project_id": doc.project_id,
                        "doc_id_pattern": doc_id_pattern
                    })
                    
                    milestone_row = milestone_result.fetchone()
                    if milestone_row:
                        doc.milestone_id = milestone_row.id
                        doc.milestone_title = milestone_row.title
                        doc.milestone_status = milestone_row.status
                        doc.milestone_category = milestone_row.category
                    else:
                        doc.milestone_id = None
                        doc.milestone_title = None
                        doc.milestone_status = None
                        doc.milestone_category = None
                except Exception as e:
                    logger.warning(f"Fehler beim Laden der Milestone-Info für Dokument {doc.id}: {e}")
                    doc.milestone_id = None
                    doc.milestone_title = None
                    doc.milestone_status = None
                    doc.milestone_category = None
            else:
                doc.milestone_id = None
                doc.milestone_title = None
                doc.milestone_status = None
                doc.milestone_category = None
            
            documents_with_milestone_info.append(doc)
        
        # Konvertiere zu DocumentSummary mit allen erforderlichen Feldern
        document_summaries = []
        for doc in documents_with_milestone_info:
            summary = {
                "id": doc.id,
                "title": doc.title,
                "document_type": doc.document_type or "other",
                "category": doc.category,
                "subcategory": doc.subcategory,
                "version_number": "1.0",  # Standard-Version
                "document_status": doc.status or "DRAFT",
                "workflow_stage": "UPLOADED",  # Standard-Stage
                "file_name": doc.file_name,
                "file_size": doc.file_size or 0,
                "created_at": doc.created_at,
                "updated_at": doc.updated_at,
                "is_favorite": doc.is_favorite or False,
                "download_count": 0,  # Standard-Download-Count
                # Ausschreibungsinformationen
                "milestone_id": getattr(doc, 'milestone_id', None),
                "milestone_title": getattr(doc, 'milestone_title', None),
                "milestone_status": getattr(doc, 'milestone_status', None),
                "milestone_category": getattr(doc, 'milestone_category', None)
            }
            document_summaries.append(DocumentSummary(**summary))
        
        return document_summaries
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fehler beim Laden der Dienstleister-Dokumente: {str(e)}")
        raise HTTPException(status_code=500, detail="Fehler beim Laden der Dokumente")


@router.get("/categories/stats/service-provider")
async def get_service_provider_category_statistics(
    project_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lade Kategorie-Statistiken für Dienstleister-Dokumente"""
    try:
        # Prüfe ob User ein Dienstleister ist
        is_service_provider = (
            current_user.user_type == "service_provider" or
            current_user.user_role == "DIENSTLEISTER"
        )
        
        if not is_service_provider:
            raise HTTPException(
                status_code=403,
                detail="Nur Dienstleister können ihre Statistiken einsehen"
            )
        
        # Lade Statistiken für Dienstleister-Dokumente
        stmt = select(
            Document.category,
            func.count(Document.id).label('total_documents'),
            func.sum(Document.file_size).label('total_size'),
            func.sum(func.case((Document.is_favorite == True, 1), else_=0)).label('favorite_count')
        ).where(
            Document.uploaded_by == current_user.id
        ).group_by(Document.category)
        
        result = await db.execute(stmt)
        stats = result.all()
        
        # Formatiere Statistiken
        category_stats = {}
        for stat in stats:
            category = stat.category or "other"
            category_stats[category] = {
                "total_documents": stat.total_documents,
                "total_size": stat.total_size or 0,
                "favorite_count": stat.favorite_count,
                "subcategories": {}  # Vereinfacht für Dienstleister
            }
        
        return category_stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fehler beim Laden der Dienstleister-Statistiken: {str(e)}")
        raise HTTPException(status_code=500, detail="Fehler beim Laden der Statistiken")