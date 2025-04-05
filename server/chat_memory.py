from typing import List, Dict, Any, Optional
import os, sys
import logging
from dataclasses import asdict
from dotenv import load_dotenv


# Thêm thư mục gốc vào sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)



from db_models import ChatSession, ChatMessage
from db_repository import ChatSessionRepository, ChatMessageRepository

# Thiết lập logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load biến môi trường
load_dotenv()

class PostgresChatMemory:
    def __init__(self, db_config: Optional[Dict[str, Any]] = None):
        """
        Khởi tạo bộ nhớ chat sử dụng PostgreSQL
        
        Args:
            db_config: Cấu hình kết nối database (nếu None sẽ dùng biến môi trường)
        """       
        # Cấu hình kết nối database
        if db_config is None:
            # Mặc định lấy từ biến môi trường
            self.db_config = {
                "host": os.getenv("POSTGRES_HOST", "localhost"),
                "port": int(os.getenv("POSTGRES_PORT", "5432")),
                "database": os.getenv("POSTGRES_DB", "chat_memory"),
                "user": os.getenv("POSTGRES_USER", "root"),
                "password": os.getenv("POSTGRES_PASSWORD", "it@HBC2025#")
            }
        else:
            self.db_config = db_config
        
        logger.info(f"Khởi tạo kết nối PostgreSQL với host={self.db_config['host']}, port={self.db_config['port']}, database={self.db_config['database']}, user={self.db_config['user']}")
        
        # Khởi tạo repositories
        self.session_repo = ChatSessionRepository(self.db_config)
        self.message_repo = ChatMessageRepository(self.db_config)
        
        # Kiểm tra kết nối
        try:
            conn = self.session_repo.get_connection()
            logger.info("Kết nối PostgreSQL thành công")
            # Đóng kết nối sau khi kiểm tra
            if conn and not conn.closed:
                conn.close()
        except Exception as e:
            logger.error(f"Lỗi khi kết nối PostgreSQL: {e}")
        
        # Thông tin phiên chat hiện tại
        self.current_session: Optional[ChatSession] = None
    
    def init_session(self, session_name: str, email: str = "guest", expertor: str = "default") -> str:
        """
        Khởi tạo hoặc lấy phiên chat dựa trên tên, email và expertor
        
        Args:
            session_name: Tên phiên chat
            email: Email người dùng
            expertor: Tên của chatbot
        
        Returns:
            ID của phiên chat
        """
        logger.info(f"Đang tìm/tạo phiên chat: session_name={session_name}, email={email}, expertor={expertor}")
        
        try:
            self.current_session = self.session_repo.get_or_create_session(
                session_name=session_name,
                email=email,
                expertor=expertor
            )
            logger.info(f"Đã tìm/tạo phiên chat với ID: {self.current_session.id}")
            
            # Kiểm tra số lượng tin nhắn trong phiên chat
            messages = self.message_repo.get_messages_by_session_id(self.current_session.id)
            logger.info(f"Phiên chat có {len(messages)} tin nhắn")
            
            return self.current_session.id
        except Exception as e:
            logger.error(f"Lỗi khi khởi tạo phiên chat: {e}")
            raise
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Thêm tin nhắn vào phiên chat hiện tại
        
        Args:
            role: Vai trò của người gửi ("user" hoặc "assistant")
            content: Nội dung tin nhắn
            metadata: Metadata bổ sung
        """
        if self.current_session is None:
            error_msg = "Chưa khởi tạo phiên chat. Hãy gọi init_session trước."
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            message = ChatMessage.create(
                session_id=self.current_session.id,
                role=role,
                content=content,
                metadata=metadata
            )
            message_id = self.message_repo.create_message(message)
            logger.info(f"Đã thêm tin nhắn mới với ID: {message_id}, role: {role}")
        except Exception as e:
            logger.error(f"Lỗi khi thêm tin nhắn: {e}")
            raise
    
    def get_messages(self) -> List[Dict[str, Any]]:
        """
        Lấy tất cả tin nhắn của phiên chat hiện tại
        
        Returns:
            Danh sách tin nhắn dưới dạng dictionaries
        """
        if self.current_session is None:
            error_msg = "Chưa khởi tạo phiên chat. Hãy gọi init_session trước."
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            messages = self.message_repo.get_messages_by_session_id(self.current_session.id)
            logger.info(f"Đã lấy {len(messages)} tin nhắn từ phiên chat ID: {self.current_session.id}")
            
            # Chuyển đổi về format dễ sử dụng
            result = [
                {
                    "role": msg.role,
                    "content": msg.content
                }
                for msg in messages
            ]
            return result
        except Exception as e:
            logger.error(f"Lỗi khi lấy tin nhắn: {e}")
            raise
    
    def clear_messages(self) -> int:
        """
        Xóa tất cả tin nhắn của phiên chat hiện tại
        
        Returns:
            Số tin nhắn đã xóa
        """
        if self.current_session is None:
            raise ValueError("Chưa khởi tạo phiên chat. Hãy gọi init_session trước.")
        
        return self.message_repo.delete_messages_by_session_id(self.current_session.id)
    
    def get_session_info(self) -> Dict[str, Any]:
        """
        Lấy thông tin phiên chat hiện tại
        
        Returns:
            Thông tin phiên chat dưới dạng dictionary
        """
        if self.current_session is None:
            raise ValueError("Chưa khởi tạo phiên chat. Hãy gọi init_session trước.")
        
        return {
            "id": self.current_session.id,
            "session_name": self.current_session.session_name,
            "email": self.current_session.email,
            "expertor": self.current_session.expertor,
            "created_at": self.current_session.created_at,
            "updated_at": self.current_session.updated_at
        }
    
    def close(self) -> None:
        """
        Đóng kết nối database
        """
        self.session_repo.close_connection()
        self.message_repo.close_connection() 