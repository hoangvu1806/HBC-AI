import os, sys
import tiktoken
from typing import List, Dict, Any, Optional, Union
from dotenv import load_dotenv

# LangChain imports - Thêm try/except để xử lý lỗi import
try:
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
except ImportError:
    print("Warning: langchain_openai không khả dụng, một số tính năng sẽ bị hạn chế")
    ChatOpenAI = None
    OpenAIEmbeddings = None

try:
    from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
except ImportError as ie:
    print(f"Warning: langchain_google_genai không khả dụng: {ie}")
    ChatGoogleGenerativeAI = None
    GoogleGenerativeAIEmbeddings = None

try:
    from langchain_community.llms import GooglePalm
    from langchain_community.embeddings import GooglePalmEmbeddings
except ImportError:
    print("Warning: Google Palm API không khả dụng, tính năng Palm sẽ không hoạt động")
    GooglePalm = None
    GooglePalmEmbeddings = None

# Các import LangChain core
try:
    from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
    from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
    from langchain_community.vectorstores import Qdrant
except ImportError as ie:
    print(f"Warning: Một số thành phần LangChain core không khả dụng: {ie}")

# Thêm thư mục gốc vào sys.path để import các module
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Load environment variables
load_dotenv()

# Thêm import cho PostgresChatMemory
from chat_memory import PostgresChatMemory
class LLM:
    """
    Lớp quản lý tương tác với các mô hình ngôn ngữ lớn (LLM) sử dụng LangChain
    """
    
    def __init__(self, 
                 model_name: str = "gpt-4o-mini", 
                 api_key: Optional[str] = None,
                 temperature: float = 0.4,
                 max_tokens: int = 16384,
                 provider: str = "openai",
                 system_prompt: Optional[str] = None,
                 system_prompt_file: Optional[str] = None,
                 use_postgres_memory: bool = False,
                 db_config: Optional[Dict[str, Any]] = None,
                 session_info: Optional[Dict[str, str]] = None):
        """
        Khởi tạo LLM với các tham số cấu hình
        
        Args:
            model_name: Tên mô hình (mặc định: gpt-4o-mini)
            api_key: API key (nếu None, sẽ lấy từ biến môi trường)
            temperature: Độ sáng tạo từ 0-1 (mặc định: 0.7)
            max_tokens: Số token tối đa cho phép trong kết quả
            provider: Nhà cung cấp LLM (hiện hỗ trợ: "openai", "gemini", "palm")
            system_prompt: System prompt mặc định
            system_prompt_file: Đường dẫn đến file system prompt
            use_postgres_memory: Sử dụng PostgreSQL để lưu trữ bộ nhớ chat
            db_config: Cấu hình kết nối database cho PostgresChatMemory
            session_info: Thông tin phiên chat khi sử dụng PostgresChatMemory (cần session_name, email, expertor)
        """
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.provider = provider
        
        # Đọc system prompt từ file nếu được chỉ định
        if system_prompt_file:
            self.system_prompt = self.load_system_prompt_from_file(system_prompt_file)
        elif system_prompt:
            self.system_prompt = system_prompt
        else:
            # Tự động load system prompt từ file mặc định
            current_dir = os.path.dirname(os.path.abspath(__file__))
            default_prompt_file = os.path.join(current_dir, "system_prompt.md")
            if os.path.exists(default_prompt_file):
                self.system_prompt = self.load_system_prompt_from_file(default_prompt_file)
            else:
                self.system_prompt = "Bạn là trợ lý AI thông minh và hữu ích."
        
        # Khởi tạo memory - PostgreSQL hoặc in-memory
        self.use_postgres_memory = use_postgres_memory and PostgresChatMemory is not None
        self.pg_memory = None
        
        if self.use_postgres_memory:
            try:
                self.pg_memory = PostgresChatMemory(db_config=db_config)
                
                # Khởi tạo session nếu có thông tin
                if session_info and all(k in session_info for k in ["session_name", "email", "expertor"]):
                    self.pg_memory.init_session(
                        session_name=session_info["session_name"],
                        email=session_info["email"],
                        expertor=session_info["expertor"]
                    )
            except Exception as e:
                print(f"Lỗi khi khởi tạo PostgresChatMemory: {e}")
                self.use_postgres_memory = False
                self.pg_memory = None
    
        
        # Khởi tạo LLM model dựa trên provider
        if provider == "openai":
            if ChatOpenAI is None:
                print("Warning: Sử dụng Fallback Mode cho OpenAI")
            else:
                # Lấy API key
                self.api_key = api_key or os.getenv("OPENAI_KEY_APHONG")
                if not self.api_key:
                    print("Warning: OpenAI API key không được cung cấp")
                else:
                    # Khởi tạo model LLM 
                    self.llm = ChatOpenAI(
                        model_name=model_name,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        streaming=True,
                        callbacks=[StreamingStdOutCallbackHandler()],
                        api_key=self.api_key
                    )
                    
                    # Khởi tạo embedding model
                    self.embedding_model = OpenAIEmbeddings(
                        model="text-embedding-3-small",
                        openai_api_key=self.api_key
                    )
            
        elif provider == "gemini":
            if ChatGoogleGenerativeAI is None:
                self.is_fallback_mode = True
                print("Warning: Sử dụng Fallback Mode cho Gemini")
            else:
                # Lấy API key
                self.gemini_api_key = api_key or os.getenv("GEMINI_API_KEY")
                if not self.gemini_api_key:
                    print("Warning: Gemini API key không được cung cấp")
                    self.is_fallback_mode = True
                else:
                    # Thiết lập model mặc định cho Gemini nếu không được chỉ định
                    if model_name == "gpt-4o-mini":
                        self.model_name = "gemini-pro"
                    
                    # Khởi tạo model LLM
                    self.llm = ChatGoogleGenerativeAI(
                        model=self.model_name,
                        temperature=temperature,
                        max_output_tokens=max_tokens,
                        google_api_key=self.gemini_api_key,
                        convert_system_message_to_human=True
                    )
                    
                    # Khởi tạo embedding model
                    self.embedding_model = GoogleGenerativeAIEmbeddings(
                        model="models/embedding-001",
                        google_api_key=self.gemini_api_key
                    )
        elif provider == "palm":
            if GooglePalm is None:
                self.is_fallback_mode = True
                print("Warning: Sử dụng Fallback Mode cho Palm")
            else:
                # Lấy API key
                self.palm_api_key = api_key or os.getenv("PALM_API_KEY")
                if not self.palm_api_key:
                    print("Warning: Google Palm API key không được cung cấp")
                    self.is_fallback_mode = True
                else:
                    # Thiết lập model mặc định cho Palm nếu không được chỉ định
                    if model_name == "gpt-4o-mini":
                        self.model_name = "text-bison-001"
                    
                    # Khởi tạo model LLM
                    self.llm = GooglePalm(
                        google_api_key=self.palm_api_key,
                        temperature=temperature,
                        max_output_tokens=max_tokens,
                        model_name=self.model_name
                    )
                    
                    # Khởi tạo embedding model
                    self.embedding_model = GooglePalmEmbeddings(
                        google_api_key=self.palm_api_key
                    )
        else:
            self.is_fallback_mode = True
            print(f"Provider không được hỗ trợ: {provider}")
        
        
        # Lịch sử hội thoại
        self.history = []
        
    def load_system_prompt_from_file(self, file_path: str) -> str:
        """
        Đọc system prompt từ file
        
        Args:
            file_path: Đường dẫn đến file system prompt
            
        Returns:
            Nội dung system prompt
        """
        try:
            # Kiểm tra xem file có tồn tại không
            if not os.path.exists(file_path):
                # Thử tìm file trong thư mục hiện tại
                current_dir = os.path.dirname(os.path.abspath(__file__))
                file_path = os.path.join(current_dir, os.path.basename(file_path))
                
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"Không tìm thấy file system prompt: {file_path}")
            
            # Đọc nội dung file
            with open(file_path, 'r', encoding='utf-8') as f:
                system_prompt = f.read().strip()
                
            return system_prompt
        except Exception as e:
            print(f"Lỗi khi đọc file system prompt: {e}")
            return "Bạn là trợ lý AI thông minh và hữu ích."
    
    def set_system_prompt_from_file(self, file_path: str):
        """
        Cập nhật system prompt từ file
        
        Args:
            file_path: Đường dẫn đến file system prompt
        """
        self.system_prompt = self.load_system_prompt_from_file(file_path)
    
    def _prepare_messages(self, prompt: str, history: Optional[List[Dict[str, str]]] = None, system_prompt: Optional[str] = None) -> List[Any]:
        """
        Chuẩn bị danh sách tin nhắn cho LangChain
        
        Args:
            prompt: Nội dung prompt
            history: Lịch sử hội thoại (tùy chọn)
            system_prompt: Ghi đè system prompt mặc định
            
        Returns:
            Danh sách các tin nhắn (messages) cho LangChain
        """
        messages = []
        
        # Thêm system message
        sys_prompt = system_prompt or self.system_prompt
        messages.append(SystemMessage(content=sys_prompt))
        
        # Thêm lịch sử hội thoại
        current_history = history if history is not None else self.history
        for msg in current_history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        
        # Thêm prompt hiện tại
        messages.append(HumanMessage(content=prompt))
        
        return messages
    
    def chat(self, 
             prompt: str, 
             history: Optional[List[Dict[str, str]]] = None,
             system_prompt: Optional[str] = None,
             temperature: Optional[float] = None,
             user_messages: str = None,
             max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """
        Gửi prompt đến LLM và nhận phản hồi
        
        Args:
            prompt: Nội dung prompt
            history: Lịch sử hội thoại (tùy chọn)
            system_prompt: Ghi đè system prompt mặc định
            temperature: Ghi đè temperature mặc định
            max_tokens: Ghi đè max_tokens mặc định
            
        Returns:
            Dict chứa kết quả và metadata
        """
        # Thiết lập các tham số
        temp = temperature or self.temperature
        max_tok = max_tokens or self.max_tokens
        
        # Chuẩn bị danh sách tin nhắn
        messages = self._prepare_messages(prompt, history, system_prompt)
        
        # Thiết lập các tham số nếu cần override
        if temp != self.temperature or max_tok != self.max_tokens:
            if self.provider == "openai":
                llm = ChatOpenAI(
                    model_name=self.model_name,
                    temperature=temp,
                    max_tokens=max_tok,
                    api_key=self.api_key
                )
            elif self.provider == "gemini":
                llm = ChatGoogleGenerativeAI(
                    model=self.model_name,
                    temperature=temp,
                    max_output_tokens=max_tok,
                    google_api_key=self.gemini_api_key,
                    convert_system_message_to_human=True
                )
            elif self.provider == "palm":
                llm = GooglePalm(
                    google_api_key=self.palm_api_key,
                    temperature=temp,
                    max_output_tokens=max_tok,
                    model_name=self.model_name
                )
        else:
            llm = self.llm
        
        # Gọi LLM
        response = llm.invoke(messages)
        
        # Xử lý kết quả
        result = {
            "content": response.content,
            "finish_reason": "stop",  # LangChain không cung cấp finish_reason
            "model": self.model_name,
        }
        
        # Cập nhật lịch sử
        self.history.append({"role": "user", "content": user_messages})
        self.history.append({"role": "assistant", "content": result["content"]})
        
        # Cập nhật lịch sử trong PostgreSQL nếu đang sử dụng
        if self.use_postgres_memory and self.pg_memory and self.pg_memory.current_session:
            try:
                self.pg_memory.add_message("user", user_messages)
                self.pg_memory.add_message("assistant", result["content"])
            except Exception as e:
                print(f"Lỗi khi cập nhật lịch sử PostgreSQL: {e}")
        
        return result
    
    def clear_history(self):
        """Xóa lịch sử hội thoại"""
        self.history = []
        
        # Xóa lịch sử trong PostgreSQL nếu đang sử dụng
        if self.use_postgres_memory and self.pg_memory and self.pg_memory.current_session:
            try:
                self.pg_memory.clear_messages()
            except Exception as e:
                print(f"Lỗi khi xóa lịch sử PostgreSQL: {e}")
    
    def set_history(self, history: List[Dict[str, str]]):
        """Đặt lịch sử hội thoại"""
        self.history = history.copy()
        
        # Cập nhật lịch sử trong PostgreSQL nếu đang sử dụng
        if self.use_postgres_memory and self.pg_memory and self.pg_memory.current_session:
            try:
                # Xóa lịch sử cũ
                self.pg_memory.clear_messages()
                
                # Thêm lịch sử mới
                for message in history:
                    self.pg_memory.add_message(message["role"], message["content"])
            except Exception as e:
                print(f"Lỗi khi cập nhật lịch sử PostgreSQL: {e}")
    
    def get_history(self) -> List[Dict[str, str]]:
        """
        Lấy lịch sử hội thoại, ưu tiên từ PostgreSQL nếu đang sử dụng
        """
        if self.use_postgres_memory and self.pg_memory and self.pg_memory.current_session:
            try:
                return self.pg_memory.get_messages()
            except Exception as e:
                print(f"Lỗi khi lấy lịch sử từ PostgreSQL, fallback về in-memory: {e}")
                return self.history.copy()
        else:
            return self.history.copy()
    
    def get_sessions_by_email(self, email: str) -> List[Dict[str, Any]]:
        """
        Lấy danh sách tất cả phiên chat của một email
        
        Args:
            email: Email người dùng
            
        Returns:
            Danh sách các phiên chat dưới dạng dictionaries
        """
        if not self.use_postgres_memory or not self.pg_memory:
            print("PostgreSQL memory không được kích hoạt, không thể lấy danh sách phiên chat")
            return []
            
        try:
            # Sử dụng repository để lấy danh sách phiên chat
            sessions = self.pg_memory.session_repo.get_sessions_by_email(email)
            
            # Chuẩn bị kết quả
            result = []
            for session in sessions:
                result.append({
                    "session_id": session.id,
                    "session_name": session.session_name,
                    "expertor": session.expertor,
                    "original_name": session.original_name,
                    "created_at": session.created_at.isoformat() if session.created_at else None,
                    "updated_at": session.updated_at.isoformat() if session.updated_at else None
                })
                
            return result
        except Exception as e:
            print(f"Lỗi khi lấy danh sách phiên chat: {e}")
            return []
    
    def get_history_by_session_id(self, session_id: str) -> List[Dict[str, str]]:
        """
        Lấy lịch sử hội thoại của một phiên chat cụ thể
        
        Args:
            session_id: ID của phiên chat
            
        Returns:
            Danh sách các tin nhắn dưới dạng dictionaries
        """
        if not self.use_postgres_memory or not self.pg_memory:
            print("PostgreSQL memory không được kích hoạt, không thể lấy lịch sử phiên chat")
            return []
            
        try:
            # Lấy tất cả tin nhắn của phiên chat
            messages = self.pg_memory.message_repo.get_messages_by_session_id(session_id)
            
            # Chuyển đổi về format chuẩn
            result = []
            for msg in messages:
                result.append({
                    "role": msg.role,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat() if msg.created_at else None
                })
                
            return result
        except Exception as e:
            print(f"Lỗi khi lấy lịch sử phiên chat: {e}")
            return []
    
    def init_session(self, session_name: str, email: str = "guest", expertor: str = "default") -> Optional[str]:
        """
        Khởi tạo phiên chat mới với PostgreSQL
        
        Args:
            session_name: Tên phiên chat
            email: Email người dùng
            expertor: Tên của chatbot
            
        Returns:
            ID của phiên chat hoặc None nếu không sử dụng PostgreSQL
        """
        if not self.use_postgres_memory:
            print(f"Postgres memory không được kích hoạt, không thể khởi tạo phiên chat: {session_name}")
            return None
            
        if not self.pg_memory:
            print(f"PostgresChatMemory chưa được khởi tạo, không thể khởi tạo phiên chat: {session_name}")
            return None
            
        try:
            print(f"Đang khởi tạo phiên chat: {session_name} (email: {email}, expertor: {expertor})")
            session_id = self.pg_memory.init_session(
                session_name=session_name,
                email=email,
                expertor=expertor
            )
            
            # Cập nhật lịch sử từ PostgreSQL
            messages = self.pg_memory.get_messages()
            print(f"Đã tải được {len(messages)} tin nhắn từ phiên chat: {session_name}")
            self.history = messages
            
            # Debug thông tin history
            if messages and len(messages) > 0:
                print(f"Thông tin tin nhắn đầu tiên: role={messages[0]['role']}")
                print(f"Thông tin tin nhắn cuối cùng: role={messages[-1]['role']}")
            else:
                print(f"Phiên chat {session_name} không có tin nhắn nào")
            
            return session_id
        except Exception as e:
            import traceback
            error_msg = f"Lỗi khi khởi tạo phiên chat PostgreSQL: {e}\n{traceback.format_exc()}"
            print(error_msg)
            return None
    
    def delete_session(self, session_name: str, email: str, expertor: str = "HCNS") -> bool:
        """
        Xóa một phiên chat theo tên, email và expertor
        
        Args:
            session_name: Tên phiên chat
            email: Email người dùng
            expertor: Tên chủ đề của chatbot (mặc định: "HCNS")
            
        Returns:
            True nếu xóa thành công, False nếu không tìm thấy hoặc có lỗi
        """
        if not self.use_postgres_memory:
            print(f"Postgres memory không được kích hoạt, không thể xóa phiên chat: {session_name}")
            return False
            
        if not self.pg_memory:
            print(f"PostgresChatMemory chưa được khởi tạo, không thể xóa phiên chat: {session_name}")
            return False
            
        try:
            print(f"Đang xóa phiên chat: {session_name} (email: {email}, expertor: {expertor})")
            
            # Kiểm tra phiên chat có tồn tại không
            sessions = self.pg_memory.session_repo.get_sessions_by_email(email)
            session_id = None
            print(sessions)
            for session in sessions:
                if session.session_name == session_name and session.expertor == expertor:
                    session_id = session.id
                    break
            
            if not session_id:
                print(f"Không tìm thấy phiên chat: {session_name} (email: {email}, expertor: {expertor})")
                return False
                
            # Xóa phiên chat theo ID
            is_deleted = self.pg_memory.session_repo.delete_session(session_id)
            
            if is_deleted:
                print(f"Đã xóa phiên chat: {session_name}")
                # Nếu phiên chat hiện tại bị xóa, clear lịch sử trên bộ nhớ
                if (
                    self.pg_memory.current_session and 
                    self.pg_memory.current_session.session_name == session_name and
                    self.pg_memory.current_session.email == email and
                    self.pg_memory.current_session.expertor == expertor
                ):
                    self.history = []
                    self.pg_memory.current_session = None
            else:
                print(f"Không thể xóa phiên chat: {session_name} (email: {email}, expertor: {expertor})")
                
            return is_deleted
        except Exception as e:
            import traceback
            error_msg = f"Lỗi khi xóa phiên chat: {e}\n{traceback.format_exc()}"
            print(error_msg)
            return False
    
    def embedding(self, text: str) -> List[float]:
        """
        Tạo embedding vector cho text đầu vào, với khả năng padding để phù hợp với kích thước vector 3072
        
        Args:
            text: Đoạn text cần tạo embedding
            
        Returns:
            List[float]: Vector embedding có kích thước 3072
        """
        try:

            if self.provider == "openai":
                # Sử dụng OpenAIEmbeddings từ langchain_openai
                try:
                    # Thay đổi model sang text-embedding-3-large để có kích thước 3072
                    self.embedding_model = OpenAIEmbeddings(
                        model="text-embedding-3-large",
                        openai_api_key=self.api_key
                    )
                    result = self.embedding_model.embed_query(text)
                    return result
                except Exception as e:
                    print(f"Lỗi khi tạo embedding với model OpenAI: {e}")
                    try:
                        # Thử embedding-3-small nếu embedding-3-large không khả dụng
                        self.embedding_model = OpenAIEmbeddings(
                            model="text-embedding-3-small",
                            openai_api_key=self.api_key
                        )
                        result = self.embedding_model.embed_query(text)
                        return result
                    except Exception as e2:
                        print(f"Lỗi khi tạo embedding với model OpenAI backup: {e2}")
                        # Trả về vector zero
                        return [0.0] * 3072
                        
            elif self.provider == "gemini":
                try:
                    self.embedding_model = GoogleGenerativeAIEmbeddings(
                        model="models/embedding-001",
                        google_api_key=self.gemini_api_key
                    )
                    result = self.embedding_model.embed_query(text)
                    return result
                except Exception as e:
                    print(f"Lỗi khi tạo embedding với Gemini: {e}")
                    return [0.0] * 3072
            elif self.provider == "palm":
                try:
                    self.embedding_model = GooglePalmEmbeddings(
                        google_api_key=self.palm_api_key
                    )
                    result = self.embedding_model.embed_query(text)
                    return result
                except Exception as e:
                    print(f"Lỗi khi tạo embedding với Palm: {e}")
                    return [0.0] * 3072
            else:
                raise ValueError(f"Provider không hỗ trợ: {self.provider}")
        except Exception as e:
            print(f"Lỗi khi tạo embedding: {e}")
            # Trả về vector zero trong trường hợp lỗi
            return [0.0] * 3072

    def get_token_count(self, text: str) -> int:
        encoding = tiktoken.get_encoding("cl100k_base")  # OK ✅
        tokens = encoding.encode(text)
        return len(tokens)

    def stream_chat(self, 
                   prompt: str, 
                   history: Optional[List[Dict[str, str]]] = None,
                   system_prompt: Optional[str] = None,
                   temperature: Optional[float] = None,
                   max_tokens: Optional[int] = None):
        """
        Stream chat với LLM
        
        Args:
            prompt: Nội dung prompt
            history: Lịch sử hội thoại (tùy chọn)
            system_prompt: Ghi đè system prompt mặc định
            temperature: Ghi đè temperature mặc định
            max_tokens: Ghi đè max_tokens mặc định
            
        Yields:
            Từng token trong phản hồi
        """
        # Thiết lập các tham số
        temp = temperature or self.temperature
        max_tok = max_tokens or self.max_tokens
        
        # Chuẩn bị danh sách tin nhắn
        messages = self._prepare_messages(prompt, history, system_prompt)
        
        # Stream handler để thu thập phản hồi
        stream_handler = StreamCallbackHandler()
        
        # Tạo LLM với stream
        if self.provider == "openai":
            streaming_llm = ChatOpenAI(
                model_name=self.model_name,
                temperature=temp,
                max_tokens=max_tok,
                api_key=self.api_key,
                streaming=True,
                callbacks=[stream_handler]
            )
        elif self.provider == "gemini":
            streaming_llm = ChatGoogleGenerativeAI(
                model=self.model_name,
                temperature=temp,
                max_output_tokens=max_tok,
                google_api_key=self.gemini_api_key,
                convert_system_message_to_human=True,
                streaming=True,
                callbacks=[stream_handler]
            )
        elif self.provider == "palm" or self.is_fallback_mode:
            # Google Palm không hỗ trợ streaming trực tiếp qua LangChain
            # Sử dụng non-streaming và mô phỏng stream
            palm_llm = GooglePalm(
                google_api_key=self.palm_api_key,
                temperature=temp,
                max_output_tokens=max_tok,
                model_name=self.model_name
            )
            
            # Tạo context với lịch sử và system prompt
            context = system_prompt or self.system_prompt
            for msg in self.history:
                if msg["role"] == "user":
                    context += f"\nUser: {msg['content']}"
                elif msg["role"] == "assistant":
                    context += f"\nAssistant: {msg['content']}"
            
            # Thêm prompt hiện tại
            prompt_with_context = f"{context}\nUser: {prompt}\nAssistant: "
            
            # Gọi LLM và mô phỏng stream
            response = palm_llm.invoke(prompt_with_context)
            
            # Mô phỏng stream bằng cách chia nhỏ phản hồi
            for i in range(0, len(response), 3):
                chunk = response[i:i+3]
                yield chunk
                
            # Lưu phản hồi đầy đủ để cập nhật lịch sử
            stream_handler.text = response
            
            # Thêm prompt và response vào lịch sử
            self.history.append({"role": "user", "content": prompt})
            self.history.append({"role": "assistant", "content": response})
            
            # Cập nhật lịch sử trong PostgreSQL nếu đang sử dụng
            if self.use_postgres_memory and self.pg_memory and self.pg_memory.current_session:
                try:
                    self.pg_memory.add_message("user", prompt)
                    self.pg_memory.add_message("assistant", response)
                except Exception as e:
                    print(f"Lỗi khi cập nhật lịch sử PostgreSQL: {e}")
            
            return
        
        # Thêm prompt vào lịch sử
        self.history.append({"role": "user", "content": prompt})
        
        # Chạy LLM trong stream mode (cho OpenAI và Gemini)
        for chunk in streaming_llm.stream(messages):
            if hasattr(chunk, 'content'):
                yield chunk.content
        
        # Cập nhật lịch sử với kết quả đầy đủ
        self.history.append({"role": "assistant", "content": stream_handler.text})
        
        # Cập nhật lịch sử trong PostgreSQL nếu đang sử dụng
        if self.use_postgres_memory and self.pg_memory and self.pg_memory.current_session:
            try:
                self.pg_memory.add_message("user", prompt)
                self.pg_memory.add_message("assistant", stream_handler.text)
            except Exception as e:
                print(f"Lỗi khi cập nhật lịch sử PostgreSQL: {e}")

    def get_session_id(self) -> Optional[str]:
        """
        Lấy ID của phiên chat hiện tại
        
        Returns:
            ID của phiên chat hoặc None nếu không có phiên chat nào được khởi tạo
        """
        if not self.use_postgres_memory or not self.pg_memory or not self.pg_memory.current_session:
            return None
            
        return self.pg_memory.current_session.id

