import os
import sys
from typing import List, Optional
from datetime import datetime
import requests

# Thêm thư mục gốc vào sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from langchain.tools import Tool
from qdrant_client import QdrantClient

try:
    from model import LLM
except ImportError:
    from server.model import LLM

class AgentTools:
    """Quản lý các công cụ cho RAG Agent"""
    
    def __init__(self, llm: LLM, qdrant_client: QdrantClient, collection_name: str):
        """
        Khởi tạo với LLM, Qdrant client và tên collection
        
        Args:
            llm: Custom LLM instance
            qdrant_client: Qdrant client
            collection_name: Tên collection trong Qdrant
        """
        self.llm = llm
        self.qdrant_client = qdrant_client
        self.collection_name = collection_name
        self._tools = [
            Tool(
                name="search_documents",
                description="Tìm kiếm thông tin trong cơ sở dữ liệu tài liệu.",
                func=self.search_documents
            ),
            Tool(
                name="list_departments",
                description="Liệt kê các phòng ban trong hệ thống.",
                func=self.list_departments
            ),
            Tool(
                name="get_current_datetime",
                description="Lấy ngày và thời gian hiện tại.",
                func=self.get_current_datetime
            )
        ]
    
    def search_documents(self, query: str, limit: int = 5, filter_dept: Optional[str] = None) -> str:
        """
        Tìm kiếm tài liệu trong cơ sở dữ liệu
        
        Args:
            query: Câu truy vấn
            limit: Số kết quả tối đa
            filter_dept: Lọc theo phòng ban (nếu có)
            
        Returns:
            Chuỗi kết quả tìm kiếm
        """
        if not self.qdrant_client:
            return "Không thể kết nối đến cơ sở dữ liệu."
        
        query_vector = self.llm.embedding(query)
        if not query_vector:
            return "Không thể tạo vector cho câu truy vấn."
        
        search_filter = {"must": [{"key": "metadata.department", "match": {"value": filter_dept}}]} if filter_dept else None
        search_results = self.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit,
            query_filter=search_filter
        )
        
        if not search_results:
            dept_msg = f" trong phòng ban '{filter_dept}'" if filter_dept else ""
            return f"Không tìm thấy thông tin cho '{query}'{dept_msg}."
        response = ""
        for i, result in enumerate(search_results):
            payload = result.payload
            response += (
                f"Kết quả #{i+1} (Độ tương đồng: {result.score:.2f}):\n"
                f"Nội dung:\n{payload.get('content', 'Không có nội dung')}\n"
                f"Metadata:\n{payload.get('metadata', {})}\n"
            )
        return response
    
    def list_departments(self, input_str: str = "") -> str:
        """Liệt kê danh sách phòng ban"""
        departments = [
            "Phòng Nhân sự", "Phòng Tài chính - Kế toán", "Phòng Công nghệ thông tin",
            "Phòng Kinh doanh", "Phòng Marketing", "Phòng Hành chính",
            "Phòng Đào tạo", "Phòng Kỹ thuật", "Ban Giám đốc"
        ]
        return "Danh sách phòng ban:\n\n" + "\n".join(f"{i+1}. {dept}" for i, dept in enumerate(departments))
    
    def get_current_datetime(self, input_str: str = "") -> str:
        """Lấy ngày và thời gian hiện tại, bỏ qua input nếu có"""
        response = requests.get(f"http://localhost:8001/tools/get_current_datetime")
        return response.json()
    
    def add_custom_tool(self, name: str, description: str, func: callable):
        """Thêm công cụ tùy chỉnh"""
        self._tools.append(Tool(name=name, description=description, func=func))
    
    def get_tools(self) -> List[Tool]:
        """Lấy danh sách công cụ"""
        return self._tools