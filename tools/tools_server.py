import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict
from qdrant_client import QdrantClient
from dotenv import load_dotenv
import json
# Load biến môi trường
load_dotenv()

app = FastAPI()

# Khởi tạo Qdrant client
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "HBC_P_HCNS_KNOWLEDGE_BASE")
qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

# Kiểm tra collection có tồn tại không
collections = qdrant_client.get_collections().collections
if COLLECTION_NAME not in [col.name for col in collections]:
    raise ValueError(f"Collection {COLLECTION_NAME} không tồn tại")

# Định nghĩa model cho request
class SearchQuery(BaseModel):
    query: str
    limit: int = 5
    filter_dept: Optional[str] = None


# Endpoint cho list_departments
@app.get("/tools/list_departments")
def list_departments():
    """
    Lấy danh sách tất cả các phòng ban từ file dữ liệu liên hệ
    
    Returns:
        Danh sách tên các phòng ban
    """
    with open("/home/vudev/workspace/chat_hcns_server/data/CONTACT_INFO.json", "r", encoding="utf-8") as f:
        contact_info = json.load(f)
    
    departments = [dept["department_name"] for dept in contact_info["departments"]]
    return {"departments": departments}

# Định nghĩa model cho request get_contact_info
class ContactInfoQuery(BaseModel):
    department: Optional[str] = None
    name: Optional[str] = None
    position: Optional[str] = None

@app.get("/tools/get_contact_info")
def get_contact_info(department: Optional[str] = None, name: Optional[str] = None, position: Optional[str] = None):
    """
    Lấy thông tin liên hệ và có thể lọc theo phòng ban, tên người, hoặc chức vụ
    
    Args:
        department: Tên phòng ban cần lọc
        name: Tên người cần lọc
        position: Chức vụ cần lọc
    
    Returns:
        Thông tin liên hệ đã được lọc theo tiêu chí
    """
    with open("/home/vudev/workspace/chat_hcns_server/data/CONTACT_INFO.json", "r", encoding="utf-8") as f:
        contact_info = json.load(f)
    
    # Trả về toàn bộ dữ liệu nếu không có tham số lọc
    if not department and not name and not position:
        return contact_info
    
    # Tạo kết quả với các thông tin cơ bản giữ nguyên
    result = {
        "title": contact_info["title"],
        "last_updated": contact_info["last_updated"],
        "hotline_hbc": contact_info["hotline_hbc"],
        "departments": []
    }
    
    # Duyệt qua các phòng ban và lọc theo điều kiện
    for dept in contact_info["departments"]:
        # Lọc theo tên phòng ban (nếu có)
        if department and department.lower() not in dept["department_name"].lower():
            continue
        
        # Tạo đối tượng phòng ban mới để thêm vào kết quả
        filtered_dept = {
            "department_name": dept["department_name"],
            "members": []
        }
        
        # Duyệt qua các thành viên trong phòng ban
        for member in dept["members"]:
            # Lọc theo tên (nếu có)
            if name and name.lower() not in (member["full_name"] or "").lower():
                continue
            
            # Lọc theo chức vụ (nếu có)
            if position and position.lower() not in (member["position"] or "").lower():
                continue
            
            # Thêm thành viên thỏa điều kiện vào danh sách
            filtered_dept["members"].append(member)
        
        # Chỉ thêm phòng ban vào kết quả nếu có ít nhất 1 thành viên
        if filtered_dept["members"]:
            result["departments"].append(filtered_dept)
    
    return result

# Endpoint cho get_current_datetime
@app.get("/tools/get_current_datetime")
def get_current_datetime():
    WEEKDAY_NAMES = {
                        0: "Thứ Hai",
                        1: "Thứ Ba",
                        2: "Thứ Tư",
                        3: "Thứ Năm",
                        4: "Thứ Sáu",
                        5: "Thứ Bảy",
                        6: "Chủ Nhật"
                    }
    current = datetime.now()
    weekday_number = current.weekday() 
    weekday_name = WEEKDAY_NAMES[weekday_number] 
    return f"Hôm nay là {weekday_name}, ngày {current.strftime('%d/%m/%Y')} lúc {current.strftime('%H:%M:%S')}"

@app.get("/tools")
def get_tools():
    return {"tools": [
        {"name": "list_departments", "description": "Liệt kê danh sách các phòng ban", "params": []},
        {"name": "get_contact_info", "description": "Lấy thông tin liên hệ, có thể lọc theo phòng ban, tên người hoặc chức vụ", 
         "params": [
             {"name": "department", "type": "string", "required": False, "description": "Tên phòng ban cần lọc"},
             {"name": "name", "type": "string", "required": False, "description": "Tên người cần lọc"},
             {"name": "position", "type": "string", "required": False, "description": "Chức vụ cần lọc"}
         ]
        },
        {"name": "get_current_datetime", "description": "Lấy thông tin ngày giờ hiện tại", "params": []}
    ]}

@app.get("/")
def root():
    return {"message": "Tools server is running"}

# Chạy server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)