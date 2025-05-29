import os
import sys
import logging
import time
import asyncio
from typing import Dict, Any, List, Optional, Tuple, AsyncGenerator
# Đã loại bỏ import lru_cache
from dotenv import load_dotenv
from qdrant_client import QdrantClient
import concurrent.futures

# Thêm thư mục gốc vào sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from model import LLM, AsyncToSyncGenerator, event_loop_manager
from agent_tools import AgentTools, tool_tracker
from agent_creator import create_normal_agent, create_think_agent

# Load biến môi trường
load_dotenv()

# Thiết lập logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Thread pool cho các tác vụ nặng không hỗ trợ async
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=10)

class RAGAgent:
    """Agent tích hợp Retrieval Augmented Generation (RAG) với LangChain và Qdrant"""

    def __init__(self,
                 model_name: str = "gpt-4o-mini",
                 temperature: float = 0.7,
                 qdrant_host: str = "localhost",
                 qdrant_port: int = 6333,
                 collection_name: str = "HBC_P_HCNS_KNOWLEDGE_BASE",
                 system_prompt_file: Optional[str] = None,
                 provider: str = "openai",
                 use_postgres_memory: bool = True):
        print(f"Khởi tạo RAG Agent với model {model_name}")

        # Khởi tạo custom LLM
        self.llm = LLM(
            model_name=model_name,
            temperature=temperature,
            provider=provider,
            system_prompt_file=system_prompt_file,
            use_postgres_memory=use_postgres_memory,
        )

        # Khởi tạo Qdrant client
        self.qdrant_client = QdrantClient(host=qdrant_host, port=qdrant_port)
        self.collection_name = collection_name

        # Kiểm tra collection có tồn tại không
        collections = self.qdrant_client.get_collections().collections
        if collection_name not in [col.name for col in collections]:
            raise ValueError(f"Collection {collection_name} không tồn tại")

        # Lấy kích thước vector từ collection
        collection_info = self.qdrant_client.get_collection(collection_name=collection_name)
        self.vector_size = collection_info.config.params.vectors.size

        # Khởi tạo AgentTools
        self.tools = AgentTools(llm=self.llm, qdrant_client=self.qdrant_client, collection_name=self.collection_name)
        self.tool_usages = []  # Lịch sử tool usage

        # Khởi tạo cả hai agent
        self.normal_agent = self._create_normal_agent()
        self.think_agent = self._create_think_agent()
        
    def _create_normal_agent(self):
        """Tạo LangChain agent chế độ 'normal'"""
        tools = self.tools.get_tools()
        return create_normal_agent(llm=self.llm, tools=tools, system_prompt=self.llm.system_prompt)

    def _create_think_agent(self):
        """Tạo LangChain agent chế độ 'think'"""
        tools = self.tools.get_tools()
        return create_think_agent(llm=self.llm, tools=tools, system_prompt=self.llm.system_prompt)

    async def _get_embedding_async(self, text: str) -> List[float]:
        """
        Tạo embedding vector cho text (bất đồng bộ)
        
        Args:
            text: Văn bản cần tạo embedding
            
        Returns:
            List[float]: Vector embedding
        """
        return await self.llm.embedding_async(text)
    
    def _get_embedding(self, text: str) -> List[float]:
        """
        Tạo embedding vector cho text (đồng bộ)
        
        Args:
            text: Văn bản cần tạo embedding
            
        Returns:
            List[float]: Vector embedding
        """
        return self.llm.embedding(text)
    
    def _get_context_from_cache(self, query: str) -> Optional[str]:
        """
        Phương thức này đã bị loại bỏ cơ chế cache
        Luôn trả về None để buộc truy xuất dữ liệu mới
        
        Args:
            query: Câu hỏi
            
        Returns:
            None: Luôn trả về None để buộc truy xuất dữ liệu mới
        """
        return None
    
    def _store_context_in_cache(self, query: str, context: str):
        """
        Phương thức này đã bị loại bỏ cơ chế cache
        Không thực hiện gì cả
        
        Args:
            query: Câu hỏi
            context: Context tìm được
        """
        # Không thực hiện gì cả vì đã loại bỏ cache
        pass
    
    async def retrieve_documents_async(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Truy xuất tài liệu từ Qdrant dựa trên query (bất đồng bộ)
        
        Args:
            query: Câu hỏi
            top_k: Số lượng tài liệu trả về
            
        Returns:
            List[Dict[str, Any]]: Danh sách tài liệu liên quan
        """
        if not self.qdrant_client:
            logger.error("Qdrant client chưa được khởi tạo")
            return []
            
        try:
            start_time = time.time()
            
            # Tạo embedding bất đồng bộ
            query_vector = await self._get_embedding_async(query)
            
            # Tìm kiếm tài liệu liên quan
            # Qdrant client không hỗ trợ async nên chạy trong thread pool
            def _search_qdrant():
                return self.qdrant_client.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    limit=top_k
                )
            
            results = await asyncio.to_thread(_search_qdrant)
            
            # Xây dựng danh sách tài liệu
            documents = []
            for result in results:
                if hasattr(result, "payload") and result.payload:
                    document = {
                        "content": result.payload.get("text", ""),
                        "source": result.payload.get("source", "unknown"),
                        "score": result.score
                    }
                    documents.append(document)
            
            logger.info(f"Tìm thấy {len(documents)} tài liệu liên quan. Thời gian: {time.time() - start_time:.2f}s")
            return documents
        except Exception as e:
            logger.error(f"Lỗi khi truy xuất tài liệu: {e}")
            return []
    
    def retrieve_documents(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Truy xuất tài liệu từ Qdrant dựa trên query (đồng bộ)
        
        Args:
            query: Câu hỏi
            top_k: Số lượng tài liệu trả về
            
        Returns:
            List[Dict[str, Any]]: Danh sách tài liệu liên quan
        """
        return asyncio.run(self.retrieve_documents_async(query, top_k))
    
    def format_context(self, documents: List[Dict[str, Any]]) -> str:
        if not documents:
            return ""
            
        context_parts = []
        for i, doc in enumerate(documents):
            source = doc.get("source", "unknown")
            content = doc.get("content", "")
            
            # Rút gọn nguồn nếu quá dài
            if len(source) > 100:
                source = source[:97] + "..."
                
            # Thêm thông tin nguồn và nội dung
            context_parts.append(f"Document {i+1} (Source: {source}):\n{content}\n")
        return "\n".join(context_parts)
    
    async def _run_agent_async(self, agent, prompt: str) -> str:
        """
        Chạy agent với prompt đầu vào (bất đồng bộ)
        
        Args:
            agent: Agent cần chạy
            prompt: Nội dung prompt
            
        Returns:
            str: Kết quả từ agent
        """
        try:
            # Đảm bảo chúng ta đang sử dụng event loop hợp lệ
            loop = event_loop_manager.get_loop()
            
            # Kiểm tra xem agent có hỗ trợ invoke_async không
            if hasattr(agent, 'invoke_async') and callable(getattr(agent, 'invoke_async')):
                # Nếu có, gọi trực tiếp
                try:
                    response = await agent.invoke_async({"input": prompt, "chat_history": self.llm.get_history()})
                except Exception as e:
                    logger.error(f"Lỗi khi gọi agent.invoke_async: {e}")
                    # Fallback: thử gọi phương thức đồng bộ trong thread
                    response = await asyncio.to_thread(
                        lambda: agent.invoke({"input": prompt, "chat_history": self.llm.get_history()})
                    )
            else:
                # Nếu không, chạy trong thread pool
                def _run_agent():
                    try:
                        return agent.invoke({"input": prompt, "chat_history": self.llm.get_history()})
                    except Exception as e:
                        logger.error(f"Lỗi trong _run_agent: {e}")
                        # Trả về một dict đơn giản để không gây ra lỗi
                        return {"output": f"Đã xảy ra lỗi khi chạy agent: {str(e)}"}
                
                response = await asyncio.to_thread(_run_agent)
                
            # Trích xuất kết quả
            if isinstance(response, dict) and "output" in response:
                agent_result = response["output"]
            elif hasattr(response, "content"):
                # Có thể là LangChain message object
                agent_result = response.content
            else:
                # Fallback, chuyển đổi sang string
                agent_result = str(response)
                
            return agent_result
        except Exception as e:
            logger.error(f"Lỗi khi chạy agent: {e}")
            import traceback
            traceback.print_exc()
            # Trả về thông báo lỗi để tiếp tục xử lý
            return f"Đã xảy ra lỗi khi chạy agent: {str(e)}. Tuy nhiên, tôi sẽ tiếp tục phân tích dựa trên thông tin hiện có."
    
    async def chat_async(self, prompt: str, mode: str = "normal") -> Dict[str, Any]:
        """
        Phiên bản bất đồng bộ của phương thức chat
        
        Args:
            prompt: Tin nhắn người dùng
            mode: Chế độ agent ('think' hoặc 'normal')
            
        Returns:
            Dict[str, Any]: Kết quả và metadata
        """
        try:
            tool_tracker.clear_logs()
            # Chọn agent dựa trên mode
            if mode == "think":
                if self.think_agent is None:
                    self.think_agent = self._create_think_agent()
                agent = self.think_agent
            else:  # Mặc định là "normal"
                if self.normal_agent is None:
                    self.normal_agent = self._create_normal_agent()
                agent = self.normal_agent

            # Gọi agent với input và lịch sử hội thoại (bất đồng bộ)
            agent_result = await self._run_agent_async(agent, prompt)
            
            # Đưa kết quả từ agent qua LLM để tạo câu trả lời cuối cùng
            final_prompt = f"""
    Dựa trên câu hỏi của tôi:
    {prompt}
    và kết quả phân tích từ agent:
    {agent_result}
    Hãy tạo một câu trả lời cuối cùng, chi tiết, rõ ràng.
    Trả lời trực tiếp vào câu hỏi.
    """
            final_response = await self.llm.chat_async(
                prompt=final_prompt,
                history=self.llm.get_history(),
                system_prompt=self.llm.system_prompt,
                user_messages=prompt
            )
            result = final_response["content"]

            input_tokens = self.llm.get_token_count(final_prompt)
            output_tokens = self.llm.get_token_count(result)

            self.llm.history.append({"role": "user", "content": prompt})
            self.llm.history.append({"role": "assistant", "content": result})
            
            output = {
                "result": result,
                "tool_usages": self.tool_usages,
                "success": True,
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens
                }
            }
            self.tool_usages = []
            return output
        except Exception as e:
            logger.error(f"Lỗi khi xử lý câu hỏi: {e}")
            import traceback
            traceback.print_exc()
            return {
                "result": f"Xin lỗi, đã xảy ra lỗi khi xử lý câu hỏi của bạn: {str(e)}",
                "usage": {}
            }
    
    def chat(self, prompt: str, mode: str = "normal") -> Dict[str, Any]:
        """
        Phiên bản đồng bộ của phương thức chat, gọi chat_async bên trong
        
        Args:
            prompt: Tin nhắn người dùng
            mode: Chế độ agent ('think' hoặc 'normal')
            
        Returns:
            Dict[str, Any]: Kết quả và metadata
        """
        return asyncio.run(self.chat_async(prompt, mode))
    
    async def chat_stream_async(self, message: str, mode: str = "normal") -> AsyncGenerator[str, None]:
        """
        Phiên bản bất đồng bộ của chat_stream
        
        Args:
            message: Tin nhắn người dùng
            mode: Chế độ agent ('think' hoặc 'normal')
            
        Returns:
            AsyncGenerator: Generator trả về từng chunk của phản hồi
        """
        # Đảm bảo chúng ta đang sử dụng event loop hợp lệ
        loop = event_loop_manager.get_loop()
        
        if mode == "think":
            if self.think_agent is None:
                self.think_agent = self._create_think_agent()
            agent = self.think_agent
        else:  # Mặc định là "normal"
            if self.normal_agent is None:
                self.normal_agent = self._create_normal_agent()
            agent = self.normal_agent

        # Biến lưu kết quả để fallback
        agent_result = None
        
        try:
            # Gọi agent với input và lịch sử hội thoại (bất đồng bộ)
            start_time = time.time()
            agent_result = await self._run_agent_async(agent, message)
            
            # Đưa kết quả từ agent qua LLM để tạo câu trả lời cuối cùng
            final_prompt = f"""
Dựa trên câu hỏi của tôi:
{message}
và kết quả phân tích từ agent:
{agent_result}
Hãy tạo một câu trả lời cuối cùng, chi tiết, rõ ràng.
Trả lời trực tiếp vào câu hỏi.
"""
            # Trả về generator từ stream_chat_async
            try:
                stream_gen = self.llm.stream_chat_async(
                    prompt=final_prompt,
                    history=self.llm.get_history(),
                    system_prompt=self.llm.system_prompt,
                    user_messages=message
                )
                
                # Sử dụng try/except trong generator để bắt lỗi từng phần
                async for chunk in stream_gen:
                    yield chunk
                
            except Exception as stream_error:
                logger.error(f"Lỗi khi streaming từ LLM: {stream_error}")
                import traceback
                traceback.print_exc()
                
                # Fallback: nếu streaming thất bại, sử dụng chat_async
                try:
                    logger.info("Thử fallback sang chat_async")
                    result = await self.llm.chat_async(
                        prompt=final_prompt,
                        history=self.llm.get_history(),
                        system_prompt=self.llm.system_prompt,
                        user_messages=message
                    )
                    # Trả về toàn bộ kết quả trong một lần
                    yield result["content"]
                except Exception as fallback_error:
                    # Nếu cả hai phương thức đều thất bại, trả về thông báo lỗi
                    error_msg = f"Lỗi khi tạo phản hồi: {fallback_error}"
                    logger.error(error_msg)
                    yield error_msg
        except Exception as e:
            logger.error(f"Lỗi trong chat_stream_async: {e}")
            import traceback
            traceback.print_exc()
            
            # Nếu đã có agent_result, thử gửi phản hồi đơn giản
            if agent_result:
                try:
                    yield f"Xin lỗi, đã xảy ra lỗi khi tạo phản hồi chi tiết. Dưới đây là phân tích cơ bản:\n\n{agent_result}"
                    return
                except:
                    pass
                
            # Trả về thông báo lỗi mặc định
            yield f"Xin lỗi, đã xảy ra lỗi: {str(e)}. Vui lòng thử lại sau."

    def chat_stream(self, message: str, mode: str = "normal"):
        """
        Gửi tin nhắn đến agent và nhận phản hồi theo dạng stream (đồng bộ)
        
        Args:
            message: Tin nhắn người dùng
            mode: Chế độ agent ('think' hoặc 'normal')
            
        Returns:
            Generator trả về từng chunk của phản hồi
        """
        # Đảm bảo sử dụng event loop hợp lệ
        loop = event_loop_manager.get_loop()
        
        # Chuyển đổi AsyncGenerator thành Generator đồng bộ
        return AsyncToSyncGenerator(self.chat_stream_async(message, mode))

    async def clear_memory_async(self):
        """Xóa lịch sử hội thoại bất đồng bộ"""
        self.tool_usages = []
        
        # Gọi clear_history của LLM
        # LLM.clear_history là phương thức đồng bộ, nhưng có thể mất thời gian với PostgreSQL
        await asyncio.to_thread(self.llm.clear_history)

    def clear_memory(self):
        """Xóa lịch sử hội thoại đồng bộ"""
        asyncio.run(self.clear_memory_async())

if __name__ == "__main__":
    agent = RAGAgent(
        model_name=os.getenv("MODEL_NAME", "gpt-4o-mini"),
        temperature=float(os.getenv("TEMPERATURE", "0.4")),
        qdrant_host=os.getenv("QDRANT_HOST", "localhost"),
        qdrant_port=int(os.getenv("QDRANT_PORT", "6333")),
        collection_name=os.getenv("QDRANT_COLLECTION", "HBC_P_HCNS_KNOWLEDGE_BASE"),
        provider=os.getenv("LLM_PROVIDER", "openai"),
        use_postgres_memory=os.getenv("USE_POSTGRES_MEMORY", "True").lower() == "true"
    )

    messages = [
        "Hiện tại tôi đang có 20 ngày nghỉ phép. Hãy cho tôi một kế hoạch nghỉ phép tối ưu nhất",
    ]

    for msg in messages:
        # Chế độ "normal"
        print(f"\nUser (Normal mode): {msg}")
        response = agent.chat(msg, mode="normal")
        print(f"Normal Agent: {response['result']}")

        # Chế độ "think"
        print(f"\nUser (Think mode): {msg}")
        response = agent.chat(msg, mode="think")
        print(f"Think Agent: {response['result']}")