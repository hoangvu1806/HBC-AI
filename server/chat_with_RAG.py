import os
import sys
import asyncio
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from qdrant_client import QdrantClient

# Thêm thư mục gốc vào sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from model import LLM
from agent_tools import AgentTools
from agent_creator import create_normal_agent, create_think_agent

# Load biến môi trường
load_dotenv()

class RAGAgent:
    """Agent tích hợp Retrieval Augmented Generation (RAG) với LangChain và Qdrant"""

    def __init__(self,
                 model_name: str = "gpt-4o-mini",
                 temperature: float = 0.7,
                 qdrant_host: str = "localhost",
                 qdrant_port: int = 6333,
                 collection_name: str = "HBC_P_HCNS_KNOWLEDGE_BASE",
                 system_prompt: Optional[str] = None,
                 system_prompt_file: Optional[str] = None,
                 provider: str = "openai",
                 use_postgres_memory: bool = True):
        """
        Khởi tạo RAG Agent

        Args:
            model_name: Tên mô hình LLM
            temperature: Nhiệt độ từ 0-1
            qdrant_host: Host của Qdrant
            qdrant_port: Port của Qdrant
            collection_name: Tên collection trong Qdrant
            system_prompt: System prompt tùy chỉnh
            system_prompt_file: File chứa system prompt
            provider: Nhà cung cấp LLM (openai, gemini, palm)
            use_postgres_memory: Sử dụng PostgreSQL để lưu trữ bộ nhớ chat
        """
        print(f"Khởi tạo RAG Agent với model {model_name}")

        # Khởi tạo custom LLM
        self.llm = LLM(
            model_name=model_name,
            temperature=temperature,
            system_prompt=system_prompt,
            system_prompt_file=system_prompt_file,
            provider=provider,
            use_postgres_memory=use_postgres_memory
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

    def chat(self, message: str, mode: str = "normal") -> Dict[str, Any]:
        """
        Gửi tin nhắn đến agent và nhận phản hồi, chọn chế độ 'think' hoặc 'normal'

        Args:
            message: Tin nhắn người dùng
            mode: Chế độ agent ('think' hoặc 'normal')

        Returns:
            Dict chứa kết quả và metadata
        """
        # Chọn agent dựa trên mode
        if mode == "think":
            if self.think_agent is None:
                self.think_agent = self._create_think_agent()
            agent = self.think_agent
        else:  # Mặc định là "normal"
            if self.normal_agent is None:
                self.normal_agent = self._create_normal_agent()
            agent = self.normal_agent

        # Gọi agent với input và lịch sử hội thoại
        response = agent.invoke({"input": message, "chat_history": self.llm.get_history()})
        agent_result = response["output"] if isinstance(response, dict) and "output" in response else str(response)
        
        # Đưa kết quả từ agent qua LLM để tạo câu trả lời cuối cùng
        final_prompt = f"""
Dựa trên câu hỏi của tôi:
{message}
và kết quả phân tích từ agent:
{agent_result}
Hãy tạo một câu trả lời cuối cùng, chi tiết, rõ ràng.
Trả lời trực tiếp vào câu hỏi.
"""
        final_response = self.llm.chat(
            prompt=final_prompt,
            history=self.llm.get_history(),
            system_prompt=self.llm.system_prompt
        )
        result = final_response["content"]
        
        # Cập nhật lịch sử hội thoại
        self.llm.history.append({"role": "user", "content": message})
        self.llm.history.append({"role": "assistant", "content": result})

        output = {
            "result": result,
            "tool_usages": self.tool_usages,
            "success": True
        }
        self.tool_usages = []
        return output

    async def stream_chat(self, message: str, mode: str = "normal"):
        """
        Stream phản hồi từ agent, chọn chế độ 'think' hoặc 'normal'

        Args:
            message: Tin nhắn người dùng
            mode: Chế độ agent ('think' hoặc 'normal')

        Yields:
            Từng chunk của phản hồi
        """
        response = self.chat(message, mode=mode)
        result = response["result"]
        for i in range(0, len(result), 3):
            yield result[i:i+3]
            await asyncio.sleep(0.01)

    def clear_memory(self):
        """Xóa lịch sử hội thoại"""
        self.llm.clear_history()
        self.tool_usages = []

if __name__ == "__main__":
    agent = RAGAgent(
        model_name=os.getenv("MODEL_NAME", "gpt-4o-mini"),
        temperature=float(os.getenv("TEMPERATURE", "0.7")),
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