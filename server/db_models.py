from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import os, sys
# Thêm thư mục gốc vào sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

@dataclass
class ChatSession:
    id: str
    session_name: str
    email: str
    expertor: str
    original_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @staticmethod
    def create(session_name: str, email: str = "guest", expertor: str = "default", 
               original_name: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> "ChatSession":
        return ChatSession(
            id=str(uuid.uuid4()),
            session_name=session_name,
            email=email,
            expertor=expertor,
            original_name=original_name or f"{email}/{expertor}/{session_name}",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata=metadata
        )


@dataclass
class ChatMessage:
    id: str
    session_id: str
    role: str
    content: str
    created_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @staticmethod
    def create(session_id: str, role: str, content: str, 
               metadata: Optional[Dict[str, Any]] = None) -> "ChatMessage":
        return ChatMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role=role,
            content=content,
            created_at=datetime.now(),
            metadata=metadata
        ) 