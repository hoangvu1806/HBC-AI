import os
import sys
import json
import time
import httpx
import requests
import logging
from typing import Dict, Any, List, Optional
from fastapi import Query, File, Header, Depends, Form
import datetime
import pathlib
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Thiết lập logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Tạo thread pool executor cho các tác vụ blocking
# Tu0103ng su1ed1 workers u0111u1ec3 xu1eed lu00fd nhiu1ec1u CPU-bound tasks hu01a1n (chu1ee7 yu1ebfu lu00e0 xu1eed lu00fd embedding vu00e0 tru01b0y xu1ea5t document)
thread_pool = ThreadPoolExecutor(max_workers=30)

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
    logger.warning("python-dotenv không được cài đặt, không thể tải biến môi trường từ .env")
    def load_dotenv():
        pass

try:
    from fastapi import FastAPI, HTTPException, Request, Depends, BackgroundTasks
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import StreamingResponse
    from pydantic import BaseModel, Field
except ImportError:
    logger.error("FastAPI không được cài đặt. Vui lòng cài đặt với lệnh: pip install fastapi uvicorn")
    sys.exit(1)
try:
    from model import LLM, event_loop_manager
    from agent_tools import tool_tracker
except ImportError:
    logger.warning("Không thể import LLM. Thử import từ thư mục server")
    try:
        from server.model import LLM, event_loop_manager
        from server.agent_tools import tool_tracker
    except ImportError:
        logger.error("Không thể import LLM. Kiểm tra cấu trúc thư mục.")

load_dotenv()

DEFAULT_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
ID_API_URL = os.getenv("ID_API_URL", "https://id-api-staging.hbc.com.vn")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "https://nghiphep.hbc.com.vn").split(",")
MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "50"))

# Semaphore để kiểm soát số lượng request đồng thời
request_semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

