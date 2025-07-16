from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import json
from datetime import datetime

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..models.project import Project
from ..schemas.canvas import (
    Canvas, CanvasCreate, CanvasUpdate, CanvasObject, CanvasObjectCreate, CanvasObjectUpdate,
    CollaborationArea, CollaborationAreaCreate, CollaborationAreaUpdate,
    CanvasState, CanvasExportRequest, CanvasExportResponse, ActiveUsersResponse, CanvasStatistics
)
from ..services.canvas_service import CanvasService

router = APIRouter(prefix="/canvas", tags=["canvas"])

# WebSocket-Verbindungen
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, canvas_id: int):
        await websocket.accept()
        if canvas_id not in self.active_connections:
            self.active_connections[canvas_id] = []
        self.active_connections[canvas_id].append(websocket)

    def disconnect(self, websocket: WebSocket, canvas_id: int):
        if canvas_id in self.active_connections:
            self.active_connections[canvas_id].remove(websocket)
            if not self.active_connections[canvas_id]:
                del self.active_connections[canvas_id]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast_to_canvas(self, message: str, canvas_id: int, exclude_websocket: WebSocket = None):
        if canvas_id in self.active_connections:
            for connection in self.active_connections[canvas_id]:
                if connection != exclude_websocket:
                    try:
                        await connection.send_text(message)
                    except:
                        # Verbindung ist nicht mehr aktiv
                        pass

manager = ConnectionManager()

