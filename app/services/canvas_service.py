from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import json
import os
from PIL import Image, ImageDraw, ImageFont
import io
import base64

from ..models.canvas import Canvas, CanvasObject, CollaborationArea, CanvasSession
from ..models.user import User
from ..models.project import Project
from ..schemas.canvas import (
    CanvasCreate, CanvasUpdate, CanvasObjectCreate, CanvasObjectUpdate,
    CollaborationAreaCreate, CollaborationAreaUpdate, CanvasSessionCreate,
    CanvasState, CanvasExportRequest, CanvasExportResponse, UserCursor
)

class CanvasService:
    def __init__(self, db: Session):
        self.db = db

    # Canvas Management
    def create_canvas(self, canvas_data: CanvasCreate, user_id: int) -> Canvas:
        """Erstellt ein neues Canvas für ein Projekt"""
        db_canvas = Canvas(
            project_id=canvas_data.project_id,
            name=canvas_data.name,
            description=canvas_data.description,
            viewport_x=canvas_data.viewport_x,
            viewport_y=canvas_data.viewport_y,
            viewport_scale=canvas_data.viewport_scale,
            created_by=user_id
        )
        self.db.add(db_canvas)
        self.db.commit()
        self.db.refresh(db_canvas)
        return db_canvas

    def get_canvas_by_project(self, project_id: int) -> Optional[Canvas]:
        """Holt das Canvas für ein Projekt"""
        return self.db.query(Canvas).filter(Canvas.project_id == project_id).first()

    def get_or_create_canvas(self, project_id: int, user_id: int) -> Canvas:
        """Holt ein Canvas oder erstellt es, falls es nicht existiert"""
        canvas = self.get_canvas_by_project(project_id)
        if not canvas:
            canvas_data = CanvasCreate(project_id=project_id)
            canvas = self.create_canvas(canvas_data, user_id)
        return canvas

    def update_canvas(self, canvas_id: int, canvas_data: CanvasUpdate) -> Optional[Canvas]:
        """Aktualisiert ein Canvas"""
        db_canvas = self.db.query(Canvas).filter(Canvas.id == canvas_id).first()
        if not db_canvas:
            return None
        
        for field, value in canvas_data.dict(exclude_unset=True).items():
            setattr(db_canvas, field, value)
        
        db_canvas.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(db_canvas)
        return db_canvas

    def delete_canvas(self, canvas_id: int) -> bool:
        """Löscht ein Canvas"""
        db_canvas = self.db.query(Canvas).filter(Canvas.id == canvas_id).first()
        if not db_canvas:
            return False
        
        self.db.delete(db_canvas)
        self.db.commit()
        return True

    # Canvas Objects
    def create_canvas_object(self, canvas_id: int, object_data: CanvasObjectCreate, user_id: int) -> CanvasObject:
        """Erstellt ein neues Canvas-Objekt"""
        db_object = CanvasObject(
            canvas_id=canvas_id,
            object_id=str(uuid.uuid4()),
            type=object_data.type.value,
            x=object_data.x,
            y=object_data.y,
            width=object_data.width,
            height=object_data.height,
            rotation=object_data.rotation,
            content=object_data.content,
            color=object_data.color,
            font_size=object_data.font_size,
            font_family=object_data.font_family,
            image_url=object_data.image_url,
            points=object_data.points,
            created_by=user_id
        )
        self.db.add(db_object)
        self.db.commit()
        self.db.refresh(db_object)
        return db_object

    def update_canvas_object(self, object_id: str, object_data: CanvasObjectUpdate) -> Optional[CanvasObject]:
        """Aktualisiert ein Canvas-Objekt"""
        db_object = self.db.query(CanvasObject).filter(CanvasObject.object_id == object_id).first()
        if not db_object:
            return None
        
        for field, value in object_data.dict(exclude_unset=True).items():
            if field == 'type' and value:
                setattr(db_object, field, value.value)
            else:
                setattr(db_object, field, value)
        
        db_object.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(db_object)
        return db_object

    def delete_canvas_object(self, object_id: str) -> bool:
        """Löscht ein Canvas-Objekt"""
        db_object = self.db.query(CanvasObject).filter(CanvasObject.object_id == object_id).first()
        if not db_object:
            return False
        
        self.db.delete(db_object)
        self.db.commit()
        return True

    def get_canvas_objects(self, canvas_id: int) -> List[CanvasObject]:
        """Holt alle Objekte eines Canvas"""
        return self.db.query(CanvasObject).filter(CanvasObject.canvas_id == canvas_id).all()

    # Collaboration Areas
    def create_collaboration_area(self, canvas_id: int, area_data: CollaborationAreaCreate, user_id: int) -> CollaborationArea:
        """Erstellt einen neuen Kollaborationsbereich"""
        db_area = CollaborationArea(
            canvas_id=canvas_id,
            area_id=str(uuid.uuid4()),
            name=area_data.name,
            x=area_data.x,
            y=area_data.y,
            width=area_data.width,
            height=area_data.height,
            color=area_data.color,
            assigned_users=area_data.assigned_users,
            created_by=user_id
        )
        self.db.add(db_area)
        self.db.commit()
        self.db.refresh(db_area)
        return db_area

    def update_collaboration_area(self, area_id: str, area_data: CollaborationAreaUpdate) -> Optional[CollaborationArea]:
        """Aktualisiert einen Kollaborationsbereich"""
        db_area = self.db.query(CollaborationArea).filter(CollaborationArea.area_id == area_id).first()
        if not db_area:
            return None
        
        for field, value in area_data.dict(exclude_unset=True).items():
            setattr(db_area, field, value)
        
        db_area.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(db_area)
        return db_area

    def delete_collaboration_area(self, area_id: str) -> bool:
        """Löscht einen Kollaborationsbereich"""
        db_area = self.db.query(CollaborationArea).filter(CollaborationArea.area_id == area_id).first()
        if not db_area:
            return False
        
        self.db.delete(db_area)
        self.db.commit()
        return True

    def get_collaboration_areas(self, canvas_id: int) -> List[CollaborationArea]:
        """Holt alle Kollaborationsbereiche eines Canvas"""
        return self.db.query(CollaborationArea).filter(CollaborationArea.canvas_id == canvas_id).all()

    def assign_user_to_area(self, area_id: str, user_id: int) -> bool:
        """Weist einen Nutzer einem Kollaborationsbereich zu"""
        db_area = self.db.query(CollaborationArea).filter(CollaborationArea.area_id == area_id).first()
        if not db_area:
            return False
        
        if user_id not in db_area.assigned_users:
            db_area.assigned_users.append(user_id)
            self.db.commit()
        return True

    def remove_user_from_area(self, area_id: str, user_id: int) -> bool:
        """Entfernt einen Nutzer aus einem Kollaborationsbereich"""
        db_area = self.db.query(CollaborationArea).filter(CollaborationArea.area_id == area_id).first()
        if not db_area:
            return False
        
        if user_id in db_area.assigned_users:
            db_area.assigned_users.remove(user_id)
            self.db.commit()
        return True

    # Canvas Sessions
    def create_canvas_session(self, canvas_id: int, user_id: int) -> CanvasSession:
        """Erstellt eine neue Canvas-Session für einen Nutzer"""
        # Deaktiviere alte Sessions des Nutzers
        old_sessions = self.db.query(CanvasSession).filter(
            and_(
                CanvasSession.canvas_id == canvas_id,
                CanvasSession.user_id == user_id,
                CanvasSession.is_active == True
            )
        ).all()
        
        for session in old_sessions:
            session.is_active = False
        
        # Erstelle neue Session
        db_session = CanvasSession(
            canvas_id=canvas_id,
            user_id=user_id,
            session_id=str(uuid.uuid4())
        )
        self.db.add(db_session)
        self.db.commit()
        self.db.refresh(db_session)
        return db_session

    def update_cursor_position(self, session_id: str, cursor_x: float, cursor_y: float) -> bool:
        """Aktualisiert die Cursor-Position eines Nutzers"""
        db_session = self.db.query(CanvasSession).filter(CanvasSession.session_id == session_id).first()
        if not db_session:
            return False
        
        db_session.cursor_x = cursor_x
        db_session.cursor_y = cursor_y
        db_session.last_activity = datetime.utcnow()
        self.db.commit()
        return True

    def deactivate_session(self, session_id: str) -> bool:
        """Deaktiviert eine Canvas-Session"""
        db_session = self.db.query(CanvasSession).filter(CanvasSession.session_id == session_id).first()
        if not db_session:
            return False
        
        db_session.is_active = False
        self.db.commit()
        return True

    def get_active_users(self, canvas_id: int) -> List[UserCursor]:
        """Holt alle aktiven Nutzer eines Canvas"""
        active_sessions = self.db.query(CanvasSession).filter(
            and_(
                CanvasSession.canvas_id == canvas_id,
                CanvasSession.is_active == True,
                CanvasSession.last_activity >= datetime.utcnow() - timedelta(minutes=5)
            )
        ).all()
        
        users = []
        for session in active_sessions:
            user = self.db.query(User).filter(User.id == session.user_id).first()
            if user:
                users.append(UserCursor(
                    user_id=user.id,
                    user_name=f"{user.first_name} {user.last_name}",
                    cursor_x=session.cursor_x,
                    cursor_y=session.cursor_y
                ))
        
        return users

    # Canvas State Management
    def save_canvas_state(self, canvas_id: int, state: CanvasState) -> bool:
        """Speichert den aktuellen Canvas-Zustand"""
        canvas = self.db.query(Canvas).filter(Canvas.id == canvas_id).first()
        if not canvas:
            return False
        
        # Aktualisiere Viewport
        canvas.viewport_x = state.viewport.get("x", 0.0)
        canvas.viewport_y = state.viewport.get("y", 0.0)
        canvas.viewport_scale = state.viewport.get("scale", 1.0)
        canvas.updated_at = datetime.utcnow()
        
        # Lösche alte Objekte und Bereiche
        self.db.query(CanvasObject).filter(CanvasObject.canvas_id == canvas_id).delete()
        self.db.query(CollaborationArea).filter(CollaborationArea.canvas_id == canvas_id).delete()
        
        # Erstelle neue Objekte
        for obj_data in state.objects:
            self.create_canvas_object(canvas_id, obj_data, obj_data.created_by)
        
        # Erstelle neue Bereiche
        for area_data in state.areas:
            self.create_collaboration_area(canvas_id, area_data, area_data.created_by)
        
        self.db.commit()
        return True

    def load_canvas_state(self, canvas_id: int) -> Optional[CanvasState]:
        """Lädt den Canvas-Zustand"""
        canvas = self.db.query(Canvas).filter(Canvas.id == canvas_id).first()
        if not canvas:
            return None
        
        objects = self.get_canvas_objects(canvas_id)
        areas = self.get_collaboration_areas(canvas_id)
        
        return CanvasState(
            objects=objects,
            areas=areas,
            viewport={
                "x": canvas.viewport_x,
                "y": canvas.viewport_y,
                "scale": canvas.viewport_scale
            }
        )

    # Export Functions
    def export_canvas(self, canvas_id: int, export_request: CanvasExportRequest) -> CanvasExportResponse:
        """Exportiert ein Canvas als Bild oder PDF"""
        canvas = self.db.query(Canvas).filter(Canvas.id == canvas_id).first()
        if not canvas:
            return CanvasExportResponse(success=False, message="Canvas nicht gefunden")
        
        try:
            # Erstelle ein Bild des Canvas
            image = self._render_canvas_to_image(canvas, export_request)
            
            if export_request.export_type == "download":
                # Speichere als temporäre Datei
                file_path = f"storage/exports/canvas_{canvas_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{export_request.format}"
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                image.save(file_path)
                
                return CanvasExportResponse(
                    success=True,
                    message="Export erfolgreich",
                    file_url=f"/exports/{os.path.basename(file_path)}"
                )
            else:
                # Speichere als Dokument
                document_id = self._save_as_document(canvas, image, export_request.format)
                
                return CanvasExportResponse(
                    success=True,
                    message="Canvas als Dokument gespeichert",
                    document_id=document_id
                )
                
        except Exception as e:
            return CanvasExportResponse(success=False, message=f"Export fehlgeschlagen: {str(e)}")

    def _render_canvas_to_image(self, canvas: Canvas, export_request: CanvasExportRequest) -> Image.Image:
        """Rendert das Canvas als Bild"""
        # Bestimme Canvas-Größe
        objects = self.get_canvas_objects(canvas.id)
        areas = self.get_collaboration_areas(canvas.id)
        
        if not objects and not areas:
            # Leeres Canvas
            width, height = 1920, 1080
        else:
            # Berechne Bounds
            min_x = min([obj.x for obj in objects] + [area.x for area in areas]) if objects or areas else 0
            max_x = max([obj.x + obj.width for obj in objects] + [area.x + area.width for area in areas]) if objects or areas else 1920
            min_y = min([obj.y for obj in objects] + [area.y for area in areas]) if objects or areas else 0
            max_y = max([obj.y + obj.height for obj in objects] + [area.y + area.height for area in areas]) if objects or areas else 1080
            
            width = int(max_x - min_x + 100)
            height = int(max_y - min_y + 100)
        
        # Erstelle Bild
        image = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(image)
        
        # Zeichne Bereiche
        for area in areas:
            x, y = int(area.x), int(area.y)
            w, h = int(area.width), int(area.height)
            draw.rectangle([x, y, x + w, y + h], outline=area.color, width=2)
            draw.text((x, y - 20), area.name, fill='black')
        
        # Zeichne Objekte
        for obj in objects:
            x, y = int(obj.x), int(obj.y)
            w, h = int(obj.width), int(obj.height)
            
            if obj.type == "rectangle":
                draw.rectangle([x, y, x + w, y + h], outline=obj.color, width=2)
            elif obj.type == "circle":
                draw.ellipse([x, y, x + w, y + h], outline=obj.color, width=2)
            elif obj.type == "sticky":
                draw.rectangle([x, y, x + w, y + h], fill=obj.color, outline='black', width=1)
                if obj.content:
                    # Einfacher Text-Rendering
                    lines = obj.content.split('\n')
                    font_size = obj.font_size or 12
                    y_offset = y + 5
                    for line in lines[:5]:  # Maximal 5 Zeilen
                        draw.text((x + 5, y_offset), line[:30], fill='black')  # Maximal 30 Zeichen
                        y_offset += font_size + 2
            elif obj.type == "text":
                if obj.content:
                    draw.text((x, y), obj.content, fill='black')
        
        return image

    def _save_as_document(self, canvas: Canvas, image: Image.Image, format: str) -> int:
        """Speichert das Canvas als Dokument"""
        # Konvertiere Bild zu Bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format=format.upper())
        img_byte_arr = img_byte_arr.getvalue()
        
        # Speichere als Dokument
        from ..models.document import Document
        from ..models.document import DocumentType
        
        document = Document(
            title=f"Canvas Export - {canvas.name}",
            description=f"Canvas Export vom {datetime.utcnow().strftime('%d.%m.%Y %H:%M')}",
            document_type=DocumentType.OTHER,
            project_id=canvas.project_id,
            uploaded_by=canvas.created_by,
            file_name=f"canvas_export.{format}",
            file_path=f"storage/documents/canvas_export_{canvas.id}.{format}",
            file_size=len(img_byte_arr),
            mime_type=f"image/{format}",
            is_public=True
        )
        
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        
        # Speichere Datei
        os.makedirs(os.path.dirname(document.file_path), exist_ok=True)
        with open(document.file_path, 'wb') as f:
            f.write(img_byte_arr)
        
        return document.id

    # Statistics
    def get_canvas_statistics(self, canvas_id: int) -> Dict[str, Any]:
        """Holt Statistiken für ein Canvas"""
        canvas = self.db.query(Canvas).filter(Canvas.id == canvas_id).first()
        if not canvas:
            return {}
        
        objects = self.get_canvas_objects(canvas_id)
        areas = self.get_collaboration_areas(canvas_id)
        active_users = self.get_active_users(canvas_id)
        
        # Berechne Canvas-Größe
        if objects or areas:
            min_x = min([obj.x for obj in objects] + [area.x for area in areas])
            max_x = max([obj.x + obj.width for obj in objects] + [area.x + area.width for area in areas])
            min_y = min([obj.y for obj in objects] + [area.y for area in areas])
            max_y = max([obj.y + obj.height for obj in objects] + [area.y + area.height for area in areas])
        else:
            min_x = max_x = min_y = max_y = 0
        
        return {
            "total_objects": len(objects),
            "total_areas": len(areas),
            "active_users": len(active_users),
            "last_activity": canvas.updated_at,
            "canvas_size": {
                "min_x": min_x,
                "max_x": max_x,
                "min_y": min_y,
                "max_y": max_y
            }
        } 