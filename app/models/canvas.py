from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
import uuid

class Canvas(Base):
    __tablename__ = "canvases"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(255), nullable=False, default="Canvas")
    description = Column(Text, nullable=True)
    viewport_x = Column(Float, default=0.0)
    viewport_y = Column(Float, default=0.0)
    viewport_scale = Column(Float, default=1.0)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Beziehungen
    project = relationship("Project", back_populates="canvases")
    creator = relationship("User", back_populates="created_canvases")
    objects = relationship("CanvasObject", back_populates="canvas", cascade="all, delete-orphan")
    areas = relationship("CollaborationArea", back_populates="canvas", cascade="all, delete-orphan")

class CanvasObject(Base):
    __tablename__ = "canvas_objects"
    
    id = Column(Integer, primary_key=True, index=True)
    canvas_id = Column(Integer, ForeignKey("canvases.id"), nullable=False)
    object_id = Column(String(255), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    type = Column(String(50), nullable=False)  # sticky, rectangle, circle, line, text, image
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    width = Column(Float, nullable=False)
    height = Column(Float, nullable=False)
    rotation = Column(Float, default=0.0)
    content = Column(Text, nullable=True)
    color = Column(String(50), default="#ffbd59")
    font_size = Column(Integer, default=16)
    font_family = Column(String(100), default="Arial")
    image_url = Column(String(500), nullable=True)
    points = Column(JSON, nullable=True)  # Für Linien und Pfade
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Beziehungen
    canvas = relationship("Canvas", back_populates="objects")
    creator = relationship("User", back_populates="created_canvas_objects")

class CollaborationArea(Base):
    __tablename__ = "collaboration_areas"
    
    id = Column(Integer, primary_key=True, index=True)
    canvas_id = Column(Integer, ForeignKey("canvases.id"), nullable=False)
    area_id = Column(String(255), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    width = Column(Float, nullable=False)
    height = Column(Float, nullable=False)
    color = Column(String(50), default="#3b82f6")
    assigned_users = Column(JSON, default=list)  # Liste von User-IDs
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Beziehungen
    canvas = relationship("Canvas", back_populates="areas")
    creator = relationship("User", back_populates="created_collaboration_areas")

class CanvasSession(Base):
    __tablename__ = "canvas_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    canvas_id = Column(Integer, ForeignKey("canvases.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String(255), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    cursor_x = Column(Float, default=0.0)
    cursor_y = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Beziehungen
    canvas = relationship("Canvas")
    user = relationship("User", back_populates="canvas_sessions") 