import os
import json
import logging
from dotenv import load_dotenv
from tqdm import tqdm
import openai
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams
import hashlib



# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/vudev/workspace/chat_hcns_server/logs/embed_qa.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('embedding')


def hash_filename(filename, length=7):
    base = filename.replace('.json', '')
    hash_object = hashlib.md5(base.encode()) 
    hex_digest = hash_object.hexdigest()
    integer_value = int(hex_digest, 16) 
    return int(str(integer_value)[:length])  
# Load environment variables từ file .env
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_KEY_APHONG")
# QDRANT_API_KEY = os.getenv("QDRANT_KEY_HBC_HCNS")
# QDRANT_HOST = "https://30293fb2-6de0-4400-b89f-80626836b5ea.us-east4-0.gcp.cloud.qdrant.io"

# Khởi tạo client cho OpenAI và Qdrant
client = openai.OpenAI(api_key=OPENAI_API_KEY,)
# qdrant_client = QdrantClient(QDRANT_HOST, api_key=QDRANT_API_KEY)
qdrant_client = QdrantClient(host="localhost", port=6333)
COLLECTION_NAME = "HBC_CHATBOT_QA"

# Khởi tạo collection nếu chưa tồn tại
if not qdrant_client.collection_exists(COLLECTION_NAME):
    qdrant_client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=3072, distance="Cosine")
    )
    logger.info(f"Đã tạo collection '{COLLECTION_NAME}' trên Qdrant.")
else:
    logger.info(f"Collection '{COLLECTION_NAME}' đã tồn tại trên Qdrant.")

# Đường dẫn đến thư mục chứa các file JSON
json_path = "/home/vudev/workspace/chat_hcns_server/data/QandA"

def create_embedding(text):
    """Tạo vector embedding từ văn bản sử dụng OpenAI API"""
    try:
        response = client.embeddings.create(
            model="text-embedding-3-large",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Lỗi khi tạo embedding: {e}")
        return None

def process_json_files():
    """Xử lý tất cả các file JSON trong thư mục và tạo embedding"""
    counter = 0
    batch_points = []
    BATCH_SIZE = 1  # Số lượng point trong một batch
    
    # Liệt kê tất cả các file JSON trong thư mục
    json_files = [f for f in os.listdir(json_path) if f.endswith('.json')]
    
    logger.info(f"Tìm thấy {len(json_files)} file JSON cần xử lý...")
    
    for filename in tqdm(json_files, desc="Xử lý file JSON"):
        file_path = os.path.join(json_path, filename)
        
        try:
            # Đọc nội dung file JSON
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Kết hợp các trường để tạo văn bản cho embedding
            question = data.get('question')
            suggest_response = data.get('suggest_response')
            
            
            # Tạo embedding
            vector = create_embedding(question)
            if not vector:
                logger.warning(f"Không thể tạo embedding cho file {filename}")
                continue
            
            
            # Tạo payload
            payload = {
                "content": question,
                "metadata": {
                    "topic": "Hành chính nhân sự" if data.get('topic', '') == "HCNS" else "Thông tin chung",
                    "author": data.get('user_email', ''),
                    "question": question,
                    "suggest_response": suggest_response,
                    "tags": [question],
                    "file_name": filename
                }
            }
            
            # Tạo point
            point = PointStruct(
                id=hash_filename(filename),
                vector=vector,
                payload=payload
            )
            
            batch_points.append(point)
            counter += 1
            
            # Upload batch khi đạt kích thước
            if len(batch_points) >= BATCH_SIZE:
                try:
                    qdrant_client.upsert(
                        collection_name=COLLECTION_NAME,
                        points=batch_points
                    )
                    logger.info(f"Đã upload batch {counter - len(batch_points)} đến {counter - 1}")
                except Exception as e:
                    logger.error(f"Lỗi khi upload batch {counter - len(batch_points)} đến {counter - 1}: {e}")
                batch_points = []
                
        except Exception as e:
            logger.error(f"Lỗi khi xử lý file {filename}: {e}")
    
    # Upload batch cuối cùng nếu còn
    if batch_points:
        try:
            qdrant_client.upsert(
                collection_name=COLLECTION_NAME,
                points=batch_points
            )
            logger.info(f"Đã upload batch cuối cùng với {len(batch_points)} points")
        except Exception as e:
            logger.error(f"Lỗi khi upload batch cuối cùng: {e}")
    
    logger.info(f"Hoàn tất quá trình embedding! Đã xử lý {counter} file JSON.")

if __name__ == "__main__":
    logger.info("Bắt đầu quá trình embedding cho các file JSON...")
    process_json_files()