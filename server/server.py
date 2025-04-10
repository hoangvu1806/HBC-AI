import os
import sys
import json
import asyncio
import time
import uuid
from typing import Dict, Any, Optional, List
from fastapi import Query

# Thêm thư mục gốc vào sys.path để import các module
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Đảm bảo thư mục hiện tại cũng có trong sys.path
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from dotenv import load_dotenv
except ImportError:
    print("Warning: python-dotenv không được cài đặt, không thể tải biến môi trường từ .env")
    def load_dotenv():
        pass

try:
    from fastapi import FastAPI, HTTPException, Request, Depends, BackgroundTasks
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import StreamingResponse
    from pydantic import BaseModel, Field
except ImportError:
    print("Error: FastAPI không được cài đặt. Vui lòng cài đặt với lệnh: pip install fastapi uvicorn")
    sys.exit(1)

# Import tương đối trong cùng package
try:
    from model import LLM
except ImportError:
    # Backup - cố gắng import với prefix
    try:
        from server.model import LLM
    except ImportError:
        print("Không thể import LLM. Kiểm tra cấu trúc thư mục.")

# Load biến môi trường
load_dotenv()

# Lấy provider từ biến môi trường
DEFAULT_PROVIDER = os.getenv("LLM_PROVIDER", "openai")

# Khởi tạo FastAPI app
app = FastAPI(
    title="RAG API",
    description="API cho hệ thống trợ lý AI sử dụng RAG",
    version="1.0.0"
)

# Thêm middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép tất cả origins trong môi trường dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Biến lưu trữ RAG Agent chính
main_rag_agent = None

