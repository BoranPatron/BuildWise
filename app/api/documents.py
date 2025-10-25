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
from ..api.deps import get_current_user, get_current_user_optional
from ..services.user_service import get_user_by_email
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

# Utility functions for robust role checking
def is_bautraeger_user(user_role) -> bool:
    """
    Robust check if user is Bauträger, handling both enum and string values.
    Supports various role formats and variations including PostgreSQL enums.
    """
    if user_role is None:
        return False
    
    # Convert to string for comparison
    role_str = str(user_role).lower()
    
    # Check for all possible Bauträger values
    bautraeger_values = [
        'bautraeger', 'bauträger', 'bauteager',  # Common variations
        'developer', 'dev',  # Developer role (also has Bauträger access)
        'ba'  # Short form
    ]
    
    # Also check if it's a PostgreSQL enum that contains 'bautraeger'
    if 'bautraeger' in role_str or 'bauträger' in role_str:
        return True
    
    return role_str in bautraeger_values

def is_dienstleister_user(user_role) -> bool:
    """
    Robust check if user is Dienstleister, handling both enum and string values.
    Supports various role formats and variations including PostgreSQL enums.
    """
    if user_role is None:
        return False
    
    # Convert to string for comparison
    role_str = str(user_role).lower()
    
    # Check for all possible Dienstleister values
    dienstleister_values = [
        'dienstleister', 'service_provider', 'serviceprovider',  # Common variations
        'contractor', 'provider',  # English alternatives
        'dl'  # Short form
    ]
    
    # Also check if it's a PostgreSQL enum that contains 'dienstleister'
    if 'dienstleister' in role_str or 'service_provider' in role_str:
        return True
    
    return role_str in dienstleister_values

def log_user_role_info(user: User, endpoint_name: str):
    """
    Log comprehensive user role information for debugging.
    """
    print(f"[DEBUG] {endpoint_name} - User ID: {user.id}")
    print(f"[DEBUG] {endpoint_name} - User email: {user.email}")
    print(f"[DEBUG] {endpoint_name} - User role: {user.user_role}")
    print(f"[DEBUG] {endpoint_name} - User role type: {type(user.user_role)}")
    print(f"[DEBUG] {endpoint_name} - User type: {user.user_type}")
    print(f"[DEBUG] {endpoint_name} - Role selected: {user.role_selected}")

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
        logger.info(f"[INFO] Upload-Request erhalten:")
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
        mime_type = file.content_type or "application/octet-stream"
        file_path, file_size = await save_uploaded_file(file_content, filename, project_id, mime_type)
        
        # Erstelle Dokument-Eintrag - Validierung erfolgt im Schema
        logger.info("[DEBUG] Erstelle DocumentCreate Schema...")
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
        
        # Generiere sicheren Dateinamen
        file_extension = os.path.splitext(file.filename)[1]
        safe_filename = f"milestone_{milestone_id}_{uuid.uuid4()}{file_extension}"
        
        # Speichere Datei mit save_uploaded_file (unterstützt S3 und lokal)
        mime_type = file.content_type or "application/octet-stream"
        file_path, file_size = await save_uploaded_file(content, safe_filename, project.id, mime_type)
        
        # Erstelle Dokument-Metadaten
        document_data = {
            "id": str(uuid.uuid4()),
            "name": file.filename,
            "url": f"/{file_path}",
            "type": file.content_type,
            "size": file_size,
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
    project_id: Optional[int] = Query(None, description="Projekt-ID für Dokumentenfilterung"),
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
    """Erweiterte Dokumentensuche mit Filtern und Sortierung - ROBUSTE VERSION"""
    
    try:
        logger.info(f"[DOCUMENTS_API] Request von User {current_user.id}: project_id={project_id}, milestone_id={milestone_id}")
        
        # ROBUSTE LÖSUNG: Wenn keine project_id, lade alle Dokumente des Users
        if project_id is None:
            logger.info(f"[DOCUMENTS_API] Keine project_id - lade alle Dokumente für User {current_user.id}")
            
            # Lade alle Projekte des Users
            from sqlalchemy import text
            user_projects_query = text("""
                SELECT DISTINCT p.id 
                FROM projects p 
                WHERE p.owner_id = :user_id
                UNION
                SELECT DISTINCT q.project_id 
                FROM quotes q 
                WHERE q.service_provider_id = :user_id AND q.status = 'accepted'
            """)
            
            projects_result = await db.execute(user_projects_query, {"user_id": current_user.id})
            user_project_ids = [row.id for row in projects_result.fetchall()]
            
            logger.info(f"[DOCUMENTS_API] Gefundene Projekt-IDs für User: {user_project_ids}")
            
            if not user_project_ids:
                logger.info(f"[DOCUMENTS_API] Keine Projekte gefunden - gebe leere Liste zurück")
                return []
            
            # Lade Dokumente aus allen Projekten des Users
            documents = []
            for pid in user_project_ids:
                try:
                    project_docs = await get_documents_for_project(db, pid)
                    documents.extend(project_docs)
                    logger.info(f"[DOCUMENTS_API] Projekt {pid}: {len(project_docs)} Dokumente geladen")
                except Exception as e:
                    logger.error(f"[DOCUMENTS_API] Fehler beim Laden von Projekt {pid}: {e}")
                    continue
        else:
            # Original-Logik für spezifisches Projekt
            logger.info(f"[DOCUMENTS_API] Lade Dokumente für Projekt {project_id}")
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
            """)
            
            result = await db.execute(milestone_query, {
                "milestone_id": milestone_id,
                "project_id": project_id
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
                # Milestone nicht gefunden
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
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DOCUMENTS_API] Kritischer Fehler beim Laden der Dokumente: {str(e)}")
        logger.exception(e)
        
        # ROBUSTE FALLBACK-LÖSUNG: Gebe leere Liste zurück statt 500-Fehler
        logger.info(f"[DOCUMENTS_API] Fallback: Gebe leere Liste zurück")
        return []


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


@router.get("/{document_id}/content")
async def get_document_content(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns document content/file for viewing (inline display)
    This endpoint is CRITICAL for frontend document preview
    Supports both S3 and local file storage
    """
    try:
        logger.info(f"[API] get_document_content called for document_id={document_id}")
        
        # Get document from database
        document = await get_document_by_id(db, document_id)
        if not document:
            logger.error(f"[API] Document {document_id} not found in database")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dokument nicht gefunden"
            )
        
        # Track access
        document.accessed_at = datetime.utcnow()
        await db.commit()
        
        file_path = str(document.file_path)
        
        # Check if file is in S3 or local storage
        from ..core.storage import is_s3_path
        from ..services.s3_service import S3Service
        
        if is_s3_path(file_path):
            # S3 file - download and return as Response
            try:
                logger.info(f"[API] Downloading from S3: {file_path}")
                file_content = await S3Service.download_file(file_path)
                logger.info(f"[SUCCESS] Downloaded {len(file_content)} bytes from S3")
                
                return Response(
                    content=file_content,
                    media_type=str(document.mime_type),
                    headers={"Content-Disposition": f"inline; filename=\"{document.file_name}\""}
                )
            except Exception as e:
                logger.error(f"[ERROR] Failed to download from S3: {e}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Datei nicht in S3 gefunden"
                )
        else:
            # Local file - use FileResponse
            if not os.path.exists(file_path):
                logger.error(f"[API] File not found on disk: {file_path}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Datei nicht auf Server gefunden"
                )
            
            logger.info(f"[SUCCESS] Returning document content for {document_id}: {file_path}")
            
            # Return file with inline content-disposition for browser preview
            return FileResponse(
                path=file_path,
                filename=str(document.file_name),
                media_type=str(document.mime_type),
                headers={"Content-Disposition": f"inline; filename=\"{document.file_name}\""}
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ERROR] Failed to get document content for {document_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Laden des Dokument-Inhalts"
        )


