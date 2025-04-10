import os
import sys
from typing import List, Optional
from datetime import datetime
import requests
import json

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
                name="get_contact_info",
                description="Sử dụng công cụ này để tra cứu thông tin liên lạc từ danh bạ nội bộ của công ty (cập nhật ngày 24/10/2024). Bạn có thể lọc thông tin theo một hoặc nhiều tiêu chí sau:\n\n- department: Tên phòng ban (ví dụ: 'Ban Lãnh đạo', 'Phòng Mua Hàng', 'Phòng Kinh Doanh Tiếp Thị', 'Phòng Hành Chính Nhân Sự', 'Phòng Công Nghệ Thông Tin', 'Phòng Tài Chính Kế Toán')\n- name: Tên nhân viên (có thể là một phần của tên đầy đủ)\n- position: Chức vụ (ví dụ: 'Giám đốc', 'Phó Giám đốc', 'Nhân viên')\n\nKết quả trả về bao gồm danh sách nhân viên phù hợp với tiêu chí tìm kiếm, mỗi bản ghi chứa thông tin: tên đầy đủ, chức vụ, email, số nội bộ, số điện thoại công ty và số điện thoại cá nhân (nếu có). Nếu không cung cấp tham số nào, công cụ sẽ trả về toàn bộ danh bạ.",
                func=self.get_contact_info
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
        """
        Liệt kê danh sách phòng ban từ API
        
        Args:
            input_str: Tham số đầu vào (không sử dụng)
            
        Returns:
            Chuỗi danh sách phòng ban định dạng đẹp
        """
        try:
            response = requests.get(f"http://localhost:8001/tools/list_departments")
            if response.status_code != 200:
                return f"Lỗi khi lấy danh sách phòng ban: {response.text}"
            
            data = response.json()
            departments = data.get("departments", [])
            
            if not departments:
                return "Không có phòng ban nào được tìm thấy."
            
            # Định dạng kết quả để dễ đọc
            result = "Danh sách phòng ban:\n\n"
            for i, dept in enumerate(departments):
                result += f"{i+1}. {dept}\n"
                
            return result
            
        except Exception as e:
            return f"Lỗi khi xử lý yêu cầu: {str(e)}"
    
    def get_current_datetime(self, input_str: str = "") -> str:
        """Lấy ngày và thời gian hiện tại, bỏ qua input nếu có"""
        response = requests.get(f"http://localhost:8001/tools/get_current_datetime")
        return response.json()
    
    def get_contact_info(self, input_str: str = "") -> str:
        """
        Lấy thông tin liên lạc nội bộ của công ty, có thể lọc theo phòng ban, tên hoặc chức vụ
        
        Args:
            input_str: Chuỗi JSON chứa các tham số lọc (department, name, position)
            
        Returns:
            Thông tin liên lạc đã được lọc
        """
        try:
            # Phân tích tham số đầu vào (nếu có)
            params = {}
            if input_str and input_str.strip():
                try:
                    # Thử parse chuỗi đầu vào như JSON
                    query_params = json.loads(input_str)
                    if isinstance(query_params, dict):
                        if "department" in query_params and query_params["department"]:
                            params["department"] = query_params["department"]
                        if "name" in query_params and query_params["name"]:
                            params["name"] = query_params["name"]
                        if "position" in query_params and query_params["position"]:
                            params["position"] = query_params["position"]
                except json.JSONDecodeError:
                    # Nếu không phải JSON, thử xử lý như văn bản thông thường
                    # Đây là xử lý dự phòng khi không có cấu trúc JSON
                    text_input = input_str.lower()
                    if "giám đốc" in text_input or "trưởng phòng" in text_input or "phó giám đốc" in text_input:
                        params["position"] = "Giám đốc" if "giám đốc" in text_input else "Phó Giám đốc"
                    
                    # Các phòng ban phổ biến
                    departments = ["Ban Lãnh đạo", "Phòng Mua Hàng", "Phòng Kinh Doanh Tiếp Thị", 
                                 "Phòng Hành Chính Nhân Sự", "Phòng Công Nghệ Thông Tin", "Phòng Tài Chính Kế Toán"]
                    for dept in departments:
                        if dept.lower() in text_input or dept.lower().replace(" ", "") in text_input.replace(" ", ""):
                            params["department"] = dept
                            break
            
            # Gửi yêu cầu tới API với các tham số tìm kiếm
            response = requests.get(f"http://localhost:8001/tools/get_contact_info", params=params)
            if response.status_code != 200:
                return f"Lỗi khi lấy thông tin liên lạc: {response.text}"
            
            data = response.json()
            
            # Kiểm tra nếu không có kết quả
            if not data.get("departments") or len(data.get("departments", [])) == 0:
                return "Không tìm thấy thông tin liên lạc phù hợp với tiêu chí tìm kiếm."
            
            # Định dạng kết quả để dễ đọc
            return data
            
        except Exception as e:
            return f"Lỗi khi xử lý yêu cầu: {str(e)}"
    
    def add_custom_tool(self, name: str, description: str, func: callable):
        """Thêm công cụ tùy chỉnh"""
        self._tools.append(Tool(name=name, description=description, func=func))
    
    def get_tools(self) -> List[Tool]:
        """Lấy danh sách công cụ"""
        return self._tools