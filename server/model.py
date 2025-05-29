import os, sys
import tiktoken
from typing import List, Dict, Any, Optional, Union
from dotenv import load_dotenv
import asyncio
import aiohttp
import json
import time
# Đã loại bỏ import lru_cache


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

# Đã loại bỏ hàm cache embedding
def embedding_without_cache(model, text, provider):
    """
    Hàm tạo embedding không sử dụng cache
    
    Args:
        model: Model embedding
        text: Văn bản cần embedding
        provider: Nhà cung cấp (để phân biệt cache)
        
    Returns:
        List[float]: Vector embedding
    """
    if provider == "openai":
        return model.embed_query(text)
    elif provider == "gemini":
        return model.embed_query(text)
    elif provider == "palm":
        return model.embed_query(text)
    else:
        raise ValueError(f"Provider không hỗ trợ: {provider}")

# Quản lý event loop toàn cục
class EventLoopManager:
    """
    Quản lý event loop tập trung cho toàn bộ ứng dụng
    """
    _instance = None
    _loop = None
    _aiohttp_session = None

    @classmethod
    def get_instance(cls):
        """Singleton pattern để đảm bảo chỉ có một instance của EventLoopManager"""
        if cls._instance is None:
            cls._instance = EventLoopManager()
        return cls._instance

    def get_loop(self):
        """Lấy event loop hiện tại hoặc tạo mới nếu cần"""
        if self._loop is None or self._loop.is_closed():
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
        return self._loop

    async def get_aiohttp_session(self):
        """Lấy aiohttp session hiện tại hoặc tạo mới nếu cần"""
        if self._aiohttp_session is None or self._aiohttp_session.closed:
            # Cấu hình timeout
            timeout = aiohttp.ClientTimeout(
                total=300,  # Tổng thời gian tối đa cho toàn bộ request
                sock_connect=30,  # Thời gian kết nối socket
                sock_read=120  # Thời gian đọc từ socket
            )
            self._aiohttp_session = aiohttp.ClientSession(timeout=timeout, loop=self.get_loop())
        return self._aiohttp_session

    def run_async(self, coro):
        """Chạy coroutine trong event loop hiện tại hoặc tạo mới"""
        loop = self.get_loop()
        if loop.is_running():
            # Nếu loop đang chạy, tạo task mới
            return asyncio.create_task(coro)
        else:
            # Nếu loop chưa chạy, chạy coroutine đến khi hoàn thành
            return loop.run_until_complete(coro)

    def close(self):
        """Đóng session và event loop nếu cần"""
        if self._aiohttp_session and not self._aiohttp_session.closed:
            try:
                if self._loop and not self._loop.is_closed():
                    self._loop.run_until_complete(self._aiohttp_session.close())
            except Exception as e:
                print(f"Lỗi khi đóng aiohttp session: {e}")
                
        # KHÔNG đóng event loop - để ngăn lỗi "Event loop is closed"
        # Event loop sẽ tự đóng khi ứng dụng kết thúc

# Tạo singleton instance
event_loop_manager = EventLoopManager.get_instance()