@router.get("/{document_id}/download")
async def download_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Lädt ein Dokument herunter und trackt den Zugriff
    Supports both S3 and local file storage
    """
    try:
        logger.info(f"[API] download_document called for document_id={document_id}")
        
        document = await get_document_by_id(db, document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dokument nicht gefunden"
            )
        
        # Tracke Zugriff
        document.accessed_at = datetime.utcnow()
        await db.commit()
        
        file_path = str(document.file_path)
        
        # Check if file is in S3 or local storage
        from ..core.storage import is_s3_path
        from ..services.s3_service import S3Service
        
        if is_s3_path(file_path):
            # S3 file - download and return as Response
            try:
                logger.info(f"[API] Downloading from S3: {file_path}")
                file_content = await S3Service.download_file(file_path)
                logger.info(f"[SUCCESS] Downloaded {len(file_content)} bytes from S3")
                
                return Response(
                    content=file_content,
                    media_type=str(document.mime_type),
                    headers={"Content-Disposition": f"attachment; filename=\"{document.file_name}\""}
                )
            except Exception as e:
                logger.error(f"[ERROR] Failed to download from S3: {e}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Datei nicht in S3 gefunden"
                )
        else:
            # Local file - use FileResponse
            if not os.path.exists(file_path):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Datei nicht gefunden"
                )
            
            logger.info(f"[SUCCESS] Returning download for {document_id}: {file_path}")
            
            return FileResponse(
                path=file_path,
                filename=str(document.file_name),
                media_type=str(document.mime_type)
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ERROR] Failed to download document {document_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Herunterladen des Dokuments"
        )


@router.get("/{document_id}/view")
async def view_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Zeigt ein Dokument an (für Browser-Vorschau)
    Supports both S3 and local file storage
    """
    document = await get_document_by_id(db, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dokument nicht gefunden"
        )
    
    file_path = str(document.file_path)
    
    try:
        # Check if file is in S3 or local storage
        from ..core.storage import is_s3_path
        from ..services.s3_service import S3Service
        
        if is_s3_path(file_path):
            # Download from S3
            content = await S3Service.download_file(file_path)
        else:
            # Load from local storage
            if not os.path.exists(file_path):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Datei nicht gefunden"
                )
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


