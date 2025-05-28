import psycopg2
from psycopg2.extras import RealDictCursor
import json
import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import os, sys

# Thêm thư mục gốc vào sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from db_models import ChatSession, ChatMessage

# Thiết lập logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PostgresRepository:
    def __init__(self, connection_params: Dict[str, Any]):
        self.connection_params = connection_params
        self._connection = None
    
    def get_connection(self):
        if self._connection is None or self._connection.closed:
            try:
                self._connection = psycopg2.connect(**self.connection_params)
                logger.info(f"Đã kết nối tới PostgreSQL: {self.connection_params['host']}:{self.connection_params['port']}/{self.connection_params['database']}")
            except Exception as e:
                logger.error(f"Lỗi kết nối PostgreSQL: {e}")
                raise
        return self._connection
    
    def close_connection(self):
        if self._connection and not self._connection.closed:
            self._connection.close()
            self._connection = None
            logger.info("Đã đóng kết nối PostgreSQL")


class ChatSessionRepository(PostgresRepository):
    def create_session(self, session: ChatSession) -> str:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            metadata_json = json.dumps(session.metadata) if session.metadata else None
            cursor.execute(
                """
                INSERT INTO chat_sessions 
                (id, session_name, email, expertor, original_name, created_at, updated_at, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    session.id,
                    session.session_name,
                    session.email,
                    session.expertor,
                    session.original_name,
                    session.created_at,
                    session.updated_at,
                    metadata_json
                )
            )
            session_id = cursor.fetchone()[0]
            conn.commit()
            logger.info(f"Đã tạo phiên chat mới với ID: {session_id}, name: {session.session_name}")
            return session_id
        except Exception as e:
            conn.rollback()
            logger.error(f"Lỗi khi tạo phiên chat: {e}")
            raise e
        finally:
            cursor.close()
    
    def get_session_by_id(self, session_id: str) -> Optional[ChatSession]:
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute(
                "SELECT * FROM chat_sessions WHERE id = %s",
                (session_id,)
            )
            result = cursor.fetchone()
            if not result:
                logger.warning(f"Không tìm thấy phiên chat với ID: {session_id}")
                return None
            
            metadata = json.loads(result["metadata"]) if result["metadata"] else None
            logger.info(f"Đã tìm thấy phiên chat với ID: {session_id}, name: {result['session_name']}")
            return ChatSession(
                id=result["id"],
                session_name=result["session_name"],
                email=result["email"],
                expertor=result["expertor"],
                original_name=result["original_name"],
                created_at=result["created_at"],
                updated_at=result["updated_at"],
                metadata=metadata
            )
        finally:
            cursor.close()
    
    def get_or_create_session(self, session_name: str, email: str, expertor: str) -> ChatSession:
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            logger.info(f"Tìm kiếm phiên chat với name={session_name}, email={email}, expertor={expertor}")
            
            # Kiểm tra session đã tồn tại chưa - tìm chính xác
            cursor.execute(
                """
                SELECT * FROM chat_sessions 
                WHERE session_name = %s AND email = %s AND expertor = %s
                """,
                (session_name, email, expertor)
            )
            result = cursor.fetchone()
            original_name = f"{email}/{expertor}/{session_name}"
            # Nếu không tìm thấy, thử tìm theo original_name
            if not result:
                logger.info(f"Không tìm thấy phiên chat chính xác, thử tìm theo original_name={session_name}")
                cursor.execute(
                    """
                    SELECT * FROM chat_sessions 
                    WHERE original_name = %s
                    """,
                    (original_name,)
                )
                result = cursor.fetchone()
            
            if result:
                # Session đã tồn tại
                metadata = json.loads(result["metadata"]) if result["metadata"] else None
                logger.info(f"Đã tìm thấy phiên chat: {result['id']}, name: {result['session_name']}")
                
                session = ChatSession(
                    id=result["id"],
                    session_name=result["session_name"],
                    email=result["email"],
                    expertor=result["expertor"],
                    original_name=result["original_name"],
                    created_at=result["created_at"],
                    updated_at=result["updated_at"],
                    metadata=metadata
                )
                
                # Kiểm tra số lượng tin nhắn trong phiên chat
                self._check_session_messages(session.id)
                
                return session
            else:
                # Tạo session mới
                logger.info(f"Không tìm thấy phiên chat, tạo mới với name={session_name}")
                session = ChatSession.create(
                    session_name=session_name,
                    email=email,
                    expertor=expertor,
                    original_name=f"{email}/{expertor}/{session_name}"
                )
                self.create_session(session)
                return session
        finally:
            cursor.close()
    
    def _check_session_messages(self, session_id: str) -> int:
        """
        Kiểm tra số lượng tin nhắn trong phiên chat - Hàm debug
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT COUNT(*) FROM chat_messages WHERE session_id = %s",
                (session_id,)
            )
            count = cursor.fetchone()[0]
            logger.info(f"Phiên chat {session_id} có {count} tin nhắn")
            return count
        except Exception as e:
            logger.error(f"Lỗi khi kiểm tra số lượng tin nhắn: {e}")
            return 0
        finally:
            cursor.close()
    
    def update_session(self, session: ChatSession) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            metadata_json = json.dumps(session.metadata) if session.metadata else None
            cursor.execute(
                """
                UPDATE chat_sessions 
                SET session_name = %s, email = %s, expertor = %s, 
                    original_name = %s, updated_at = %s, metadata = %s
                WHERE id = %s
                """,
                (
                    session.session_name,
                    session.email,
                    session.expertor,
                    session.original_name,
                    datetime.now(),
                    metadata_json,
                    session.id
                )
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()

    def get_sessions_by_email(self, email: str) -> List[ChatSession]:
        """
        Lấy danh sách tất cả phiên chat của một email
        
        Args:
            email: Email người dùng
            
        Returns:
            Danh sách các phiên chat
        """
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            logger.info(f"Đang lấy danh sách phiên chat cho email: {email}")
            
            cursor.execute(
                """
                SELECT * FROM chat_sessions 
                WHERE email = %s
                ORDER BY updated_at DESC
                """,
                (email,)
            )
            results = cursor.fetchall()
            
            sessions = []
            for result in results:
                metadata = json.loads(result["metadata"]) if result["metadata"] else None
                session = ChatSession(
                    id=result["id"],
                    session_name=result["session_name"],
                    email=result["email"],
                    expertor=result["expertor"],
                    original_name=result["original_name"],
                    created_at=result["created_at"],
                    updated_at=result["updated_at"],
                    metadata=metadata
                )
                sessions.append(session)
            
            logger.info(f"Đã tìm thấy {len(sessions)} phiên chat cho email: {email}")
            return sessions
        except Exception as e:
            logger.error(f"Lỗi khi lấy danh sách phiên chat: {e}")
            return []
        finally:
            cursor.close()

    def delete_session(self, session_id: str) -> bool:
        """
        Xóa một phiên chat và tất cả tin nhắn liên quan
        
        Args:
            session_id: ID của phiên chat cần xóa
            
        Returns:
            True nếu xóa thành công, False nếu thất bại
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # Bắt đầu transaction
            conn.autocommit = False
            
            # Xóa tất cả tin nhắn của phiên chat
            cursor.execute(
                "DELETE FROM chat_messages WHERE session_id = %s",
                (session_id,)
            )
            message_count = cursor.rowcount
            logger.info(f"Đã xóa {message_count} tin nhắn của phiên chat {session_id}")
            
            # Xóa phiên chat
            cursor.execute(
                "DELETE FROM chat_sessions WHERE id = %s",
                (session_id,)
            )
            session_deleted = cursor.rowcount > 0
            
            # Commit nếu xóa thành công
            if session_deleted:
                conn.commit()
                logger.info(f"Đã xóa phiên chat {session_id}")
            else:
                conn.rollback()
                logger.warning(f"Không tìm thấy phiên chat {session_id} để xóa")
            
            return session_deleted
        except Exception as e:
            conn.rollback()
            logger.error(f"Lỗi khi xóa phiên chat: {e}")
            return False
        finally:
            conn.autocommit = True
            cursor.close()
            
    def delete_session_by_name_and_email(self, session_name: str, email: str) -> bool:
        """
        Xóa một phiên chat và tất cả tin nhắn liên quan dựa trên tên và email
        
        Args:
            session_name: Tên phiên chat
            email: Email người dùng
            
        Returns:
            True nếu xóa thành công, False nếu thất bại
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # Tìm phiên chat trước
            cursor.execute(
                "SELECT id FROM chat_sessions WHERE session_name = %s AND email = %s",
                (session_name, email)
            )
            result = cursor.fetchone()
            
            if not result:
                logger.warning(f"Không tìm thấy phiên chat với tên {session_name} và email {email}")
                return False
                
            session_id = result[0]
            return self.delete_session(session_id)
        except Exception as e:
            logger.error(f"Lỗi khi tìm và xóa phiên chat: {e}")
            return False
        finally:
            cursor.close()


class ChatMessageRepository(PostgresRepository):
    def create_message(self, message: ChatMessage) -> str:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            metadata_json = json.dumps(message.metadata) if message.metadata else None
            cursor.execute(
                """
                INSERT INTO chat_messages 
                (id, session_id, role, content, created_at, metadata)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    message.id,
                    message.session_id,
                    message.role,
                    message.content,
                    message.created_at,
                    metadata_json
                )
            )
            message_id = cursor.fetchone()[0]
            conn.commit()
            return message_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
    
    def get_messages_by_session_id(self, session_id: str) -> List[ChatMessage]:
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            # Lấy giới hạn tin nhắn từ biến môi trường
            max_messages = int(os.getenv("MAX_CHAT_HISTORY_MESSAGES", "8"))
            
            cursor.execute(
                """
                SELECT * FROM chat_messages 
                WHERE session_id = %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (session_id, max_messages)
            )
            results = cursor.fetchall()
            
            messages = []
            for row in results:
                metadata = json.loads(row["metadata"]) if row["metadata"] else None
                messages.append(ChatMessage(
                    id=row["id"],
                    session_id=row["session_id"],
                    role=row["role"],
                    content=row["content"],
                    created_at=row["created_at"],
                    metadata=metadata
                ))
            
            # Đảo ngược danh sách để lấy theo thứ tự cũ (từ cũ đến mới)
            messages.reverse()
            
            return messages
        finally:
            cursor.close()
    
    def delete_messages_by_session_id(self, session_id: str) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "DELETE FROM chat_messages WHERE session_id = %s",
                (session_id,)
            )
            deleted_count = cursor.rowcount
            conn.commit()
            return deleted_count
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close() 