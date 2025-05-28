from fastapi import APIRouter, Query, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient

from embedding.retrieve_qa import QARetriever, COLLECTION_NAME

# Khởi tạo router
router = APIRouter(prefix="/qa", tags=["Question & Answer"])

# Khởi tạo Qdrant client
qdrant_client = QdrantClient(host="localhost", port=6333)

# Dependency để lấy QARetriever
def get_qa_retriever():
    return QARetriever(qdrant_client, COLLECTION_NAME)

# Models cho API
class QAItem(BaseModel):
    id: str
    question: str
    answer: str
    topic: str
    tags: List[str] = Field(default_factory=list)
    file_name: Optional[str] = None
    score: Optional[float] = None
    
class SearchQuery(BaseModel):
    query: str
    limit: int = 5

class TopicQuery(BaseModel):
    topic: str
    limit: int = 100

class CollectionInfo(BaseModel):
    name: str
    vector_size: int
    distance: str
    total_points: int
    status: str

# Endpoints
@router.get("/info", response_model=CollectionInfo)
async def get_collection_info(
    retriever: QARetriever = Depends(get_qa_retriever)
):
    """Lấy thông tin về collection Q&A."""
    return retriever.get_collection_info()

@router.get("/all", response_model=List[QAItem])
async def get_all_qa(
    limit: int = Query(50, ge=1, le=1000, description="Số lượng kết quả tối đa"),
    offset: int = Query(0, ge=0, description="Vị trí bắt đầu"),
    retriever: QARetriever = Depends(get_qa_retriever)
):
    """Lấy tất cả các cặp Q&A từ collection."""
    results = retriever.get_all_qa(limit=limit, offset=offset)
    return results

@router.post("/search", response_model=List[QAItem])
async def search_qa(
    search_query: SearchQuery,
    retriever: QARetriever = Depends(get_qa_retriever)
):
    """Tìm kiếm Q&A bằng từ khóa sử dụng vector similarity."""
    results = retriever.search_by_keywords(
        keywords=search_query.query, 
        limit=search_query.limit
    )
    return results

@router.post("/search-by-topic", response_model=List[QAItem])
async def search_by_topic(
    topic_query: TopicQuery,
    retriever: QARetriever = Depends(get_qa_retriever)
):
    """Tìm kiếm Q&A theo chủ đề."""
    results = retriever.search_by_topic(
        topic=topic_query.topic, 
        limit=topic_query.limit
    )
    return results

@router.get("/{qa_id}", response_model=QAItem)
async def get_qa_by_id(
    qa_id: str,
    retriever: QARetriever = Depends(get_qa_retriever)
):
    """Lấy thông tin Q&A theo ID."""
    result = retriever.get_qa_by_id(qa_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy Q&A với ID '{qa_id}'")
    return result 