@router.get("/bautraeger/overview")
async def get_bautraeger_documents_overview(
    project_id: int = Query(..., description="Project ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get documents overview for Bauträger with role-based access.
    Bauträger can see all documents in their projects.
    """
    try:
        from sqlalchemy import text, and_
        from app.models import Document, Milestone
        
        # Verify user has access to this project
        project_query = text("SELECT id, owner_id FROM projects WHERE id = :project_id")
        project_result = await db.execute(project_query, {"project_id": project_id})
        project = project_result.fetchone()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Debug logging and robust role checking
        log_user_role_info(current_user, "Bauträger endpoint")
        
        # Additional debug info for PostgreSQL enum handling
        print(f"[DEBUG] Bauträger endpoint - Raw user_role: {repr(current_user.user_role)}")
        print(f"[DEBUG] Bauträger endpoint - user_role as string: {str(current_user.user_role)}")
        print(f"[DEBUG] Bauträger endpoint - user_role type: {type(current_user.user_role)}")
        
        is_bautraeger = is_bautraeger_user(current_user.user_role)
        print(f"[DEBUG] Bauträger endpoint - Is Bauträger check result: {is_bautraeger}")
        
        if not is_bautraeger:
            print(f"[ERROR] Bauträger endpoint - Access denied. User role: {current_user.user_role}, Type: {type(current_user.user_role)}")
            raise HTTPException(status_code=403, detail="Access denied: Bauträger only")
        
        # Get all documents for this project
        query = select(Document).where(
            Document.project_id == project_id
        ).order_by(Document.created_at.desc())
        
        result = await db.execute(query)
        documents = result.scalars().all()
        
        # Enrich documents with milestone information
        documents_enriched = await add_milestone_info_to_documents(
            db, project_id, documents, current_user.id
        )
        
        # Format response
        document_list = []
        for doc in documents_enriched:
            doc_dict = {
                "id": doc.id,
                "title": doc.title,
                "filename": doc.file_name,
                "file_path": doc.file_path,
                "file_url": doc.file_path,
                "category": doc.category,
                "subcategory": doc.subcategory,
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "file_size": doc.file_size,
                "file_type": doc.mime_type,
                "project_id": doc.project_id,
                "milestone_id": getattr(doc, 'milestone_id', None),
                "milestone_title": getattr(doc, 'milestone_title', None),
                "ausschreibung_title": getattr(doc, 'milestone_title', None),
            }
            document_list.append(doc_dict)
        
        return {
            "documents": document_list,
            "total": len(document_list),
            "project_id": project_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading bautraeger documents: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error loading documents: {str(e)}"
        )


@router.get("/dienstleister/overview")
async def get_dienstleister_documents_overview(
    project_id: int = Query(..., description="Project ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get documents overview for Dienstleister with role-based access.
    Dienstleister can only see documents they are authorized to access
    (documents shared with them via accepted quotes/milestones).
    """
    try:
        from sqlalchemy import text
        import json
        
        # Debug logging and robust role checking
        log_user_role_info(current_user, "Dienstleister endpoint")
        
        is_dienstleister = is_dienstleister_user(current_user.user_role)
        print(f"[DEBUG] Dienstleister endpoint - Is Dienstleister check result: {is_dienstleister}")
        
        if not is_dienstleister:
            print(f"[ERROR] Dienstleister endpoint - Access denied. User role: {current_user.user_role}, Type: {type(current_user.user_role)}")
            raise HTTPException(status_code=403, detail="Access denied: Dienstleister only")
        
        # Get milestones where user has accepted quotes
        milestone_query = text("""
            SELECT DISTINCT m.id, m.title, m.shared_document_ids, m.documents
            FROM milestones m
            INNER JOIN quotes q ON q.milestone_id = m.id
            WHERE m.project_id = :project_id
            AND q.service_provider_id = :user_id
            AND q.status = 'accepted'
        """)
        
        result = await db.execute(milestone_query, {
            "project_id": project_id,
            "user_id": current_user.id
        })
        milestones = result.fetchall()
        
        # Collect authorized document IDs
        authorized_doc_ids = set()
        for milestone in milestones:
            # Parse shared_document_ids
            if milestone.shared_document_ids:
                try:
                    doc_ids = json.loads(milestone.shared_document_ids)
                    if isinstance(doc_ids, list):
                        authorized_doc_ids.update(map(str, doc_ids))
                except:
                    pass
            
            # Parse documents field
            if milestone.documents:
                try:
                    docs = json.loads(milestone.documents)
                    if isinstance(docs, list):
                        authorized_doc_ids.update(map(str, docs))
                except:
                    pass
        
        # Get documents user is authorized to see
        if not authorized_doc_ids:
            return {"documents": [], "total": 0, "project_id": project_id}
        
        doc_query = text("""
            SELECT id, title, filename, file_path, file_url, category, 
                   subcategory, created_at, file_size, file_type, project_id
            FROM documents
            WHERE id IN :doc_ids
            ORDER BY created_at DESC
        """)
        
        result = await db.execute(doc_query, {"doc_ids": tuple(map(int, authorized_doc_ids))})
        documents = result.fetchall()
        
        # Format response
        document_list = []
        for doc in documents:
            doc_dict = {
                "id": doc[0],
                "title": doc[1],
                "filename": doc[2],
                "file_path": doc[3],
                "file_url": doc[4],
                "category": doc[5],
                "subcategory": doc[6],
                "created_at": doc[7].isoformat() if doc[7] else None,
                "file_size": doc[8],
                "file_type": doc[9],
                "project_id": doc[10],
            }
            document_list.append(doc_dict)
        
        return {
            "documents": document_list,
            "total": len(document_list),
            "project_id": project_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading dienstleister documents: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error loading documents: {str(e)}"
        )




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

# Bauträger-spezifische Endpunkte
# WICHTIG: Diese Endpunkte MÜSSEN vor den allgemeinen GET-Endpunkten definiert werden!
@router.get("/bautraeger/overview")
async def get_bautraeger_documents_overview(
    project_id: int = Query(..., description="ID des Projekts für das die Dokumente geladen werden sollen"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Liefert eine übersichtliche Liste aller Dokumente für Bauträger,
    gruppiert nach Ausschreibungen mit allen relevanten Metadaten.
    """
    try:
        # Prüfe ob User ein Bauträger ist
        # user_role ist ein Enum, daher müssen wir sowohl Enum als auch String-Wert prüfen
        from app.models.user import UserRole
        
        is_bautraeger = False
        
        # Prüfe user_role (Enum oder String)
        if current_user.user_role:
            if hasattr(current_user.user_role, 'value'):
                # Enum-Objekt
                is_bautraeger = current_user.user_role.value in ["BAUTRAEGER", "bautraeger", "developer", "DEVELOPER"]
            else:
                # String
                is_bautraeger = str(current_user.user_role).upper() in ["BAUTRAEGER", "DEVELOPER"]
        
        # Zusätzlich user_type prüfen (für Kompatibilität)
        if not is_bautraeger and current_user.user_type:
            if hasattr(current_user.user_type, 'value'):
                is_bautraeger = current_user.user_type.value in ["project_owner", "bautraeger", "developer"]
            else:
                is_bautraeger = str(current_user.user_type).lower() in ["project_owner", "bautraeger", "developer"]
        
        logger.info(f"[BAUTRAEGER_CHECK] User {current_user.id} - user_role: {current_user.user_role}, user_type: {current_user.user_type}, is_bautraeger: {is_bautraeger}")
        
        if not is_bautraeger:
            raise HTTPException(
                status_code=403,
                detail="Nur Bauträger können diese Übersicht einsehen"
            )
        
        # Prüfe ob das Projekt dem Bauträger gehört
        project_query = text("""
            SELECT id, name 
            FROM projects 
            WHERE id = :project_id AND owner_id = :user_id
        """)
        project_result = await db.execute(project_query, {"project_id": project_id, "user_id": current_user.id})
        project = project_result.fetchone()
        
        if not project:
            raise HTTPException(
                status_code=404,
                detail="Projekt nicht gefunden oder Sie haben keine Berechtigung"
            )
        
        project_ids = [project.id]
        project_map = {project.id: project.name}
        
        # Lade alle Milestones (Ausschreibungen) für diese Projekte
        # Erstelle Platzhalter für IN-Clause
        project_ids_placeholders = ', '.join([f':pid_{i}' for i in range(len(project_ids))])
        milestones_query = text(f"""
            SELECT id, project_id, title, description, status, category, 
                   shared_document_ids, documents
            FROM milestones 
            WHERE project_id IN ({project_ids_placeholders})
            AND created_by = :user_id
        """)
        
        # Erstelle Parameter-Dictionary
        milestone_params = {f'pid_{i}': pid for i, pid in enumerate(project_ids)}
        milestone_params['user_id'] = current_user.id
        
        milestones_result = await db.execute(milestones_query, milestone_params)
        milestones = milestones_result.fetchall()
        
        # Erstelle Mapping: Document-ID -> Milestone-Info
        doc_to_milestone = {}
        for milestone in milestones:
            milestone_info = {
                'milestone_id': milestone.id,
                'milestone_title': milestone.title,
                'milestone_status': milestone.status,
                'milestone_category': milestone.category,
                'project_id': milestone.project_id,
                'project_title': project_map.get(milestone.project_id, 'Unbekanntes Projekt')
            }
            
            # Verarbeite shared_document_ids
            if milestone.shared_document_ids:
                try:
                    doc_ids = json.loads(milestone.shared_document_ids)
                    if isinstance(doc_ids, list):
                        for doc_id in doc_ids:
                            doc_to_milestone[str(doc_id)] = milestone_info
                except (json.JSONDecodeError, TypeError):
                    pass
            
            # Verarbeite documents Feld
            if milestone.documents:
                try:
                    docs_raw = milestone.documents
                    if isinstance(docs_raw, str) and docs_raw.startswith('"') and docs_raw.endswith('"'):
                        docs_raw = docs_raw[1:-1]
                    
                    docs = json.loads(docs_raw)
                    if isinstance(docs, list):
                        for doc_id in docs:
                            doc_to_milestone[str(doc_id)] = milestone_info
                except (json.JSONDecodeError, TypeError):
                    pass
        
        # Lade alle Dokumente für die Projekte
        docs_placeholders = ', '.join([f':did_{i}' for i in range(len(project_ids))])
        documents_query = text(f"""
            SELECT 
                d.id,
                d.title,
                d.file_name,
                d.file_path,
                d.category,
                d.subcategory,
                d.mime_type,
                d.file_size,
                d.created_at,
                d.project_id
            FROM documents d
            WHERE d.project_id IN ({docs_placeholders})
            ORDER BY d.created_at DESC
        """)
        
        # Erstelle Parameter-Dictionary
        docs_params = {f'did_{i}': pid for i, pid in enumerate(project_ids)}
        
        docs_result = await db.execute(documents_query, docs_params)
        documents = docs_result.fetchall()
        
        # Formatiere Dokumente mit allen Metadaten
        formatted_documents = []
        for doc in documents:
            doc_id_str = str(doc.id)
            milestone_info = doc_to_milestone.get(doc_id_str, {})
            
            # created_at behandeln (kann DateTime-Objekt oder String sein)
            created_at_value = doc.created_at
            if created_at_value:
                if hasattr(created_at_value, 'isoformat'):
                    created_at_value = created_at_value.isoformat()
                else:
                    created_at_value = str(created_at_value)
            
            formatted_doc = {
                "id": doc.id,
                "title": doc.title,
                "filename": doc.file_name or "Unbenannt",
                "file_path": doc.file_path,
                "file_url": None,  # file_url existiert nicht in der DB
                "category": doc.category,
                "subcategory": doc.subcategory,
                "file_type": doc.mime_type,
                "file_size": doc.file_size,
                "created_at": created_at_value,
                "project_id": doc.project_id,
                "project_title": project_map.get(doc.project_id, 'Unbekanntes Projekt'),
                "milestone_id": milestone_info.get('milestone_id'),  # Nur aus Mapping
                "milestone_title": milestone_info.get('milestone_title'),
                "milestone_status": milestone_info.get('milestone_status'),
                "milestone_category": milestone_info.get('milestone_category'),
                "ausschreibung_title": milestone_info.get('milestone_title')
            }
            
            formatted_documents.append(formatted_doc)
        
        return {
            "documents": formatted_documents,
            "total_count": len(formatted_documents),
            "project_name": project.name,
            "project_id": project.id,
            "milestones_count": len(milestones)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fehler beim Laden der Bauträger-Dokumenten-Übersicht: {str(e)}")
        logger.exception(e)
        raise HTTPException(status_code=500, detail="Fehler beim Laden der Dokumenten-Übersicht")


# Dienstleister-spezifische Endpunkte
# WICHTIG: Diese Endpunkte MÜSSEN vor den allgemeinen GET-Endpunkten definiert werden!
@router.get("/sp/documents", response_model=List[DocumentSummary])
async def read_service_provider_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lade Dokumente für Dienstleister (Rechnungen, etc.)"""
    logger.info(f"[DEBUG] Service provider documents request - User: {current_user.email}, User ID: {current_user.id}")
    
    try:
        # Importiere UserRole und UserType für Enum-Vergleiche
        from ..models.user import UserRole, UserType
        
        # Prüfe ob User ein Dienstleister ist
        is_service_provider = (
            current_user.user_type == UserType.SERVICE_PROVIDER or
            current_user.user_role == UserRole.DIENSTLEISTER
        )
        
        logger.info(f"[DEBUG] is_service_provider: {is_service_provider}")
        
        if not is_service_provider:
            logger.error(f"[ERROR] User {current_user.id} ist kein Dienstleister")
            raise HTTPException(
                status_code=403,
                detail="Nur Dienstleister können ihre Dokumente einsehen"
            )
        
        # Lade alle Dokumente von Projekten, wo der Dienstleister akzeptierte Quotes hat
        from sqlalchemy import text
        
        logger.info(f"[DEBUG] Lade akzeptierte Quotes für User {current_user.id}")
        
        # ZUERST: Prüfe alle Quotes des Dienstleisters (unabhängig vom Status)
        all_quotes_query = text("""
            SELECT q.id, q.project_id, q.status, q.created_at
            FROM quotes q
            WHERE q.service_provider_id = :service_provider_id
            ORDER BY q.created_at DESC
        """)
        
        all_quotes_result = await db.execute(all_quotes_query, {
            "service_provider_id": current_user.id
        })
        all_quotes = all_quotes_result.fetchall()
        
        logger.info(f"[DEBUG] Alle Quotes des Dienstleisters: {len(all_quotes)}")
        for quote in all_quotes:
            logger.info(f"[DEBUG] Quote {quote.id}: project_id={quote.project_id}, status={quote.status}")
        
        # Query für akzeptierte Quotes des Dienstleisters
        accepted_quotes_query = text("""
            SELECT DISTINCT q.project_id
            FROM quotes q
            WHERE q.service_provider_id = :service_provider_id
            AND q.status = 'accepted'
        """)
        
        quotes_result = await db.execute(accepted_quotes_query, {
            "service_provider_id": current_user.id
        })
        accepted_quotes = quotes_result.fetchall()
        
        logger.info(f"[DEBUG] Gefundene akzeptierte Quotes: {len(accepted_quotes)}")
        
        # TEMPORÄRE LÖSUNG: Falls keine akzeptierten Quotes gefunden werden,
        # lade alle Dokumente des Dienstleisters (unabhängig vom Quote-Status)
        if not accepted_quotes:
            logger.info(f"[DEBUG] Keine akzeptierten Quotes - lade ALLE Dokumente des Dienstleisters")
            
            # Lade alle Dokumente, die der Dienstleister hochgeladen hat
            all_docs_query = text("""
                SELECT d.id, d.title, d.description, d.file_name, d.file_path, 
                       d.file_size, d.mime_type, d.document_type, d.category, 
                       d.subcategory, d.is_favorite, d.tags, 
                       d.created_at, d.updated_at, 
                       d.project_id, d.uploaded_by
                FROM documents d
                WHERE d.uploaded_by = :service_provider_id
                AND d.hidden_for_service_providers = FALSE
                ORDER BY d.created_at DESC
                LIMIT 200
            """)
            
            docs_result = await db.execute(all_docs_query, {
                "service_provider_id": current_user.id
            })
            documents = docs_result.fetchall()
            
            logger.info(f"[DEBUG] Gefundene eigene Dokumente: {len(documents)}")
            
            if not documents:
                logger.info(f"[DEBUG] Keine eigenen Dokumente gefunden - gebe leere Liste zurück")
                return []
            
            # Konvertiere zu DocumentSummary
            document_summaries = []
            for doc in documents:
                try:
                    summary = DocumentSummary(
                        id=doc.id,
                        title=doc.title,
                        description=doc.description,
                        file_name=doc.file_name,
                        file_path=doc.file_path,
                        file_size=doc.file_size or 0,
                        mime_type=doc.mime_type,
                        document_type=doc.document_type or "other",
                        category=doc.category,
                        subcategory=doc.subcategory,
                        is_favorite=doc.is_favorite or False,
                        status="active",  # Default-Status da Spalte nicht existiert
                        tags=doc.tags,
                        is_encrypted=False,  # Default-Wert da Spalte nicht existiert
                        created_at=doc.created_at,
                        updated_at=doc.updated_at,
                        accessed_at=None,  # Default-Wert da Spalte nicht existiert
                        project_id=doc.project_id,
                        uploaded_by=doc.uploaded_by,
                        milestone_id=None,  # Default-Wert da Spalte nicht existiert
                        milestone_title=None,
                        milestone_status=None,
                        milestone_category=None,
                        # Pflichtfelder für DocumentSummary
                        version_number="1",  # Default-Version (String!)
                        document_status="active",  # Default-Status
                        workflow_stage="completed",  # Default-Workflow-Stage
                        download_count=0  # Default-Download-Count
                    )
                    document_summaries.append(summary)
                except Exception as e:
                    logger.error(f"[ERROR] Fehler beim Konvertieren von Dokument {doc.id}: {str(e)}")
                    continue
            
            logger.info(f"[DEBUG] Erfolgreich {len(document_summaries)} eigene Dokumente konvertiert")
            return document_summaries
        
        # Sammle alle Projekt-IDs
        project_ids = [quote.project_id for quote in accepted_quotes if quote.project_id]
        
        if not project_ids:
            logger.info(f"[DEBUG] Keine gültigen Projekt-IDs - gebe leere Liste zurück")
            return []
        
        logger.info(f"[DEBUG] Lade Dokumente für {len(project_ids)} Projekte: {project_ids}")
        
        # ZUERST: Prüfe ob es überhaupt Dokumente in der Datenbank gibt
        total_docs_query = text("SELECT COUNT(*) as total FROM documents")
        total_docs_result = await db.execute(total_docs_query)
        total_docs = total_docs_result.fetchone()
        logger.info(f"[DEBUG] Gesamtanzahl Dokumente in DB: {total_docs.total if total_docs else 0}")
        
        # Lade alle Dokumente aus diesen Projekten
        project_placeholders = ', '.join([f':pid_{i}' for i in range(len(project_ids))])
        
        documents_query = text(f"""
            SELECT d.id, d.title, d.description, d.file_name, d.file_path, 
                   d.file_size, d.mime_type, d.document_type, d.category, 
                   d.subcategory, d.is_favorite, d.tags, 
                   d.created_at, d.updated_at, 
                   d.project_id, d.uploaded_by
            FROM documents d
            WHERE d.project_id IN ({project_placeholders})
            AND d.hidden_for_service_providers = FALSE
            ORDER BY d.created_at DESC
            LIMIT 200
        """)
        
        docs_params = {f'pid_{i}': pid for i, pid in enumerate(project_ids)}
        docs_result = await db.execute(documents_query, docs_params)
        documents = docs_result.fetchall()
        
        logger.info(f"[DEBUG] Gefundene Dokumente: {len(documents)}")
        
        # Konvertiere zu DocumentSummary
        document_summaries = []
        for doc in documents:
            try:
                summary = DocumentSummary(
                    id=doc.id,
                    title=doc.title,
                    description=doc.description,
                    file_name=doc.file_name,
                    file_path=doc.file_path,
                    file_size=doc.file_size or 0,
                    mime_type=doc.mime_type,
                    document_type=doc.document_type or "other",
                    category=doc.category,
                    subcategory=doc.subcategory,
                    is_favorite=doc.is_favorite or False,
                    status="active",  # Default-Status da Spalte nicht existiert
                    tags=doc.tags,
                    is_encrypted=False,  # Default-Wert da Spalte nicht existiert
                    created_at=doc.created_at,
                    updated_at=doc.updated_at,
                    accessed_at=None,  # Default-Wert da Spalte nicht existiert
                    project_id=doc.project_id,
                    uploaded_by=doc.uploaded_by,
                    milestone_id=None,  # Default-Wert da Spalte nicht existiert
                    milestone_title=None,
                    milestone_status=None,
                    milestone_category=None,
                    # Pflichtfelder für DocumentSummary
                    version_number="1",  # Default-Version (String!)
                    document_status="active",  # Default-Status
                    workflow_stage="completed",  # Default-Workflow-Stage
                    download_count=0  # Default-Download-Count
                )
                document_summaries.append(summary)
            except Exception as e:
                logger.error(f"[ERROR] Fehler beim Konvertieren von Dokument {doc.id}: {str(e)}")
                continue
        
        logger.info(f"[DEBUG] Erfolgreich {len(document_summaries)} Dokumente konvertiert")
        return document_summaries
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ERROR] Fehler beim Laden der Dienstleister-Dokumente: {str(e)}")
        import traceback
        logger.error(f"[ERROR] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Fehler beim Laden der Dokumente: {str(e)}")


@router.get("/sp/stats")
async def get_service_provider_category_statistics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lade Kategorie-Statistiken für Dienstleister-Dokumente"""
    try:
        # Importiere UserRole und UserType für Enum-Vergleiche
        from ..models.user import UserRole, UserType
        
        # Prüfe ob User ein Dienstleister ist
        is_service_provider = (
            current_user.user_type == UserType.SERVICE_PROVIDER or
            current_user.user_role == UserRole.DIENSTLEISTER
        )
        
        if not is_service_provider:
            raise HTTPException(
                status_code=403,
                detail="Nur Dienstleister können ihre Statistiken einsehen"
            )
        
        # Lade Statistiken von akzeptierten Quotes
        from sqlalchemy import text
        
        # Query für akzeptierte Quotes des Dienstleisters
        accepted_quotes_query = text("""
            SELECT DISTINCT q.project_id
            FROM quotes q
            WHERE q.service_provider_id = :service_provider_id
            AND q.status = 'accepted'
        """)
        
        quotes_result = await db.execute(accepted_quotes_query, {
            "service_provider_id": current_user.id
        })
        accepted_quotes = quotes_result.fetchall()
        
        if accepted_quotes:
            # Sammle alle Projekt-IDs
            project_ids = [quote.project_id for quote in accepted_quotes if quote.project_id]
            
            if project_ids:
                project_placeholders = ', '.join([f':pid_{i}' for i in range(len(project_ids))])
                
                # Lade Statistiken für Dokumente aus diesen Projekten
                stats_query = text(f"""
                    SELECT 
                        category,
                        subcategory,
                        COUNT(*) as document_count,
                        SUM(file_size) as total_size,
                        AVG(file_size) as avg_size,
                        COUNT(CASE WHEN is_favorite = true THEN 1 END) as favorite_count
                    FROM documents
                    WHERE project_id IN ({project_placeholders})
                    GROUP BY category, subcategory
                    ORDER BY category, subcategory
                """)
                
                stats_params = {f'pid_{i}': pid for i, pid in enumerate(project_ids)}
                result = await db.execute(stats_query, stats_params)
                stats = result.fetchall()
                
                # Formatiere Statistiken
                category_stats = {}
                for stat in stats:
                    category = stat.category or "other"
                    if category not in category_stats:
                        category_stats[category] = {
                            "total_documents": 0,
                            "total_size": 0,
                            "favorite_count": 0,
                            "subcategories": {}
                        }
                    
                    category_stats[category]["total_documents"] += stat.document_count
                    category_stats[category]["total_size"] += stat.total_size or 0
                    category_stats[category]["favorite_count"] += stat.favorite_count or 0
                    
                    if stat.subcategory:
                        category_stats[category]["subcategories"][stat.subcategory] = {
                            "document_count": stat.document_count,
                            "total_size": stat.total_size or 0,
                            "avg_size": stat.avg_size or 0,
                            "favorite_count": stat.favorite_count or 0
                        }
                
                return category_stats
            else:
                return {}
        else:
            return {}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fehler beim Laden der Dienstleister-Statistiken: {str(e)}")
        raise HTTPException(status_code=500, detail="Fehler beim Laden der Statistiken")


@router.get("/frontend/list")
async def get_documents_for_frontend(
    project_id: Optional[int] = Query(None, description="Projekt-ID (optional)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """ROBUSTER Frontend-Endpunkt für Dokumentenlisten - löst 404-Probleme"""
    try:
        logger.info(f"[FRONTEND_DOCS] Request von User {current_user.id}, project_id={project_id}")
        
        # ROBUSTE LÖSUNG: Immer erfolgreich antworten
        if project_id:
            # Spezifisches Projekt
            documents = await get_documents_for_project(db, project_id)
            documents = await add_milestone_info_to_documents(db, project_id, documents, current_user.id)
        else:
            # Alle Projekte des Users
            from sqlalchemy import text
            user_projects_query = text("""
                SELECT DISTINCT p.id 
                FROM projects p 
                WHERE p.owner_id = :user_id
                UNION
                SELECT DISTINCT q.project_id 
                FROM quotes q 
                WHERE q.service_provider_id = :user_id AND q.status = 'accepted'
            """)
            
            projects_result = await db.execute(user_projects_query, {"user_id": current_user.id})
            user_project_ids = [row.id for row in projects_result.fetchall()]
            
            documents = []
            for pid in user_project_ids:
                try:
                    project_docs = await get_documents_for_project(db, pid)
                    project_docs = await add_milestone_info_to_documents(db, pid, project_docs, current_user.id)
                    documents.extend(project_docs)
                except Exception as e:
                    logger.error(f"[FRONTEND_DOCS] Fehler bei Projekt {pid}: {e}")
                    continue
        
        # Konvertiere zu DocumentSummary für Frontend
        document_summaries = []
        for doc in documents:
            try:
                summary = DocumentSummary(
                    id=doc.id,
                    title=doc.title,
                    description=doc.description,
                    file_name=doc.file_name,
                    file_path=doc.file_path,
                    file_size=doc.file_size or 0,
                    mime_type=doc.mime_type,
                    document_type=doc.document_type or "other",
                    category=doc.category,
                    subcategory=doc.subcategory,
                    is_favorite=getattr(doc, 'is_favorite', False),
                    status=getattr(doc, 'status', 'active'),
                    tags=doc.tags,
                    is_encrypted=getattr(doc, 'is_encrypted', False),
                    created_at=doc.created_at,
                    updated_at=doc.updated_at,
                    accessed_at=getattr(doc, 'accessed_at', None),
                    project_id=doc.project_id,
                    uploaded_by=doc.uploaded_by,
                    milestone_id=getattr(doc, 'milestone_id', None),
                    milestone_title=getattr(doc, 'milestone_title', None),
                    milestone_status=getattr(doc, 'milestone_status', None),
                    milestone_category=getattr(doc, 'milestone_category', None),
                    version_number=getattr(doc, 'version_number', "1"),
                    document_status=getattr(doc, 'document_status', 'active'),
                    workflow_stage=getattr(doc, 'workflow_stage', 'completed'),
                    download_count=getattr(doc, 'download_count', 0)
                )
                document_summaries.append(summary)
            except Exception as e:
                logger.error(f"[FRONTEND_DOCS] Fehler beim Konvertieren von Dokument {doc.id}: {e}")
                continue
        
        logger.info(f"[FRONTEND_DOCS] Erfolgreich {len(document_summaries)} Dokumente für Frontend geladen")
        return document_summaries
        
    except Exception as e:
        logger.error(f"[FRONTEND_DOCS] Kritischer Fehler: {str(e)}")
        logger.exception(e)
        # ROBUSTE FALLBACK-LÖSUNG: Gebe leere Liste zurück
        return []


@router.delete("/sp/documents/{document_id}")
async def soft_delete_document_for_service_provider(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Soft-Delete für Service Provider: Macht ein Dokument nur für Service Provider unsichtbar,
    aber lässt es für Bauträger weiterhin sichtbar.
    """
    try:
        from ..models.user import UserRole, UserType
        
        # Prüfe ob User ein Service Provider ist
        is_service_provider = (
            current_user.user_type == UserType.SERVICE_PROVIDER or
            current_user.user_role == UserRole.DIENSTLEISTER
        )
        
        if not is_service_provider:
            logger.error(f"User {current_user.id} ist kein Service Provider")
            raise HTTPException(
                status_code=403,
                detail="Nur Service Provider können Dokumente für sich verstecken"
            )
        
        logger.info(f"[DEBUG] Service Provider {current_user.id} möchte Dokument {document_id} verstecken")
        
        # Prüfe ob das Dokument existiert und für diesen Service Provider sichtbar ist
        from sqlalchemy import text
        
        # Lade das Dokument mit allen relevanten Informationen
        doc_query = text("""
            SELECT d.id, d.title, d.project_id, d.uploaded_by, d.hidden_for_service_providers
            FROM documents d
            WHERE d.id = :document_id
        """)
        
        doc_result = await db.execute(doc_query, {"document_id": document_id})
        document = doc_result.fetchone()
        
        if not document:
            logger.error(f"Dokument {document_id} nicht gefunden")
            raise HTTPException(status_code=404, detail="Dokument nicht gefunden")
        
        if document.hidden_for_service_providers:
            logger.info(f"Dokument {document_id} ist bereits für Service Provider versteckt")
            return {"message": "Dokument ist bereits versteckt", "document_id": document_id}
        
        # Prüfe ob der Service Provider Zugriff auf dieses Dokument hat
        # (über akzeptierte Quotes)
        access_query = text("""
            SELECT COUNT(*) as count
            FROM quotes q
            WHERE q.service_provider_id = :service_provider_id
            AND q.status = 'accepted'
            AND q.project_id = :project_id
        """)
        
        access_result = await db.execute(access_query, {
            "service_provider_id": current_user.id,
            "project_id": document.project_id
        })
        access_count = access_result.fetchone()
        
        if not access_count or access_count.count == 0:
            logger.error(f"Service Provider {current_user.id} hat keinen Zugriff auf Dokument {document_id}")
            raise HTTPException(
                status_code=403,
                detail="Kein Zugriff auf dieses Dokument"
            )
        
        # Führe Soft-Delete durch
        update_query = text("""
            UPDATE documents 
            SET hidden_for_service_providers = TRUE,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :document_id
        """)
        
        await db.execute(update_query, {"document_id": document_id})
        await db.commit()
        
        logger.info(f"[SUCCESS] Dokument {document_id} für Service Provider {current_user.id} versteckt")
        
        return {
            "message": "Dokument wurde für Sie versteckt",
            "document_id": document_id,
            "title": document.title,
            "note": "Bauträger können das Dokument weiterhin sehen"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ERROR] Fehler beim Verstecken des Dokuments {document_id}: {str(e)}")
        import traceback
        logger.error(f"[ERROR] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Fehler beim Verstecken des Dokuments: {str(e)}")