import os, sys
from dotenv import load_dotenv
import openai
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables từ file .env
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_KEY_APHONG")
QDRANT_API_KEY = os.getenv("QDRANT_KEY_HBC_HCNS")
QDRANT_HOST = "https://30293fb2-6de0-4400-b89f-80626836b5ea.us-east4-0.gcp.cloud.qdrant.io"

# Khởi tạo client cho OpenAI và Qdrant
client = openai.OpenAI(api_key=OPENAI_API_KEY)
qdrant_client = QdrantClient(host="localhost", port=6333)

# Tên collection trên Qdrant
COLLECTION_NAME = "HBC_P_HCNS_KNOWLEDGE_BASE"

# Hàm tạo embedding cho câu hỏi
def get_embedding(query):
    response = client.embeddings.create(
        model="text-embedding-3-large",
        input=query
    )
    return response.data[0].embedding

# Hàm thực hiện truy vấn tới Qdrant
def search_qdrant(query_vector, limit=5, filter=None):
    search_result = qdrant_client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        limit=limit,
        query_filter=filter
    )
    return search_result

# Hàm hiển thị kết quả
def display_results(results):
    for idx, result in enumerate(results):
        print(f"Result {idx+1}:")
        print(f"  Score: {result.score}")
        print(f"  File Name: {result.payload['file_name']}")
        print(f"  Group: {result.payload['group']}")
        print(f"  Section: {result.payload['section']}")
        print(f"  Year: {result.payload['year']}")
        print(f"  Text: {result.payload['text'][:200]}...")  # Hiển thị 200 ký tự đầu tiên
        print("-" * 50)

if __name__ == "__main__":
    # Nhập câu hỏi từ người dùng
    query = input("Nhập câu hỏi của bạn: ")
    
    # Tạo embedding cho câu hỏi
    query_vector = get_embedding(query)
    
    # Thực hiện truy vấn (có thể thêm filter nếu cần)
    # Ví dụ filter: chỉ lấy các điểm có section là "HANH CHINH"
    # filter = Filter(must=[FieldCondition(key="section", match=MatchValue(value="HANH CHINH"))])
    results = search_qdrant(query_vector, limit=5)
    
    # Hiển thị kết quả
    display_results(results)