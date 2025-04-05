import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict
from qdrant_client import QdrantClient
from dotenv import load_dotenv

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
    departments = [
        "Phòng Nhân sự", "Phòng Tài chính - Kế toán", "Phòng Công nghệ thông tin",
        "Phòng Kinh doanh", "Phòng Marketing", "Phòng Hành chính",
        "Phòng Đào tạo", "Phòng Kỹ thuật", "Ban Giám đốc"
    ]
    return {"departments": departments}

# Từ điển ánh xạ số thứ trong tuần sang tên tiếng Việt


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
    return {"tools": ["list_departments", "get_current_datetime"]}

@app.get("/")
def root():
    return {"message": "Tools server is running"}

# Chạy server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)