# Canvas CRUD Endpunkte
@router.get("/{project_id}", response_model=Canvas)
async def get_canvas(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Holt das Canvas für ein Projekt"""
    canvas_service = CanvasService(db)
    
    # Prüfe Projekt-Zugriff
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Keine Berechtigung für dieses Projekt")
    
    canvas = canvas_service.get_or_create_canvas(project_id, current_user.id)
    return canvas

@router.post("/{project_id}", response_model=Canvas)
async def create_canvas(
    project_id: int,
    canvas_data: CanvasCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Erstellt ein neues Canvas für ein Projekt"""
    canvas_service = CanvasService(db)
    
    # Prüfe Projekt-Zugriff
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Keine Berechtigung für dieses Projekt")
    
    # Prüfe ob bereits ein Canvas existiert
    existing_canvas = canvas_service.get_canvas_by_project(project_id)
    if existing_canvas:
        raise HTTPException(status_code=400, detail="Canvas für dieses Projekt existiert bereits")
    
    canvas = canvas_service.create_canvas(canvas_data, current_user.id)
    return canvas

@router.put("/{canvas_id}", response_model=Canvas)
async def update_canvas(
    canvas_id: int,
    canvas_data: CanvasUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Aktualisiert ein Canvas"""
    canvas_service = CanvasService(db)
    
    canvas = db.query(Canvas).filter(Canvas.id == canvas_id).first()
    if not canvas:
        raise HTTPException(status_code=404, detail="Canvas nicht gefunden")
    
    # Prüfe Projekt-Zugriff
    project = db.query(Project).filter(Project.id == canvas.project_id).first()
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Keine Berechtigung für dieses Canvas")
    
    updated_canvas = canvas_service.update_canvas(canvas_id, canvas_data)
    if not updated_canvas:
        raise HTTPException(status_code=404, detail="Canvas nicht gefunden")
    
    return updated_canvas

@router.delete("/{canvas_id}")
async def delete_canvas(
    canvas_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Löscht ein Canvas"""
    canvas_service = CanvasService(db)
    
    canvas = db.query(Canvas).filter(Canvas.id == canvas_id).first()
    if not canvas:
        raise HTTPException(status_code=404, detail="Canvas nicht gefunden")
    
    # Prüfe Projekt-Zugriff
    project = db.query(Project).filter(Project.id == canvas.project_id).first()
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Keine Berechtigung für dieses Canvas")
    
    success = canvas_service.delete_canvas(canvas_id)
    if not success:
        raise HTTPException(status_code=404, detail="Canvas nicht gefunden")
    
    return {"message": "Canvas erfolgreich gelöscht"}

# Canvas State Management
@router.post("/{canvas_id}/save")
async def save_canvas_state(
    canvas_id: int,
    state: CanvasState,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Speichert den aktuellen Canvas-Zustand"""
    canvas_service = CanvasService(db)
    
    canvas = db.query(Canvas).filter(Canvas.id == canvas_id).first()
    if not canvas:
        raise HTTPException(status_code=404, detail="Canvas nicht gefunden")
    
    # Prüfe Projekt-Zugriff
    project = db.query(Project).filter(Project.id == canvas.project_id).first()
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Keine Berechtigung für dieses Canvas")
    
    success = canvas_service.save_canvas_state(canvas_id, state)
    if not success:
        raise HTTPException(status_code=500, detail="Fehler beim Speichern des Canvas")
    
    return {"message": "Canvas erfolgreich gespeichert"}

@router.get("/{canvas_id}/load", response_model=CanvasState)
async def load_canvas_state(
    canvas_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lädt den Canvas-Zustand"""
    canvas_service = CanvasService(db)
    
    canvas = db.query(Canvas).filter(Canvas.id == canvas_id).first()
    if not canvas:
        raise HTTPException(status_code=404, detail="Canvas nicht gefunden")
    
    # Prüfe Projekt-Zugriff
    project = db.query(Project).filter(Project.id == canvas.project_id).first()
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Keine Berechtigung für dieses Canvas")
    
    state = canvas_service.load_canvas_state(canvas_id)
    if not state:
        raise HTTPException(status_code=404, detail="Canvas-Zustand nicht gefunden")
    
    return state

# Canvas Objects
@router.post("/{canvas_id}/objects", response_model=CanvasObject)
async def create_canvas_object(
    canvas_id: int,
    object_data: CanvasObjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Erstellt ein neues Canvas-Objekt"""
    canvas_service = CanvasService(db)
    
    canvas = db.query(Canvas).filter(Canvas.id == canvas_id).first()
    if not canvas:
        raise HTTPException(status_code=404, detail="Canvas nicht gefunden")
    
    # Prüfe Projekt-Zugriff
    project = db.query(Project).filter(Project.id == canvas.project_id).first()
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Keine Berechtigung für dieses Canvas")
    
    canvas_object = canvas_service.create_canvas_object(canvas_id, object_data, current_user.id)
    return canvas_object

@router.put("/objects/{object_id}", response_model=CanvasObject)
async def update_canvas_object(
    object_id: str,
    object_data: CanvasObjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Aktualisiert ein Canvas-Objekt"""
    canvas_service = CanvasService(db)
    
    canvas_object = db.query(CanvasObject).filter(CanvasObject.object_id == object_id).first()
    if not canvas_object:
        raise HTTPException(status_code=404, detail="Canvas-Objekt nicht gefunden")
    
    # Prüfe Projekt-Zugriff
    canvas = db.query(Canvas).filter(Canvas.id == canvas_object.canvas_id).first()
    project = db.query(Project).filter(Project.id == canvas.project_id).first()
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Keine Berechtigung für dieses Canvas")
    
    updated_object = canvas_service.update_canvas_object(object_id, object_data)
    if not updated_object:
        raise HTTPException(status_code=404, detail="Canvas-Objekt nicht gefunden")
    
    return updated_object

@router.delete("/objects/{object_id}")
async def delete_canvas_object(
    object_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Löscht ein Canvas-Objekt"""
    canvas_service = CanvasService(db)
    
    canvas_object = db.query(CanvasObject).filter(CanvasObject.object_id == object_id).first()
    if not canvas_object:
        raise HTTPException(status_code=404, detail="Canvas-Objekt nicht gefunden")
    
    # Prüfe Projekt-Zugriff
    canvas = db.query(Canvas).filter(Canvas.id == canvas_object.canvas_id).first()
    project = db.query(Project).filter(Project.id == canvas.project_id).first()
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Keine Berechtigung für dieses Canvas")
    
    success = canvas_service.delete_canvas_object(object_id)
    if not success:
        raise HTTPException(status_code=404, detail="Canvas-Objekt nicht gefunden")
    
    return {"message": "Canvas-Objekt erfolgreich gelöscht"}

# Collaboration Areas
@router.post("/{canvas_id}/areas", response_model=CollaborationArea)
async def create_collaboration_area(
    canvas_id: int,
    area_data: CollaborationAreaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Erstellt einen neuen Kollaborationsbereich"""
    canvas_service = CanvasService(db)
    
    canvas = db.query(Canvas).filter(Canvas.id == canvas_id).first()
    if not canvas:
        raise HTTPException(status_code=404, detail="Canvas nicht gefunden")
    
    # Prüfe Projekt-Zugriff
    project = db.query(Project).filter(Project.id == canvas.project_id).first()
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Keine Berechtigung für dieses Canvas")
    
    collaboration_area = canvas_service.create_collaboration_area(canvas_id, area_data, current_user.id)
    return collaboration_area

@router.put("/areas/{area_id}", response_model=CollaborationArea)
async def update_collaboration_area(
    area_id: str,
    area_data: CollaborationAreaUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Aktualisiert einen Kollaborationsbereich"""
    canvas_service = CanvasService(db)
    
    collaboration_area = db.query(CollaborationArea).filter(CollaborationArea.area_id == area_id).first()
    if not collaboration_area:
        raise HTTPException(status_code=404, detail="Kollaborationsbereich nicht gefunden")
    
    # Prüfe Projekt-Zugriff
    canvas = db.query(Canvas).filter(Canvas.id == collaboration_area.canvas_id).first()
    project = db.query(Project).filter(Project.id == canvas.project_id).first()
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Keine Berechtigung für dieses Canvas")
    
    updated_area = canvas_service.update_collaboration_area(area_id, area_data)
    if not updated_area:
        raise HTTPException(status_code=404, detail="Kollaborationsbereich nicht gefunden")
    
    return updated_area

@router.delete("/areas/{area_id}")
async def delete_collaboration_area(
    area_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Löscht einen Kollaborationsbereich"""
    canvas_service = CanvasService(db)
    
    collaboration_area = db.query(CollaborationArea).filter(CollaborationArea.area_id == area_id).first()
    if not collaboration_area:
        raise HTTPException(status_code=404, detail="Kollaborationsbereich nicht gefunden")
    
    # Prüfe Projekt-Zugriff
    canvas = db.query(Canvas).filter(Canvas.id == collaboration_area.canvas_id).first()
    project = db.query(Project).filter(Project.id == canvas.project_id).first()
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Keine Berechtigung für dieses Canvas")
    
    success = canvas_service.delete_collaboration_area(area_id)
    if not success:
        raise HTTPException(status_code=404, detail="Kollaborationsbereich nicht gefunden")
    
    return {"message": "Kollaborationsbereich erfolgreich gelöscht"}

@router.post("/areas/{area_id}/assign/{user_id}")
async def assign_user_to_area(
    area_id: str,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Weist einen Nutzer einem Kollaborationsbereich zu"""
    canvas_service = CanvasService(db)
    
    collaboration_area = db.query(CollaborationArea).filter(CollaborationArea.area_id == area_id).first()
    if not collaboration_area:
        raise HTTPException(status_code=404, detail="Kollaborationsbereich nicht gefunden")
    
    # Prüfe Projekt-Zugriff
    canvas = db.query(Canvas).filter(Canvas.id == collaboration_area.canvas_id).first()
    project = db.query(Project).filter(Project.id == canvas.project_id).first()
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Keine Berechtigung für dieses Canvas")
    
    success = canvas_service.assign_user_to_area(area_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Kollaborationsbereich nicht gefunden")
    
    return {"message": "Nutzer erfolgreich zugewiesen"}

@router.delete("/areas/{area_id}/assign/{user_id}")
async def remove_user_from_area(
    area_id: str,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Entfernt einen Nutzer aus einem Kollaborationsbereich"""
    canvas_service = CanvasService(db)
    
    collaboration_area = db.query(CollaborationArea).filter(CollaborationArea.area_id == area_id).first()
    if not collaboration_area:
        raise HTTPException(status_code=404, detail="Kollaborationsbereich nicht gefunden")
    
    # Prüfe Projekt-Zugriff
    canvas = db.query(Canvas).filter(Canvas.id == collaboration_area.canvas_id).first()
    project = db.query(Project).filter(Project.id == canvas.project_id).first()
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Keine Berechtigung für dieses Canvas")
    
    success = canvas_service.remove_user_from_area(area_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Kollaborationsbereich nicht gefunden")
    
    return {"message": "Nutzer erfolgreich entfernt"}

# Active Users
@router.get("/{canvas_id}/active-users", response_model=ActiveUsersResponse)
async def get_active_users(
    canvas_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Holt alle aktiven Nutzer eines Canvas"""
    canvas_service = CanvasService(db)
    
    canvas = db.query(Canvas).filter(Canvas.id == canvas_id).first()
    if not canvas:
        raise HTTPException(status_code=404, detail="Canvas nicht gefunden")
    
    # Prüfe Projekt-Zugriff
    project = db.query(Project).filter(Project.id == canvas.project_id).first()
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Keine Berechtigung für dieses Canvas")
    
    users = canvas_service.get_active_users(canvas_id)
    return ActiveUsersResponse(users=users, total=len(users))

# Export
@router.post("/{canvas_id}/export", response_model=CanvasExportResponse)
async def export_canvas(
    canvas_id: int,
    export_request: CanvasExportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Exportiert ein Canvas als Bild oder PDF"""
    canvas_service = CanvasService(db)
    
    canvas = db.query(Canvas).filter(Canvas.id == canvas_id).first()
    if not canvas:
        raise HTTPException(status_code=404, detail="Canvas nicht gefunden")
    
    # Prüfe Projekt-Zugriff
    project = db.query(Project).filter(Project.id == canvas.project_id).first()
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Keine Berechtigung für dieses Canvas")
    
    result = canvas_service.export_canvas(canvas_id, export_request)
    return result

# Statistics
@router.get("/{canvas_id}/statistics", response_model=CanvasStatistics)
async def get_canvas_statistics(
    canvas_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Holt Statistiken für ein Canvas"""
    canvas_service = CanvasService(db)
    
    canvas = db.query(Canvas).filter(Canvas.id == canvas_id).first()
    if not canvas:
        raise HTTPException(status_code=404, detail="Canvas nicht gefunden")
    
    # Prüfe Projekt-Zugriff
    project = db.query(Project).filter(Project.id == canvas.project_id).first()
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Keine Berechtigung für dieses Canvas")
    
    statistics = canvas_service.get_canvas_statistics(canvas_id)
    return CanvasStatistics(**statistics)

# WebSocket für Echtzeit-Kollaboration
@router.websocket("/ws/{canvas_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    canvas_id: int,
    db: Session = Depends(get_db)
):
    await manager.connect(websocket, canvas_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Verarbeite Nachricht basierend auf Typ
            if message["type"] == "cursor_move":
                # Cursor-Position aktualisieren
                canvas_service = CanvasService(db)
                canvas_service.update_cursor_position(
                    message["session_id"],
                    message["data"]["x"],
                    message["data"]["y"]
                )
            
            # Broadcast an alle anderen Verbindungen
            await manager.broadcast_to_canvas(
                json.dumps(message),
                canvas_id,
                websocket
            )
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, canvas_id) 