# Khởi tạo RAG Agent khi cần
def initialize_rag_agent():
    """Khởi tạo RAG Agent để tránh import vòng tròn"""
    # Import trong hàm để tránh import vòng tròn
    try:
        # Đảm bảo thư mục hiện tại nằm trong sys.path
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
            
        # Import để kiểm tra
        import agent_tools
        print(f"agent_tools được import từ: {agent_tools.__file__}")
            
        from chat_with_RAG import RAGAgent
    except ImportError as e:
        print(f"Import error từ module tương đối ({e})")
        try:
            from server.chat_with_RAG import RAGAgent
        except ImportError as e:
            print(f"Error: Không thể import RAGAgent ({e}). Kiểm tra cấu trúc thư mục.")
            return None
            
    global main_rag_agent
    
    if main_rag_agent is None:
        try:
            main_rag_agent = RAGAgent(
                model_name=os.getenv("MODEL_NAME", "gpt-4o-mini"),
                temperature=float(os.getenv("TEMPERATURE", "0.7")),
                qdrant_host=os.getenv("QDRANT_HOST", "localhost"),
                qdrant_port=int(os.getenv("QDRANT_PORT", "6333")),
                collection_name=os.getenv("QDRANT_COLLECTION", "HBC_P_HCNS_KNOWLEDGE_BASE"),
                system_prompt_file="system_prompt.md",
                provider=DEFAULT_PROVIDER,
                use_postgres_memory=os.getenv("USE_POSTGRES_MEMORY", "True").lower() == "true"
            )
        except Exception as e:
            print(f"Error: Không thể khởi tạo RAGAgent: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    return main_rag_agent

# Định nghĩa các model Pydantic
class ChatRequest(BaseModel):
    topic: str = Field(..., description="Chủ đề của cuộc hội thoại")
    user_email: str = Field(..., description="Email người dùng")
    prompt: str = Field(..., description="Nội dung tin nhắn")
    mode: str = Field(..., description="Mode của cuộc hội thoại think hoặc normal")
    section_name: str = Field(..., description="Tên section của cuộc hội thoại")

class ChatResponse(BaseModel):
    output: str = Field(..., description="Phản hồi từ AI")
    tool_usages: Optional[List[Dict[str, Any]]] = Field(None, description="Các công cụ đã được sử dụng")
    topic: str = Field(..., description="Chủ đề của cuộc hội thoại")
    token_input: int = Field(..., description="Số token đã sử dụng")
    token_output: int = Field(..., description="Số token đã sử dụng")
    time_response: float = Field(..., description="Thời gian phản hồi")
    section_name: str = Field(..., description="Tên section của cuộc hội thoại")
    mode: str = Field(..., description="Mode của cuộc hội thoại think hoặc normal")

class ProviderRequest(BaseModel):
    provider: str = Field(..., description="Nhà cung cấp LLM mới (openai, gemini, palm)")

@app.post("/api/chat", response_model=ChatResponse)
async def chat(
    topic: str = Query(..., description="Chủ đề của cuộc hội thoại"),
    user_email: str = Query(..., description="Email người dùng"),
    prompt: str = Query(..., description="Nội dung tin nhắn"),
    section_name: str = Query(..., description="Tên section của cuộc hội thoại"),
    mode: str = Query(..., description="Mode của cuộc hội thoại think hoặc normal")
):
    """
    Endpoint để chat với AI
    """
    try:
        # Đảm bảo RAG Agent đã được khởi tạo
        global main_rag_agent
        if main_rag_agent is None:
            main_rag_agent = initialize_rag_agent()
        
        # Gọi RAG Agent
        time_start = time.time()
        response = main_rag_agent.chat(prompt, mode)
        time_end = time.time()
        time_response = time_end - time_start
        
        # Trả về kết quả
        return ChatResponse(
            output=response["result"],
            tool_usages=response.get("tool_usages"),
            topic=topic,
            token_input=0,
            token_output=0,
            time_response=time_response,
            section_name=section_name,
            mode=mode
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi: {str(e)}")

@app.post("/api/chat/stream")
async def stream_chat(
    topic: str = Query(..., description="Chủ đề của cuộc hội thoại"),
    prompt: str = Query(..., description="Nội dung tin nhắn"),
    section_name: str = Query(..., description="Tên section của cuộc hội thoại"),
    mode: str = Query(..., description="Mode của cuộc hội thoại think hoặc normal")
):
    """
    Endpoint để stream chat với AI
    """
    # Đảm bảo RAG Agent đã được khởi tạo
    global main_rag_agent
    if main_rag_agent is None:
        main_rag_agent = initialize_rag_agent()
    
    async def event_generator():
        try:
            # Gọi stream chat
            async for chunk in main_rag_agent.stream_chat(prompt):
                # Định dạng tin nhắn theo SSE
                data = {
                    'output': chunk, 
                    'topic': topic,
                    'section_name': section_name,
                    'mode': mode
                }
                yield f"data: {json.dumps(data)}\n\n"
            
            # Kết thúc stream
            done_data = {
                'output': '[DONE]', 
                'topic': topic,
                'section_name': section_name,
                'mode': mode
            }
            yield f"data: {json.dumps(done_data)}\n\n"
        except Exception as e:
            error_data = {
                'error': str(e), 
                'topic': topic,
                'section_name': section_name,
                'mode': mode
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    # Trả về StreamingResponse
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )

@app.post("/api/chat/clear")
async def clear_chat_history():
    """
    Endpoint để xóa lịch sử hội thoại
    """
    try:
        # Đảm bảo RAG Agent đã được khởi tạo
        global main_rag_agent
        if main_rag_agent is None:
            main_rag_agent = initialize_rag_agent()
        
        # Xóa lịch sử
        main_rag_agent.clear_memory()
        
        return {"status": "success", "message": "Đã xóa lịch sử hội thoại"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi: {str(e)}")

@app.get("/api/health")
async def health_check():
    """
    Endpoint kiểm tra trạng thái hoạt động của API
    """
    return {
        "status": "ok", 
        "message": "API đang hoạt động bình thường"
    }

@app.get("/api/config")
async def get_config():
    """
    Endpoint để kiểm tra các cấu hình môi trường hiện tại
    """
    # Đảm bảo RAG Agent đã được khởi tạo
    global main_rag_agent
    if main_rag_agent is None:
        initialize_rag_agent()
        
    config = {
        "model_name": os.getenv("MODEL_NAME", "gpt-4o-mini"),
        "temperature": float(os.getenv("TEMPERATURE", "0.7")),
        "qdrant_host": os.getenv("QDRANT_HOST", "localhost"),
        "qdrant_port": int(os.getenv("QDRANT_PORT", "6333")),
        "qdrant_collection": os.getenv("QDRANT_COLLECTION", "HBC_P_HCNS_KNOWLEDGE_BASE"),
        "provider": os.getenv("LLM_PROVIDER", "openai"),
        "available_providers": ["openai", "gemini", "palm"],
        "server_version": "1.0.0"
    }
    
    # Kiểm tra các API key (chỉ hiển thị tình trạng, không hiển thị giá trị thực)
    api_keys = {
        "openai_key": "Đã cấu hình" if os.getenv("OPENAI_KEY_APHONG") else "Chưa cấu hình",
        "gemini_key": "Đã cấu hình" if os.getenv("GEMINI_API_KEY") else "Chưa cấu hình",
        "palm_key": "Đã cấu hình" if os.getenv("PALM_API_KEY") else "Chưa cấu hình"
    }
    
    config["api_keys"] = api_keys
    
    # Kiểm tra kết nối tới Qdrant
    try:
        # Lấy danh sách collection từ Qdrant
        from qdrant_client import QdrantClient
        client = QdrantClient(host=config["qdrant_host"], port=config["qdrant_port"])
        collections = client.get_collections().collections
        collection_names = [collection.name for collection in collections]
        
        # Kiểm tra xem collection hiện tại có tồn tại không
        if config["qdrant_collection"] in collection_names:
            collection_exists = True
            # Lấy thêm thông tin về collection
            collection_info = client.get_collection(collection_name=config["qdrant_collection"])
            config["collection_info"] = {
                "dimension": collection_info.config.params.vectors.size,
                "distance": collection_info.config.params.vectors.distance,
                "vector_count": collection_info.vectors_count
            }
        else:
            collection_exists = False
            
        config["qdrant_status"] = {
            "connected": True,
            "collections": collection_names,
            "current_collection_exists": collection_exists
        }
        
    except Exception as e:
        config["qdrant_status"] = {
            "connected": False,
            "error": str(e)
        }
    
    return config

@app.post("/api/provider/change")
async def change_provider(request: ProviderRequest):
    """
    Endpoint để thay đổi provider của LLM
    
    Args:
        provider: Nhà cung cấp LLM mới
    """
    try:
        # Khởi tạo RAG Agent nếu cần
        global main_rag_agent
        if main_rag_agent is None:
            initialize_rag_agent()
        
        # Kiểm tra provider hợp lệ
        valid_providers = ["openai", "gemini", "palm"]
        if request.provider not in valid_providers:
            raise ValueError(f"Provider không hợp lệ. Chọn một trong: {', '.join(valid_providers)}")
        
        # Cập nhật agent chính
        if main_rag_agent:
            main_rag_agent.llm = LLM(
                model_name=os.getenv("MODEL_NAME", "gpt-4o-mini"),
                temperature=float(os.getenv("TEMPERATURE", "0.7")),
                provider=request.provider,
                system_prompt_file="system_prompt.md"
            )
        
        # Cập nhật biến môi trường
        os.environ["LLM_PROVIDER"] = request.provider
        
        return {
            "status": "success", 
            "message": f"Đã chuyển đổi provider sang {request.provider}"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi đổi provider: {str(e)}")

@app.post("/api/chat/init")
async def init_chat_session(
    session_name: str = Query(..., description="Tên phiên chat"),
    email: str = Query("guest", description="Email người dùng"),
    expertor: str = Query("default", description="Tên của chatbot")
):
    """
    Endpoint để khởi tạo phiên chat mới hoặc tải phiên chat cũ
    """
    try:
        # Đảm bảo RAG Agent đã được khởi tạo
        global main_rag_agent
        if main_rag_agent is None:
            main_rag_agent = initialize_rag_agent()
            if main_rag_agent is None:
                raise HTTPException(status_code=500, detail="Không thể khởi tạo RAG Agent")
        
        print(f"API: Khởi tạo phiên chat với thông tin: session_name={session_name}, email={email}, expertor={expertor}")
        
        # Kiểm tra cấu hình PostgreSQL
        use_postgres = os.getenv("USE_POSTGRES_MEMORY", "True").lower() == "true"
        if not use_postgres:
            return {
                "status": "warning", 
                "message": "PostgreSQL memory không được kích hoạt, không thể lưu trữ và lấy lịch sử phiên chat",
                "session_name": session_name
            }
        
        # Khởi tạo phiên chat mới
        session_id = main_rag_agent.llm.init_session(
            session_name=session_name,
            email=email,
            expertor=expertor
        )
        
        if not session_id:
            return {
                "status": "error", 
                "message": "Không thể khởi tạo hoặc tìm phiên chat. Kiểm tra logs để biết thêm thông tin", 
                "session_name": session_name
            }
        
        # Kiểm tra có load được tin nhắn hay không
        history = main_rag_agent.llm.get_history()
        message_count = len(history)
        
        return {
            "status": "success", 
            "message": f"Đã khởi tạo phiên chat và tải {message_count} tin nhắn", 
            "session_id": session_id,
            "session_name": session_name,
            "email": email,
            "expertor": expertor,
            "message_count": message_count,
            "has_history": message_count > 0
        }
    except Exception as e:
        import traceback
        error_detail = f"Lỗi: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        raise HTTPException(status_code=500, detail=error_detail)

# Route mặc định
@app.get("/")
async def root():
    return {
        "message": "API chat service",
        "version": "1.0.0",
        "endpoints": [
            "/api/chat",
            "/api/chat/stream",
            "/api/chat/clear",
            "/api/health",
            "/api/config",
            "/api/provider/change"
        ]
    }

# Khởi tạo RAG Agent khi server khởi động
@app.on_event("startup")
async def startup_event():
    """Sự kiện khởi động server"""
    global main_rag_agent
    main_rag_agent = initialize_rag_agent()
    print("RAG Agent đã được khởi tạo thành công")

# Hàm main để chạy server
if __name__ == "__main__":
    import uvicorn
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("SERVER_PORT", "8000"))
    
    # Khởi động uvicorn server
    uvicorn.run("server:app", host=host, port=port, reload=True) 