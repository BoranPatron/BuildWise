from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

# Canvas-Objekte Schemas
class CanvasObjectType(str, Enum):
    STICKY = "sticky"
    RECTANGLE = "rectangle"
    CIRCLE = "circle"
    LINE = "line"
    TEXT = "text"
    IMAGE = "image"

class CanvasObjectBase(BaseModel):
    type: CanvasObjectType
    x: float
    y: float
    width: float
    height: float
    rotation: float = 0.0
    content: Optional[str] = None
    color: str = "#ffbd59"
    font_size: Optional[int] = 16
    font_family: Optional[str] = "Arial"
    image_url: Optional[str] = None
    points: Optional[List[Dict[str, float]]] = None

class CanvasObjectCreate(CanvasObjectBase):
    pass

class CanvasObjectUpdate(BaseModel):
    type: Optional[CanvasObjectType] = None
    x: Optional[float] = None
    y: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    rotation: Optional[float] = None
    content: Optional[str] = None
    color: Optional[str] = None
    font_size: Optional[int] = None
    font_family: Optional[str] = None
    image_url: Optional[str] = None
    points: Optional[List[Dict[str, float]]] = None

class CanvasObject(CanvasObjectBase):
    id: int
    object_id: str
    canvas_id: int
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Kollaborationsbereich Schemas
class CollaborationAreaBase(BaseModel):
    name: str
    x: float
    y: float
    width: float
    height: float
    color: str = "#3b82f6"
    assigned_users: List[int] = []

class CollaborationAreaCreate(CollaborationAreaBase):
    pass

class CollaborationAreaUpdate(BaseModel):
    name: Optional[str] = None
    x: Optional[float] = None
    y: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    color: Optional[str] = None
    assigned_users: Optional[List[int]] = None

class CollaborationArea(CollaborationAreaBase):
    id: int
    area_id: str
    canvas_id: int
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Canvas Schemas
class CanvasBase(BaseModel):
    name: str = "Canvas"
    description: Optional[str] = None
    viewport_x: float = 0.0
    viewport_y: float = 0.0
    viewport_scale: float = 1.0

class CanvasCreate(CanvasBase):
    project_id: int

class CanvasUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    viewport_x: Optional[float] = None
    viewport_y: Optional[float] = None
    viewport_scale: Optional[float] = None

class Canvas(CanvasBase):
    id: int
    project_id: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    objects: List[CanvasObject] = []
    areas: List[CollaborationArea] = []

    class Config:
        from_attributes = True

# Canvas Session Schemas
class CanvasSessionBase(BaseModel):
    cursor_x: float = 0.0
    cursor_y: float = 0.0
    is_active: bool = True

class CanvasSessionCreate(CanvasSessionBase):
    canvas_id: int

class CanvasSessionUpdate(BaseModel):
    cursor_x: Optional[float] = None
    cursor_y: Optional[float] = None
    is_active: Optional[bool] = None

class CanvasSession(CanvasSessionBase):
    id: int
    session_id: str
    canvas_id: int
    user_id: int
    joined_at: datetime
    last_activity: datetime

    class Config:
        from_attributes = True

# Canvas State Schemas
class CanvasState(BaseModel):
    objects: List[CanvasObject] = []
    areas: List[CollaborationArea] = []
    viewport: Dict[str, float] = {"x": 0.0, "y": 0.0, "scale": 1.0}

class CanvasSaveRequest(BaseModel):
    objects: List[CanvasObjectCreate]
    areas: List[CollaborationAreaCreate]
    viewport: Dict[str, float]

# Export Schemas
class CanvasExportRequest(BaseModel):
    format: str = "png"  # png, pdf
    area: str = "full"  # full, selected
    area_id: Optional[str] = None
    export_type: str = "download"  # download, docs

class CanvasExportResponse(BaseModel):
    success: bool
    message: str
    file_url: Optional[str] = None
    document_id: Optional[int] = None

# WebSocket Message Schemas
class CanvasMessageType(str, Enum):
    OBJECT_ADD = "object_add"
    OBJECT_UPDATE = "object_update"
    OBJECT_DELETE = "object_delete"
    AREA_ADD = "area_add"
    AREA_UPDATE = "area_update"
    AREA_DELETE = "area_delete"
    CURSOR_MOVE = "cursor_move"
    USER_JOIN = "user_join"
    USER_LEAVE = "user_leave"

class CanvasMessage(BaseModel):
    type: CanvasMessageType
    data: Dict[str, Any]
    user_id: int
    timestamp: datetime

# User Cursor Schema
class UserCursor(BaseModel):
    user_id: int
    user_name: str
    cursor_x: float
    cursor_y: float

# Active Users Schema
class ActiveUsersResponse(BaseModel):
    users: List[UserCursor]
    total: int

# Canvas Statistics
class CanvasStatistics(BaseModel):
    total_objects: int
    total_areas: int
    active_users: int
    last_activity: datetime
    canvas_size: Dict[str, float]  # min_x, max_x, min_y, max_y 