app = FastAPI(
    title="HBC AI API",
    description="API cho hệ thống trợ lý HBC AI",
    version="1.0.1"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# RAG Agent creation helper
def initialize_rag_agent(session_name=None, email=None, expertor=None):
    try:
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        from chat_with_RAG import RAGAgent
    except ImportError as e:
        logger.error(f"Import error từ module tương đối ({e})")
        try:
            from server.chat_with_RAG import RAGAgent
        except ImportError as e:
            logger.error(f"Error: Không thể import RAGAgent ({e})")
            return None
            
    try:
        # Luôn tạo mới RAG Agent (không kiểm tra biến toàn cục)
        rag_agent = RAGAgent(
            model_name=os.getenv("MODEL_NAME"),
            temperature=float(os.getenv("TEMPERATURE")),
            qdrant_host=os.getenv("QDRANT_HOST"),
            qdrant_port=int(os.getenv("QDRANT_PORT")),
            collection_name=os.getenv("QDRANT_COLLECTION"),
            system_prompt_file=os.getenv("SYSTEM_PROMPT_PATH"),
            provider=DEFAULT_PROVIDER,
            use_postgres_memory=os.getenv("USE_POSTGRES_MEMORY", "True").lower() == "true"
        )
        
        # Nếu có thông tin session, khởi tạo session để tải lịch sử hội thoại
        if session_name and email and expertor:
            session_id = rag_agent.llm.init_session(
                session_name=session_name,
                email=email,
                expertor=expertor
            )
            logger.info(f"Khởi tạo phiên chat trong agent mới: {session_id}")
            
    except Exception as e:
        logger.error(f"Error: Không thể khởi tạo RAGAgent: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    return rag_agent

class ChatRequest(BaseModel):
    topic: str = Form(..., description="Chủ đề của cuộc hội thoại")
    user_email: str = Form(..., description="Email người dùng")
    prompt: str = Form(..., description="Nội dung tin nhắn")
    mode: str = Form(..., description="Mode của cuộc hội thoại think hoặc normal")
    session_name: str = Form(..., description="Tên section của cuộc hội thoại")

class ChatResponse(BaseModel):
    output: str = Field(..., description="Phản hồi từ AI")
    tool_usages: List[Dict[str, Any]] = Field(..., description="Các công cụ đã sử dụng")
    topic: str = Field(..., description="Chủ đề của cuộc hội thoại")
    usage: dict = Field(..., description="Số token đã sử dụng")
    time_response: float = Field(..., description="Thời gian phản hồi")
    session_name: str = Field(..., description="Tên section của cuộc hội thoại")
    mode: str = Field(..., description="Mode của cuộc hội thoại think hoặc normal")
    
class ProviderRequest(BaseModel):
    provider: str = Field(..., description="Nhà cung cấp LLM mới (openai, gemini, palm)")

async def verify_access_token(authorization: Request):
    token = authorization.headers.get("Authorization")
    if not token:
        raise HTTPException(status_code=401, detail="Invalid Authorization header")
    
    token = token.replace("Bearer ", "")
    
    # Sử dụng httpx async
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{ID_API_URL}/v1/user/auth/google/access-token?accessToken={token}",
                headers={"Content-Type": "application/json"},
                timeout=5.0  # Thêm timeout
            )
            if str(response.json()) == "False":
                return False
            return True
        except Exception as e:
            logger.error(f"Lỗi khi xác thực token: {e}")
            raise HTTPException(status_code=500, detail=f"Lỗi xác thực: {str(e)}")

def chat_with_leave_request_agent(user_name: str, user_email: str, refresh_token: str, message: str) -> ChatResponse:
    url = "http://localhost:5680/chat"
    payload = {
        "user_name": user_name,
        "email": user_email,
        "refresh_token": refresh_token,
        "message": message
    }
    try:
        response = requests.post(url, json=payload, timeout=30)  # Thêm timeout
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi khi gọi leave request agent: {str(e)}")

# Hàm xử lý chat trong thread riêng biệt để không block worker chính
async def process_chat_request_async(topic, user_email, prompt, session_name, mode, user_name, refresh_token):
    if topic == "NGHI_PHEP":
        try:
            # Chat với leave request agent vẫn sử dụng requests đồng bộ, nhưng được chạy trong thread pool
            def call_leave_request_agent():
                response = chat_with_leave_request_agent(
                    user_name, user_email, refresh_token, message=prompt
                )["output"]
                return response
                
            response = await asyncio.to_thread(call_leave_request_agent)
            
            return {
                "output": response,
                "tool_usages": [],
                "topic": topic,
                "usage": {},
                "time_response": 0,
                "session_name": session_name,
                "mode": "normal"
            }
        except Exception as e:
            logger.error(f"Lỗi khi xử lý request NGHI_PHEP: {str(e)}")
            raise

    # Khởi tạo RAG Agent cho request này
    rag_agent = await asyncio.to_thread(
        initialize_rag_agent,
        session_name, user_email, topic
    )
    
    if rag_agent is None:
        raise Exception("Không thể khởi tạo RAG Agent")

    # Gọi RAG Agent bất đồng bộ
    time_start = time.time()
    try:
        response = await rag_agent.chat_async(prompt, mode)
        time_end = time.time()
        tool_usages = tool_tracker.get_logs()
        tool_tracker.clear_logs()
        
        return {
            "output": response["result"],
            "tool_usages": tool_usages,
            "topic": topic,
            "usage": response.get("usage", {}),
            "time_response": time_end - time_start,
            "session_name": session_name,
            "mode": mode
        }
    except Exception as e:
        logger.error(f"Lỗi trong process_chat_request_async: {str(e)}")
        raise

# Phiên bản đồng bộ của process_chat_request (tương thích ngược)
def process_chat_request(topic, user_email, prompt, session_name, mode, user_name, refresh_token):
    return asyncio.run(process_chat_request_async(
        topic, user_email, prompt, session_name, mode, user_name, refresh_token
    ))

# Endpoint chat với xử lý non-blocking
@app.post("/api/chat", response_model=ChatResponse)
async def chat(
    topic: str = Form(...),
    user_email: str = Form(...),
    prompt: str = Form(...),
    session_name: str = Form(...),
    mode: str = Form(...),
    user_name: str = Form(...),
    refresh_token: str = Form(...),
    authorization: bool = Depends(verify_access_token)
):  
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Sử dụng semaphore để kiểm soát số lượng requests đồng thời
    async with request_semaphore:
        try:
            # Sử dụng process_chat_request_async trực tiếp thay vì thông qua thread pool
            result = await process_chat_request_async(
                topic, user_email, prompt, session_name, mode, user_name, refresh_token
            )
            
            return ChatResponse(**result)
        except Exception as e:
            logger.error(f"Lỗi trong /api/chat: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Lỗi: {str(e)}")

@app.post("/api/chat/stream")
async def chat_stream(
    topic: str = Form(...),
    user_email: str = Form(...),
    prompt: str = Form(...),
    session_name: str = Form(...),
    mode: str = Form(...),
    user_name: str = Form(...),
    refresh_token: str = Form(...),
    authorization: bool = Depends(verify_access_token)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Sử dụng semaphore để kiểm soát số lượng requests đồng thời
    async with request_semaphore:
        try:
            # Khởi tạo RAG Agent cho request này
            if topic == "NGHI_PHEP":
                # Không hỗ trợ streaming cho agent nghỉ phép
                raise HTTPException(
                    status_code=400, 
                    detail="Streaming không được hỗ trợ cho chủ đề NGHI_PHEP. Vui lòng sử dụng /api/chat thay thế."
                )
            
            # Tạo hàm generator để stream phản hồi
            async def response_generator():
                rag_agent = None
                try:
                    # Ghi lại thời gian bắt đầu
                    time_start = time.time()
                    yield f"data: {json.dumps({'start': True})}\n\n"
                    
                    # Biến theo dõi các lỗi
                    has_error = False
                    error_message = ""
                    
                    # Khởi tạo RAG Agent
                    try:
                        # Chạy initialize_rag_agent trong thread pool để không block event loop
                        rag_agent = await asyncio.to_thread(
                            initialize_rag_agent,
                            session_name, user_email, topic
                        )
                        
                        if rag_agent is None:
                            raise Exception("Không thể khởi tạo RAG Agent")
                            
                        # Chuẩn bị prompt và phân tích
                        logger.info(f"Chuẩn bị xử lý prompt: {prompt[:50]}...")
                            
                        # Chuẩn bị agent
                        agent = None
                        if mode == "think":
                            if rag_agent.think_agent is None:
                                rag_agent.think_agent = rag_agent._create_think_agent()
                            agent = rag_agent.think_agent
                        else:  # Mặc định là "normal"
                            if rag_agent.normal_agent is None:
                                rag_agent.normal_agent = rag_agent._create_normal_agent()
                            agent = rag_agent.normal_agent
                            
                        # Chạy agent trực tiếp trong thread pool
                        agent_result = await asyncio.to_thread(
                            lambda: agent.invoke({"input": prompt, "chat_history": rag_agent.llm.get_history()})
                        )
                        
                        # Trích xuất kết quả từ agent
                        if isinstance(agent_result, dict) and "output" in agent_result:
                            agent_output = agent_result["output"]
                        else:
                            agent_output = str(agent_result)
                            
                        # Tạo prompt cuối cùng
                        final_prompt = f"""
Dựa trên câu hỏi của tôi:
{prompt}
và kết quả phân tích từ agent:
{agent_output}
Hãy tạo một câu trả lời cuối cùng, chi tiết, rõ ràng.
Trả lời trực tiếp vào câu hỏi.
"""
                        # Sử dụng OpenAI API trực tiếp để streaming
                        api_key = os.getenv("OPENAI_KEY_APHONG")
                        model = os.getenv("MODEL_NAME", "gpt-4o-mini")
                        
                        # Chuẩn bị tin nhắn
                        history = rag_agent.llm.get_history()
                        messages = [{"role": "system", "content": rag_agent.llm.system_prompt}]
                        
                        for msg in history:
                            if msg["role"] in ["user", "assistant", "system"]:
                                messages.append({"role": msg["role"], "content": msg["content"]})
                        
                        messages.append({"role": "user", "content": final_prompt})
                        
                        # Cấu hình payload
                        payload = {
                            "model": model,
                            "messages": messages,
                            "temperature": 0.7,
                            "max_tokens": 4000,
                            "stream": True
                        }
                        
                        headers = {
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {api_key}"
                        }
                        
                        # Sử dụng httpx thay vì aiohttp
                        async with httpx.AsyncClient(timeout=300.0) as client:
                            async with client.stream("POST", 
                                                    "https://api.openai.com/v1/chat/completions",
                                                    headers=headers, 
                                                    json=payload) as response:
                                
                                if response.status_code != 200:
                                    error_text = await response.aread()
                                    raise Exception(f"OpenAI API error: {response.status_code}, {error_text}")
                                
                                # Xử lý stream từng dòng
                                full_response = ""
                                async for line in response.aiter_lines():
                                    if line.startswith("data: ") and line != "data: [DONE]":
                                        try:
                                            data = json.loads(line[6:])  # Loại bỏ 'data: ' ở đầu
                                            if 'choices' in data and len(data['choices']) > 0:
                                                delta = data['choices'][0].get('delta', {})
                                                if 'content' in delta and delta['content']:
                                                    chunk_text = delta['content']
                                                    full_response += chunk_text
                                                    # Gửi từng chunk về client
                                                    yield f"data: {json.dumps({'content': chunk_text})}\n\n"
                                        except Exception as e:
                                            logger.error(f"Lỗi khi xử lý chunk: {e}, line: {line}")
                                
                                # Lưu tin nhắn vào lịch sử
                                rag_agent.llm.history.append({"role": "user", "content": prompt})
                                rag_agent.llm.history.append({"role": "assistant", "content": full_response})
                                
                                # Lưu vào PostgreSQL nếu cần
                                if rag_agent.llm.use_postgres_memory and rag_agent.llm.pg_memory and rag_agent.llm.pg_memory.current_session:
                                    await asyncio.to_thread(rag_agent.llm.pg_memory.add_message, "user", prompt)
                                    await asyncio.to_thread(rag_agent.llm.pg_memory.add_message, "assistant", full_response)
                    
                    except Exception as e:
                        has_error = True
                        error_message = f"Lỗi khi xử lý stream: {str(e)}"
                        logger.error(error_message)
                        import traceback
                        traceback.print_exc()
                        yield f"data: {json.dumps({'content': error_message})}\n\n"
                    
                    # Lấy thông tin về các tool đã sử dụng
                    time_end = time.time()
                    tool_usages = tool_tracker.get_logs()
                    tool_tracker.clear_logs()
                    
                    # Gửi event kết thúc với metadata
                    result = {
                        'finished': True, 
                        'tool_usages': tool_usages, 
                        'topic': topic, 
                        'time_response': time_end - time_start, 
                        'session_name': session_name, 
                        'mode': mode
                    }
                    
                    # Thêm thông tin lỗi nếu có
                    if has_error:
                        result['has_error'] = True
                        result['error_message'] = error_message
                        
                    yield f"data: {json.dumps(result)}\n\n"
                    
                except Exception as e:
                    # Gửi thông báo lỗi
                    logger.error(f"Lỗi trong chat_stream generator: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
            # Trả về streaming response với KeepAlive
            return StreamingResponse(
                response_generator(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",  # Tắt buffering cho Nginx
                    "Keep-Alive": "timeout=600"  # Giữ kết nối sống lâu hơn
                }
            )
        except Exception as e:
            logger.error(f"Lỗi trong /api/chat/stream: {str(e)}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Lỗi: {str(e)}")

@app.post("/api/chat/clear")
async def clear_chat_history(
    session_name: str = Query(..., description="Tên phiên chat"),
    email: str = Query("guest", description="Email người dùng"),
    expertor: str = Query("default", description="Tên của chatbot")
):
    """
    Endpoint để xóa lịch sử hội thoại
    """
    try:
        # Xử lý trong thread pool
        async with request_semaphore:
            # Tạo mới RAG Agent với thông tin session
            rag_agent = await asyncio.to_thread(
                initialize_rag_agent,
                session_name, email, expertor
            )
            
            if rag_agent is None:
                raise HTTPException(status_code=500, detail="Không thể khởi tạo RAG Agent")
            
            # Xóa lịch sử sử dụng phương thức bất đồng bộ
            await rag_agent.clear_memory_async()
            
            return {"status": "success", "message": "Đã xóa lịch sử hội thoại"}
    except Exception as e:
        logger.error(f"Lỗi trong /api/chat/clear: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi: {str(e)}")

@app.get("/api/health")
async def health_check():
    """
    Endpoint kiểm tra trạng thái hoạt động của API
    """
    return {
        "status": "ok", 
        "message": "API đang hoạt động bình thường",
        "concurrent_requests": MAX_CONCURRENT_REQUESTS - request_semaphore._value,
        "max_concurrent_requests": MAX_CONCURRENT_REQUESTS
    }

@app.get("/api/config")
async def get_config():
    """
    Endpoint để kiểm tra các cấu hình môi trường hiện tại
    """
    config = {
        "model_name": os.getenv("MODEL_NAME", "gpt-4o-mini"),
        "temperature": float(os.getenv("TEMPERATURE", "0.7")),
        "qdrant_host": os.getenv("QDRANT_HOST", "localhost"),
        "qdrant_port": int(os.getenv("QDRANT_PORT", "6333")),
        "qdrant_collection": os.getenv("QDRANT_COLLECTION", "HBC_P_HCNS_KNOWLEDGE_BASE"),
        "provider": os.getenv("LLM_PROVIDER", "openai"),
        "available_providers": ["openai", "gemini", "palm"],
        "server_version": "1.0.0",
        "concurrent_settings": {
            "max_concurrent_requests": MAX_CONCURRENT_REQUESTS,
            "thread_pool_workers": thread_pool._max_workers
        }
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
        # Kiểm tra provider hợp lệ
        valid_providers = ["openai", "gemini", "palm"]
        if request.provider not in valid_providers:
            raise ValueError(f"Provider không hợp lệ. Chọn một trong: {', '.join(valid_providers)}")
        
        # Cập nhật biến môi trường
        os.environ["LLM_PROVIDER"] = request.provider
        global DEFAULT_PROVIDER
        DEFAULT_PROVIDER = request.provider
        
        return {
            "status": "success", 
            "message": f"Đã chuyển đổi provider sang {request.provider}"
        }
    
    except Exception as e:
        logger.error(f"Lỗi khi đổi provider: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi khi đổi provider: {str(e)}")

@app.post("/api/chat/init")
async def init_chat_session(
    session_name: str = Query(..., description="Tên phiên chat"),
    email: str = Query("guest", description="Email người dùng"),
    expertor: str = Query("default", description="Tên của chatbot")
):
    try:
        async with request_semaphore:
            # Khởi tạo RAG Agent trong thread pool
            rag_agent = await asyncio.get_event_loop().run_in_executor(
                thread_pool,
                initialize_rag_agent,
                session_name, email, expertor
            )
            
            if rag_agent is None:
                raise HTTPException(status_code=500, detail="Không thể khởi tạo RAG Agent")
            
            logger.info(f"API: Khởi tạo phiên chat với thông tin: session_name={session_name}, email={email}, expertor={expertor}")
            
            # Session đã được khởi tạo trong initialize_rag_agent
            session_id = rag_agent.llm.get_session_id()
            
            if not session_id:
                return {
                    "status": "error", 
                    "message": "Không thể khởi tạo hoặc tìm phiên chat. Kiểm tra logs để biết thêm thông tin", 
                    "session_name": session_name
                }

            history = rag_agent.llm.get_history()
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
        logger.error(error_detail)
        raise HTTPException(status_code=500, detail=error_detail)

@app.get("/api/chat/sessions")
async def get_chat_sessions(
    user_email: str = Query(..., description="Email người dùng"),
    authorization: bool = Depends(verify_access_token)
):
    # Xử lý trường hợp email có dạng "guest?email=guest"
    if "?" in user_email:
        user_email = user_email.split("?")[0]
    
    """
    Endpoint để lấy toàn bộ phiên chat và lịch sử chat theo email
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        async with request_semaphore:
            # Tạo RAG Agent mới (không cần thông tin session vì chỉ truy vấn danh sách)
            rag_agent = await asyncio.get_event_loop().run_in_executor(
                thread_pool,
                initialize_rag_agent
            )
            
            if rag_agent is None:
                raise HTTPException(status_code=500, detail="Không thể khởi tạo RAG Agent")
            
            # Kiểm tra cấu hình PostgreSQL
            use_postgres = os.getenv("USE_POSTGRES_MEMORY", "True").lower() == "true"
            if not use_postgres:
                raise HTTPException(
                    status_code=400,
                    detail="PostgreSQL memory không được kích hoạt, không thể lấy dữ liệu phiên chat"
                )
            
            # Lấy tất cả phiên chat của người dùng - chạy trong thread pool
            sessions = await asyncio.get_event_loop().run_in_executor(
                thread_pool,
                rag_agent.llm.get_sessions_by_email,
                user_email
            )
            
            if not sessions:
                return {
                    "status": "success", 
                    "message": "Không tìm thấy phiên chat nào",
                    "email": user_email,
                    "sessions": []
                }
            
            # Chuẩn bị dữ liệu kết quả
            result_sessions = []
            
            # Lấy lịch sử cho từng session - có thể mất nhiều thời gian
            for session in sessions:
                # Lấy lịch sử chat của phiên - chạy trong thread pool
                history = await asyncio.get_event_loop().run_in_executor(
                    thread_pool,
                    rag_agent.llm.get_history_by_session_id,
                    session["session_id"]
                )
                
                result_sessions.append({
                    "session_id": session["session_id"],
                    "session_name": session["session_name"],
                    "expertor": session["expertor"],
                    "created_at": session["created_at"],
                    "updated_at": session["updated_at"],
                    "message_count": len(history),
                    "messages": history
                })
            
            return {
                "status": "success",
                "email": user_email,
                "session_count": len(result_sessions),
                "sessions": result_sessions
            }
    
    except Exception as e:
        import traceback
        error_detail = f"Lỗi: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_detail)
        raise HTTPException(status_code=500, detail=error_detail)

@app.delete("/api/chat/delete")
async def delete_chat_session(
    topic: str = Query(..., description="Chủ đề của phiên chat"),
    user_email: str = Query(..., description="Email người dùng"),
    session_name: str = Query(..., description="Tên phiên chat"),
    authorization: bool = Depends(verify_access_token)
):
    """
    Endpoint để xóa một phiên chat cụ thể
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        async with request_semaphore:
            # Tạo RAG Agent mới với thông tin session
            rag_agent = await asyncio.get_event_loop().run_in_executor(
                thread_pool,
                initialize_rag_agent,
                session_name, user_email, topic
            )
            
            if rag_agent is None:
                raise HTTPException(status_code=500, detail="Không thể khởi tạo RAG Agent")
            
            # Kiểm tra cấu hình PostgreSQL
            use_postgres = os.getenv("USE_POSTGRES_MEMORY", "True").lower() == "true"
            if not use_postgres:
                raise HTTPException(
                    status_code=400,
                    detail="PostgreSQL memory không được kích hoạt, không thể xóa phiên chat"
                )
            
            # Xóa phiên chat
            is_deleted = await asyncio.get_event_loop().run_in_executor(
                thread_pool,
                lambda: rag_agent.llm.delete_session(
                    session_name=session_name,
                    email=user_email,
                    expertor=topic
                )
            )
            
            if not is_deleted:
                return {
                    "status": "error",
                    "message": "Không thể xóa phiên chat hoặc phiên chat không tồn tại",
                    "email": user_email,
                    "session_name": session_name,
                    "topic": topic
                }
            
            return {
                "status": "success",
                "message": "Đã xóa phiên chat thành công",
                "email": user_email,
                "session_name": session_name,
                "topic": topic
            }
    
    except Exception as e:
        import traceback
        error_detail = f"Lỗi: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_detail)
        raise HTTPException(status_code=500, detail=error_detail)

@app.post("/api/chat/feedback")
async def submit_chat_feedback(
    user_email: str = Form(..., description="Email người dùng"),
    topic: str = Form(..., description="Chủ đề của phiên chat"),
    session_name: str = Form(..., description="Tên phiên chat"),
    question: str = Form(..., description="Câu hỏi người dùng"),
    initial_response: str = Form(..., description="Phản hồi ban đầu từ hệ thống"),
    suggest_response: str = Form(None, description="Phản hồi gợi ý từ người dùng"),
    authorization: bool = Depends(verify_access_token)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        # Tạo dữ liệu để lưu
        feedback_data = {
            "user_email": user_email,
            "topic": topic,
            "session_name": session_name,
            "question": question,
            "initial_response": initial_response,
            "suggest_response": suggest_response,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        # Tạo tên file dựa trên timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        file_name = f"{timestamp}.json"
        
        # Đảm bảo thư mục tồn tại
        feedback_dir = "/home/vudev/workspace/chat_hcns_server/data/QandA"
        pathlib.Path(feedback_dir).mkdir(parents=True, exist_ok=True)
        
        # Đường dẫn đầy đủ đến file
        file_path = os.path.join(feedback_dir, file_name)
        
        # Lưu dữ liệu vào file (chạy trong thread pool để không block)
        def write_feedback():
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(feedback_data, f, ensure_ascii=False, indent=2)
        
        await asyncio.get_event_loop().run_in_executor(thread_pool, write_feedback)
        
        return {
            "status": "success",
            "message": "Đã nhận và lưu phản hồi từ người dùng",
            "file_path": file_path,
            "data": feedback_data
        }
    
    except Exception as e:
        import traceback
        error_detail = f"Lỗi: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_detail)
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
            "/api/chat/sessions",
            "/api/chat/delete",
            "/api/chat/feedback",
            "/api/health",
            "/api/config",
            "/api/provider/change"
        ],
        "concurrent_settings": {
            "max_concurrent_requests": MAX_CONCURRENT_REQUESTS,
            "current_requests": MAX_CONCURRENT_REQUESTS - request_semaphore._value,
            "thread_pool_workers": thread_pool._max_workers
        }
    }

# Hàm chạy trước khi khởi động server để khởi tạo event loop
@app.on_event("startup")
async def startup_event():
    """Sự kiện khởi động server"""
    logger.info("Server started successfully")
    logger.info(f"Concurrent settings: max_requests={MAX_CONCURRENT_REQUESTS}, thread_pool={thread_pool._max_workers}")
    
    # Khởi tạo event loop global
    loop = event_loop_manager.get_loop()
    logger.info(f"Event loop initialized: {loop}")
    
    # Khởi tạo aiohttp session toàn cục
    try:
        session = await event_loop_manager.get_aiohttp_session()
        logger.info(f"Global aiohttp session initialized: {session}")
    except Exception as e:
        logger.error(f"Lỗi khi khởi tạo aiohttp session: {e}")

# Đóng thread pool và aiohttp session khi tắt server
@app.on_event("shutdown")
async def shutdown_event():
    """Sự kiện tắt server"""
    logger.info("Shutting down server...")
    
    # Đóng aiohttp session
    try:
        session = await event_loop_manager.get_aiohttp_session()
        if session and not session.closed:
            await session.close()
            logger.info("Closed aiohttp session")
    except Exception as e:
        logger.error(f"Lỗi khi đóng aiohttp session: {e}")
    
    # Đóng thread pool
    thread_pool.shutdown(wait=False)
    logger.info("Thread pool shutdown complete")
    
    # KHÔNG đóng event loop - để tránh lỗi "Event loop is closed"
    logger.info("Server shutdown complete")

# Hàm main để chạy server
if __name__ == "__main__":
    import uvicorn
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("SERVER_PORT", "8000"))
    
    # Thêm worker parameter
    workers = int(os.getenv("SERVER_WORKERS", "4"))
    
    # Khởi động uvicorn server với nhiều worker
    uvicorn.run("server:app", host=host, port=port, workers=workers) 