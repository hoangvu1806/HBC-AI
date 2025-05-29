import os
import sys
from typing import List, Optional
from datetime import datetime
import requests
import json
from functools import wraps

# Thêm thư mục gốc vào sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from langchain.tools import Tool
from langchain_community.utilities.serpapi import SerpAPIWrapper
from qdrant_client import QdrantClient

try:
    from model import LLM
except ImportError:
    from server.model import LLM

class ToolTracker:
    def __init__(self):
        self.logs = []
    
    def log_tool_usage(self, tool_name: str):
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = datetime.now()
                input_value = args[1] if len(args) > 1 else kwargs.get('query', '')
                result = func(*args, **kwargs)
                response_time = (datetime.now() - start_time).total_seconds()
                # print(f"Tool: '{tool_name}' | Input: '{input_value}' | Thời gian: {response_time:.2f}s | Kết quả: {result[:100]}...")
                self.logs.append({
                    "tool_name": tool_name,
                    "input_value": input_value,
                    "response_time": response_time,
                    # "result": result
                })
                return result
            return wrapper
        return decorator
    
    def get_logs(self):
        return self.logs
    
    def clear_logs(self):
        self.logs = []

tool_tracker = ToolTracker()

class AgentTools:
    def __init__(self, llm: LLM, qdrant_client: QdrantClient, collection_name: str):
        self.llm = llm
        self.qdrant_client = qdrant_client
        self.collection_name = collection_name
        self.collection_qa_name = "HBC_CHATBOT_QA"
        self._tools = [
            Tool(
                name="search_documents",
                description="Tìm kiếm thông tin trong cơ sở dữ liệu tài liệu. Tool này thường được sử dụng để tìm thông tin (Trừ những câu hỏi giao tiếp thông thường). Nếu câu hỏi của bạn không liên quan đến nội dung nội bộ của công ty, hãy sử dụng công cụ này để tìm kiếm thông tin trên internet. Đầu vào là câu truy vấn chung chung, không quá chi tiết",
                func=self.search_documents,
            ),
            Tool(
                name="search_qa",
                description="Tìm kiếm thông tin trong cơ sở dữ liệu câu hỏi và câu trả lời Q&A. Đầu vào là câu truy vấn chung chung, không quá chi tiết. Tool này thường được dùng sau khi sử dụng tool search_documents không có kết quả hoặc không đủ thông tin.",
                func=self.search_qa
            ),
            Tool(
                name="get_contact_info",
                description="Sử dụng công cụ này để trả lời cho câu hỏi '...là ai?' và tra cứu thông tin liên lạc hoặc tên người hoặc chức vụ từ danh bạ nội bộ của công ty. Bạn có thể lọc thông tin theo một hoặc nhiều tiêu chí sau:\n\n- department: Tên phòng ban (ví dụ: 'Ban Lãnh đạo', 'Phòng Mua Hàng', 'Phòng Kinh Doanh Tiếp Thị', 'Phòng Hành Chính Nhân Sự', 'Phòng Công Nghệ Thông Tin', 'Phòng Tài Chính Kế Toán')\n- name: Tên nhân viên (có thể là một phần của tên đầy đủ)\n- position: Chức vụ (ví dụ: 'Giám đốc', 'Phó Giám đốc', 'Nhân viên')\n\nKết quả trả về bao gồm danh sách nhân viên phù hợp với tiêu chí tìm kiếm, mỗi bản ghi chứa thông tin: tên đầy đủ, chức vụ, email, số nội bộ, số điện thoại công ty và số điện thoại cá nhân (nếu có). Nếu không cung cấp tham số nào, công cụ sẽ trả về toàn bộ danh bạ.",
                func=self.get_contact_info
            ),
            Tool(
                name="get_current_datetime",
                description="Lấy ngày và thời gian hiện tại.",
                func=self.get_current_datetime
            ),
            Tool(
                name="get_company_info",
                description="Lấy thông tin cơ bản của công ty liên quan đến giới thiệu, lịch sử, sứ mệnh, sản phẩm,...",
                func=self.get_company_info
            ),
            Tool(
                name="Google Search",
                func=self.web_search,
                description="Sử dụng tool này để tìm kiếm thông tin trên internet, đầu vào là nội dung cần tìm kiếm. Tool này thường được sử dụng khi sử dụng tool search_qa và search_documents không có kết quả hoặc không đủ thông tin."
            )
        ]
    
    @tool_tracker.log_tool_usage("search_documents")
    def search_documents(self, query: str, limit: int = 3, filter_dept: Optional[str] = None) -> str:
        if not self.qdrant_client:
            return "Không thể kết nối đến cơ sở dữ liệu."
        
        query_vector = self.llm.embedding(query)
        if not query_vector:
            return "Không thể tạo vector cho câu truy vấn."
        
        search_filter = {"must": [{"key": "metadata.department", "match": {"value": filter_dept}}]} if filter_dept else None
        search_results = self.qdrant_client.search(
            collection_name= self.collection_name,
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
    
    @tool_tracker.log_tool_usage("search_qa")
    def search_qa(self, query: str, limit: int = 3) -> str:
        if not self.qdrant_client:
            return "Không thể kết nối đến cơ sở dữ liệu."
        
        query_vector = self.llm.embedding(query)
        if not query_vector:
            return "Không thể tạo vector cho câu truy vấn."
        
        search_results = self.qdrant_client.search(
            collection_name=self.collection_qa_name,
            query_vector=query_vector,
            limit=limit,
        )
        if not search_results:
            return f"Không tìm thấy thông tin cho '{query}'."
        response = ""
        for i, result in enumerate(search_results):
            payload = result.payload["metadata"]
            response += (
                f"Kết quả #{i+1} (Độ tương đồng: {result.score:.2f}):\n"
                f"{payload.get('suggest_response')}\n"
            )
        return response
    
    @tool_tracker.log_tool_usage("web_search")
    def web_search(self, query: str) -> str:
        """Tìm kiếm trên web"""
        search = SerpAPIWrapper(serpapi_api_key="dcdc2a63b220455572693f5b33eee090ecf3a070076fff85e257a9a64fc2d9b7")
        return search.run(query)
    
    @tool_tracker.log_tool_usage("get_current_datetime")
    def get_current_datetime(self, input_str: str = "") -> str:
        """Lấy ngày và thời gian hiện tại, bỏ qua input nếu có"""
        response = requests.get(f"http://localhost:8001/tools/get_current_datetime")
        return response.json()
    
    @tool_tracker.log_tool_usage("get_contact_info")
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
    
    @tool_tracker.log_tool_usage("get_company_info")
    def get_company_info(self, input_str: str = "") -> str:
        """
        Lấy thông tin cơ bản của công ty như giới thiệu, lịch sử, sứ mệnh, sản phẩm,..."""
        response = requests.get(f"http://localhost:8001/tools/get_company_info", params={"query": input_str})
        return response.json()
    
    def add_custom_tool(self, name: str, description: str, func: callable):
        """Thêm công cụ tùy chỉnh"""
        self._tools.append(Tool(name=name, description=description, func=func))
    
    def get_tools(self) -> List[Tool]:
        """Lấy danh sách công cụ"""
        return self._tools
    