# Helper class để chuyển đổi AsyncGenerator thành Generator đồng bộ
class AsyncToSyncGenerator:
    def __init__(self, async_gen):
        self.async_gen = async_gen
        # Luôn sử dụng event loop từ manager
        self.loop = event_loop_manager.get_loop()
        
    def __iter__(self):
        return self
        
    def __next__(self):
        try:
            # Đảm bảo sử dụng event loop hợp lệ
            if self.loop.is_closed():
                self.loop = event_loop_manager.get_loop()
                
            return self.loop.run_until_complete(self.async_gen.__anext__())
        except StopAsyncIteration:
            # KHÔNG đóng event loop ở đây
            raise StopIteration
            
    def __del__(self):
        # KHÔNG đóng event loop trong destructor
        pass

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
                        model="text-embedding-3-large",
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
        
        # Không tạo event loop hay aiohttp session trong constructor,
        # thay vào đó sẽ sử dụng từ EventLoopManager

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
    
    def _prepare_messages(self, prompt: str, history: Optional[List[Dict[str, str]]] = None, system_prompt: Optional[str] = None, for_langchain: bool = False) -> List[Any]:
        """
        Chuẩn bị danh sách tin nhắn cho LangChain hoặc API trực tiếp
        
        Args:
            prompt: Nội dung prompt
            history: Lịch sử hội thoại (tùy chọn)
            system_prompt: Ghi đè system prompt mặc định
            for_langchain: Nếu True, trả về đối tượng LangChain Message, nếu False, trả về dict
            
        Returns:
            Danh sách các tin nhắn (messages) cho LangChain hoặc API
        """
        sys_prompt = system_prompt or self.system_prompt
        current_history = history if history is not None else self.history
        
        if for_langchain:
            # Trả về đối tượng LangChain Message (format cũ)
            messages = []
            messages.append(SystemMessage(content=sys_prompt))
            
            for msg in current_history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
            
            messages.append(HumanMessage(content=prompt))
            return messages
        else:
            # Trả về dict (format cho API trực tiếp)
            messages = []
            messages.append({"role": "system", "content": sys_prompt})
            
            for msg in current_history:
                # Chỉ sử dụng các role được hỗ trợ bởi OpenAI API
                if msg["role"] in ["user", "assistant", "system"]:
                    messages.append({"role": msg["role"], "content": msg["content"]})
            
            messages.append({"role": "user", "content": prompt})
            return messages

    async def _ensure_aiohttp_session(self):
        """Đảm bảo có một aiohttp session sẵn sàng để sử dụng"""
        if self.aiohttp_session is None or self.aiohttp_session.closed:
            # Cấu hình timeout
            timeout = aiohttp.ClientTimeout(
                total=120,  # Tổng thời gian tối đa cho toàn bộ request
                sock_connect=10,  # Thời gian kết nối socket
                sock_read=60  # Thời gian đọc từ socket
            )
            
            # Lấy event loop hiện tại
            loop = event_loop_manager.get_loop()
            self.aiohttp_session = aiohttp.ClientSession(timeout=timeout, loop=loop)
        return self.aiohttp_session

    async def chat_async(self, 
             prompt: str, 
             history: Optional[List[Dict[str, str]]] = None,
             system_prompt: Optional[str] = None,
             temperature: Optional[float] = None,
             user_messages: str = None,
             max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """
        Phiên bản bất đồng bộ của phương thức chat
        """
        temp = temperature or self.temperature
        max_tok = max_tokens or self.max_tokens
        
        # Chuẩn bị danh sách tin nhắn (dict format cho API)
        messages = self._prepare_messages(prompt, history, system_prompt, for_langchain=False)
        
        # Lưu nội dung người dùng cho việc update history
        user_content = user_messages if user_messages else prompt
        
        try:
            start_time = time.time()
            
            # Xử lý theo provider
            if self.provider == "openai":
                # Sử dụng API trực tiếp qua aiohttp thay vì ChatOpenAI
                session = await event_loop_manager.get_aiohttp_session()
                
                payload = {
                    "model": self.model_name,
                    "messages": messages,
                    "temperature": temp,
                    "max_tokens": max_tok
                }
                
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                }
                
                async with session.post(
                    "https://api.openai.com/v1/chat/completions", 
                    headers=headers, 
                    json=payload
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"OpenAI API error: {response.status}, {error_text}")
                    
                    result = await response.json()
                    content = result["choices"][0]["message"]["content"]
                    
                    # Tính usage
                    input_tokens = result.get("usage", {}).get("prompt_tokens", self.get_token_count("".join([m.get("content", "") for m in messages])))
                    output_tokens = result.get("usage", {}).get("completion_tokens", self.get_token_count(content))
            
            elif self.provider == "gemini" and not self.is_fallback_mode:
                # Sử dụng ChatGoogleGenerativeAI nhưng với phương thức invoke_async nếu có
                try:
                    from langchain_google_genai import ChatGoogleGenerativeAI
                    llm = ChatGoogleGenerativeAI(
                        model=self.model_name,
                        temperature=temp,
                        max_output_tokens=max_tok,
                        google_api_key=self.gemini_api_key,
                    )
                    
                    # Sử dụng format LangChain cho Gemini
                    langchain_messages = self._prepare_messages(prompt, history, system_prompt, for_langchain=True)
                    
                    # Kiểm tra xem có phương thức invoke_async không
                    if hasattr(llm, 'invoke_async') and callable(getattr(llm, 'invoke_async')):
                        response = await llm.invoke_async(langchain_messages)
                    else:
                        # Fallback to sync method in a thread
                        response = await asyncio.to_thread(llm.invoke, langchain_messages)
                    
                    content = response.content
                    input_tokens = self.get_token_count("".join([m.get("content", "") for m in messages]))
                    output_tokens = self.get_token_count(content)
                except Exception as e:
                    print(f"Lỗi khi gọi Gemini API: {e}")
                    # Fallback to OpenAI
                    self.is_fallback_mode = True
                    return await self.chat_async(prompt, history, system_prompt, temperature, user_messages, max_tokens)
            
            elif self.provider == "palm" and not self.is_fallback_mode:
                # Tương tự cho Palm API
                try:
                    from langchain_google_palm import ChatGooglePalm
                    llm = ChatGooglePalm(
                        google_api_key=self.palm_api_key,
                        temperature=temp,
                        max_output_tokens=max_tok,
                    )
                    
                    # Sử dụng format LangChain cho Palm
                    langchain_messages = self._prepare_messages(prompt, history, system_prompt, for_langchain=True)
                    
                    # Kiểm tra xem có phương thức invoke_async không
                    if hasattr(llm, 'invoke_async') and callable(getattr(llm, 'invoke_async')):
                        response = await llm.invoke_async(langchain_messages)
                    else:
                        # Fallback to sync method in a thread
                        response = await asyncio.to_thread(llm.invoke, langchain_messages)
                    
                    content = response.content
                    input_tokens = self.get_token_count("".join([m.get("content", "") for m in messages]))
                    output_tokens = self.get_token_count(content)
                except Exception as e:
                    print(f"Lỗi khi gọi Palm API: {e}")
                    # Fallback to OpenAI
                    self.is_fallback_mode = True
                    return await self.chat_async(prompt, history, system_prompt, temperature, user_messages, max_tokens)
            else:
                # Fallback to OpenAI
                self.is_fallback_mode = True
                return await self.chat_async(prompt, history, system_prompt, temperature, user_messages, max_tokens)
                
            # Tính thời gian xử lý
            elapsed_time = time.time() - start_time
            
            # Lưu tin nhắn vào lịch sử
            self.history.append({"role": "user", "content": user_content})
            self.history.append({"role": "assistant", "content": content})
            
            # Cập nhật lịch sử trong PostgreSQL nếu đang sử dụng
            if self.use_postgres_memory and self.pg_memory and self.pg_memory.current_session:
                try:
                    await asyncio.to_thread(self.pg_memory.add_message, "user", user_content)
                    await asyncio.to_thread(self.pg_memory.add_message, "assistant", content)
                except Exception as e:
                    print(f"Lỗi khi cập nhật lịch sử PostgreSQL: {e}")
            
            return {
                "content": content,
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens
                },
                "elapsed_time": elapsed_time
            }
            
        except Exception as e:
            print(f"Lỗi trong chat_async: {e}")
            import traceback
            traceback.print_exc()
            
            # Trả về lỗi
            return {
                "content": f"Xin lỗi, đã xảy ra lỗi: {str(e)}",
                "usage": {
                    "input_tokens": 0,
                    "output_tokens": 0
                },
                "elapsed_time": 0,
                "error": str(e)
            }

    # Giữ lại phương thức chat đồng bộ nhưng sử dụng chat_async bên trong
    def chat(self, 
             prompt: str, 
             history: Optional[List[Dict[str, str]]] = None,
             system_prompt: Optional[str] = None,
             temperature: Optional[float] = None,
             user_messages: str = None,
             max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """
        Phiên bản đồng bộ của chat, gọi chat_async bên trong.
        """
        # Chạy coroutine trong event loop hiện tại hoặc tạo mới
        loop = event_loop_manager.get_loop()
        if loop.is_running():
            # Không thể chạy blocking call trong event loop đang chạy
            # Tạo một event loop mới tạm thời
            temp_loop = asyncio.new_event_loop()
            try:
                return temp_loop.run_until_complete(self.chat_async(
                    prompt=prompt,
                    history=history,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    user_messages=user_messages,
                    max_tokens=max_tokens
                ))
            finally:
                temp_loop.close()
        else:
            return loop.run_until_complete(self.chat_async(
                prompt=prompt,
                history=history,
                system_prompt=system_prompt,
                temperature=temperature,
                user_messages=user_messages,
                max_tokens=max_tokens
            ))

    async def stream_chat_async(self, 
                prompt: str, 
                history: Optional[List[Dict[str, str]]] = None,
                system_prompt: Optional[str] = None,
                temperature: Optional[float] = None,
                max_tokens: Optional[int] = None,
                user_messages: str = None):
        """
        Phiên bản bất đồng bộ của stream_chat
        """
        # Thiết lập các tham số
        temp = temperature or self.temperature
        max_tok = max_tokens or self.max_tokens
        
        # Chuẩn bị danh sách tin nhắn (dict format cho API)
        messages = self._prepare_messages(prompt, history, system_prompt, for_langchain=False)
        
        # Lưu tin nhắn người dùng vào lịch sử
        user_content = user_messages if user_messages else prompt
        self.history.append({"role": "user", "content": user_content})
        
        # Biến để lưu toàn bộ phản hồi
        full_response = ""
        
        try:
            # Xử lý theo provider
            if self.provider == "openai":
                # Sử dụng API trực tiếp qua aiohttp
                session = await event_loop_manager.get_aiohttp_session()
                
                payload = {
                    "model": self.model_name,
                    "messages": messages,
                    "temperature": temp,
                    "max_tokens": max_tok,
                    "stream": True
                }
                
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                }
                
                try:
                    async with session.post(
                        "https://api.openai.com/v1/chat/completions", 
                        headers=headers, 
                        json=payload
                    ) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            raise Exception(f"OpenAI API error: {response.status}, {error_text}")
                        
                        # Xử lý stream
                        async for line in response.content:
                            line = line.decode('utf-8').strip()
                            if line.startswith('data: ') and line != 'data: [DONE]':
                                try:
                                    data = json.loads(line[6:])  # Loại bỏ 'data: ' ở đầu
                                    if 'choices' in data and len(data['choices']) > 0:
                                        delta = data['choices'][0].get('delta', {})
                                        if 'content' in delta and delta['content']:
                                            chunk_text = delta['content']
                                            full_response += chunk_text
                                            yield chunk_text
                                except Exception as e:
                                    print(f"Lỗi khi xử lý chunk: {e}, line: {line}")
                except (asyncio.TimeoutError, aiohttp.ClientError) as e:
                    error_msg = f"Lỗi kết nối đến OpenAI API: {str(e)}"
                    print(error_msg)
                    yield error_msg
                    # Cập nhật lịch sử với thông báo lỗi
                    full_response = error_msg
            
            elif self.provider == "gemini" and not self.is_fallback_mode:
                # Sử dụng ChatGoogleGenerativeAI với streaming
                try:
                    from langchain_google_genai import ChatGoogleGenerativeAI
                    from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
                    
                    class CustomStreamingCallbackHandler(StreamingStdOutCallbackHandler):
                        def __init__(self):
                            super().__init__()
                            self.tokens = []
                            
                        def on_llm_new_token(self, token: str, **kwargs):
                            self.tokens.append(token)
                            return token
                    
                    handler = CustomStreamingCallbackHandler()
                    
                    llm = ChatGoogleGenerativeAI(
                        model=self.model_name,
                        temperature=temp,
                        max_output_tokens=max_tok,
                        google_api_key=self.gemini_api_key,
                        streaming=True,
                        callbacks=[handler]
                    )
                    
                    # Sử dụng format LangChain cho Gemini
                    langchain_messages = self._prepare_messages(prompt, history, system_prompt, for_langchain=True)
                    
                    # Chạy trong một thread riêng biệt để không block event loop
                    async def run_streaming():
                        def _run_stream():
                            return llm.invoke(langchain_messages)
                        
                        # Chạy hàm đồng bộ trong thread pool
                        await asyncio.to_thread(_run_stream)
                        return handler.tokens
                    
                    tokens_future = asyncio.create_task(run_streaming())
                    
                    # Sử dụng polling để lấy tokens khi chúng sẵn sàng
                    last_index = 0
                    max_wait_time = 60  # Tối đa đợi 60 giây
                    start_time = time.time()
                    
                    while True:
                        current_time = time.time()
                        if current_time - start_time > max_wait_time:
                            error_msg = "Timeout khi đợi phản hồi từ Gemini API"
                            print(error_msg)
                            yield error_msg
                            full_response = error_msg
                            break
                            
                        if not tokens_future.done():
                            tokens = handler.tokens
                            if len(tokens) > last_index:
                                for i in range(last_index, len(tokens)):
                                    chunk_text = tokens[i]
                                    full_response += chunk_text
                                    yield chunk_text
                                last_index = len(tokens)
                                # Reset thời gian mỗi khi nhận được token mới
                                start_time = time.time()
                            await asyncio.sleep(0.01)  # Giảm CPU usage
                        else:
                            # Khi task hoàn thành, đảm bảo lấy tất cả tokens còn lại
                            tokens = handler.tokens
                            if len(tokens) > last_index:
                                for i in range(last_index, len(tokens)):
                                    chunk_text = tokens[i]
                                    full_response += chunk_text
                                    yield chunk_text
                            break
                except Exception as e:
                    print(f"Lỗi khi gọi Gemini API streaming: {e}")
                    error_msg = f"Lỗi khi gọi Gemini API: {str(e)}"
                    yield error_msg
                    full_response = error_msg
            
            elif self.provider == "palm" and not self.is_fallback_mode:
                # Palm API không hỗ trợ streaming, fallback sang OpenAI
                print("Palm API không hỗ trợ streaming, sử dụng OpenAI fallback")
                self.is_fallback_mode = True
                async for chunk in self.stream_chat_async(prompt, history, system_prompt, temperature, max_tokens, user_messages):
                    yield chunk
                return
            else:
                # Fallback to OpenAI
                self.is_fallback_mode = True
                async for chunk in self.stream_chat_async(prompt, history, system_prompt, temperature, max_tokens, user_messages):
                    yield chunk
                return
            
            # Cập nhật lịch sử với kết quả đầy đủ
            self.history.append({"role": "assistant", "content": full_response})
            
            # Cập nhật lịch sử trong PostgreSQL nếu đang sử dụng
            if self.use_postgres_memory and self.pg_memory and self.pg_memory.current_session:
                try:
                    await asyncio.to_thread(self.pg_memory.add_message, "user", user_content)
                    await asyncio.to_thread(self.pg_memory.add_message, "assistant", full_response)
                except Exception as e:
                    print(f"Lỗi khi cập nhật lịch sử PostgreSQL: {e}")
                    
        except Exception as e:
            print(f"Lỗi trong stream_chat_async: {e}")
            import traceback
            traceback.print_exc()
            
            # Trả về thông báo lỗi
            error_message = f"Xin lỗi, đã xảy ra lỗi: {str(e)}"
            yield error_message
            # Cập nhật lịch sử với thông báo lỗi
            self.history.append({"role": "assistant", "content": error_message})

    # Giữ lại phương thức stream_chat đồng bộ nhưng tái cấu trúc
    def stream_chat(self, 
                prompt: str, 
                history: Optional[List[Dict[str, str]]] = None,
                system_prompt: Optional[str] = None,
                temperature: Optional[float] = None,
                max_tokens: Optional[int] = None,
                user_messages: str = None):
        """
        Phiên bản đồng bộ của stream_chat, tương thích với interface cũ.
        """
        # Tạo generator từ coroutine
        async def run_async_stream():
            async for chunk in self.stream_chat_async(
                prompt=prompt,
                history=history,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                user_messages=user_messages
            ):
                yield chunk
        
        # Trả về generator đồng bộ từ generator bất đồng bộ
        return AsyncToSyncGenerator(run_async_stream())

    async def embedding_async(self, text: str) -> List[float]:
        """
        Phiên bản bất đồng bộ của embedding
        """
        try:
            if self.provider == "openai":
                # Sử dụng aiohttp thay vì OpenAIEmbeddings
                session = await event_loop_manager.get_aiohttp_session()
                
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                }
                
                # Thử với model text-embedding-3-large
                try:
                    payload = {
                        "model": "text-embedding-3-large",
                        "input": text
                    }
                    
                    async with session.post(
                        "https://api.openai.com/v1/embeddings", 
                        headers=headers, 
                        json=payload
                    ) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            raise Exception(f"OpenAI API error: {response.status}, {error_text}")
                        
                        result = await response.json()
                        return result["data"][0]["embedding"]
                except Exception as e:
                    print(f"Lỗi khi tạo embedding với model text-embedding-3-large: {e}")
                    
                    # Thử với model text-embedding-3-small
                    try:
                        payload = {
                            "model": "text-embedding-3-small",
                            "input": text
                        }
                        
                        async with session.post(
                            "https://api.openai.com/v1/embeddings", 
                            headers=headers, 
                            json=payload
                        ) as response:
                            if response.status != 200:
                                error_text = await response.text()
                                raise Exception(f"OpenAI API error: {response.status}, {error_text}")
                            
                            result = await response.json()
                            return result["data"][0]["embedding"]
                    except Exception as e2:
                        print(f"Lỗi khi tạo embedding với model text-embedding-3-small: {e2}")
                        # Trả về vector zero
                        return [0.0] * 3072
            
            elif self.provider == "gemini":
                # Sử dụng GoogleGenerativeAIEmbeddings trong thread pool
                try:
                    from langchain_google_genai import GoogleGenerativeAIEmbeddings
                    
                    def _create_embedding():
                        embedding_model = GoogleGenerativeAIEmbeddings(
                            model="models/embedding-001",
                            google_api_key=self.gemini_api_key
                        )
                        return embedding_model.embed_query(text)
                    
                    return await asyncio.to_thread(_create_embedding)
                except Exception as e:
                    print(f"Lỗi khi tạo embedding với Gemini: {e}")
                    return [0.0] * 3072
            
            elif self.provider == "palm":
                # Sử dụng GooglePalmEmbeddings trong thread pool
                try:
                    from langchain_google_palm import GooglePalmEmbeddings
                    
                    def _create_embedding():
                        embedding_model = GooglePalmEmbeddings(
                            google_api_key=self.palm_api_key
                        )
                        return embedding_model.embed_query(text)
                    
                    return await asyncio.to_thread(_create_embedding)
                except Exception as e:
                    print(f"Lỗi khi tạo embedding với Palm: {e}")
                    return [0.0] * 3072
            else:
                raise ValueError(f"Provider không hỗ trợ: {self.provider}")
        except Exception as e:
            print(f"Lỗi khi tạo embedding: {e}")
            # Trả về vector zero trong trường hợp lỗi
            return [0.0] * 3072

    # Giữ lại phương thức embedding đồng bộ
    def embedding(self, text: str) -> List[float]:
        self.embedding_model = OpenAIEmbeddings(
            model="text-embedding-3-large",
            openai_api_key=self.api_key
        )
        result = self.embedding_model.embed_query(text)
        return result
        # return asyncio.run(self.embedding_async(text))

    def get_token_count(self, text: str) -> int:
        encoding = tiktoken.get_encoding("cl100k_base")  # OK ✅
        tokens = encoding.encode(text)
        return len(tokens)

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
            
    def get_session_id(self) -> Optional[str]:
        """
        Lấy ID của phiên chat hiện tại
        
        Returns:
            ID của phiên chat hoặc None nếu không có phiên chat nào được khởi tạo
        """
        if not self.use_postgres_memory or not self.pg_memory or not self.pg_memory.current_session:
            return None
            
        return self.pg_memory.current_session.id

