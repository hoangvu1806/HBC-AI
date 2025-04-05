import os
import re
from datetime import datetime
from dotenv import load_dotenv
from tqdm import tqdm
import openai
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams

# Load environment variables từ file .env
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_KEY_APHONG")
# QDRANT_API_KEY = os.getenv("QDRANT_KEY_HBC_HCNS")
# QDRANT_HOST = "https://30293fb2-6de0-4400-b89f-80626836b5ea.us-east4-0.gcp.cloud.qdrant.io"

# Khởi tạo client cho OpenAI và Qdrant
client = openai.OpenAI(api_key=OPENAI_API_KEY,)
# qdrant_client = QdrantClient(QDRANT_HOST, api_key=QDRANT_API_KEY)
qdrant_client = QdrantClient(host="localhost", port=6333)
COLLECTION_NAME = "HBC_P_CNTT_KNOWLEDGE_BASE"

if not qdrant_client.collection_exists(COLLECTION_NAME):
    qdrant_client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=3072, distance="Cosine")
    )
    print(f"Đã tạo collection '{COLLECTION_NAME}' trên Qdrant.")

root_path = r"/home/vudev/workspace/chat_hcns_server/data/CNTT_DATA_TEXT" 

def split_text(text, chunk_size=2000, overlap=500, tolerance=50):
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        if end >= text_length:
            chunks.append(text[start:])
            break
        
        # Tìm điểm ngắt tự nhiên gần nhất sau end
        search_end = min(end + tolerance, text_length)
        split_points = [m.start() for m in re.finditer(r'[.!?]\s|\n', text[end:search_end])]
        
        if split_points:
            split_point = split_points[0] + end
            chunk = text[start:split_point + 1]
        else:
            chunk = text[start:end]
        
        if chunk:
            chunks.append(chunk)

        start += len(chunk) - overlap
        if start >= text_length:
            break
    
    return chunks

# Hàm xác định section và group từ đường dẫn file
def get_section_and_group(file_path, root_path):
    rel_path = os.path.relpath(file_path, root_path)
    parts = rel_path.split(os.sep)
    if len(parts) < 2:
        return None, None
    section = parts[0]
    for part in parts[1:]:
        if re.match(r'^\d+\.', part):
            return section, part
    return section, None

def extract_metadata(text):
    metadata = {
        "issue_number": None,
        "effective_date": None,
        "revision": None,
        "issue_date": None
    }
    patterns = {
        "issue_number": [
            r'Mã số \s*([\w./-]+)',
            r'Mã số:\s*([\w./-]+)',
            r'Mã số.*?([\w./-]+)',
        ],
        "effective_date": [
            r'Ngày hiệu lực \s*(\d{1,2}/\d{1,2}/\d{4})',
            r'Ngày hiệu lực: \s*(\d{1,2}/\d{1,2}/\d{4})',
            r'có hiệu lực từ.*?(\d{1,2}/\d{1,2}/\d{4})',
        ],
        "revision": [
            r'Lần ban hành \s*(\d+)',
            r'Lần ban hành: \s*(\d+)',
            r'Lần ban hành.*?(\d+)',
        ],
        "issue_date": [
            r'Ngày ban hành \s*(\d{1,2}/\d{1,2}/\d{4})',
            r'Ngày ban hành: \s*(\d{1,2}/\d{1,2}/\d{4})',
            r'ban hành ngày.*?(\d{1,2}/\d{1,2}/\d{4})',
        ]
    }
    
    for key, pattern_list in patterns.items():
        for pattern in pattern_list:
            matches = re.findall(pattern, text)
            if matches:
                value = matches[0]
                if key in ["effective_date", "issue_date"]:
                    try:
                        date_obj = datetime.strptime(value, '%d/%m/%Y')
                        metadata[key] = date_obj.strftime('%Y-%m-%d')
                    except ValueError:
                        continue
                else:
                    metadata[key] = value
                break
    return metadata

counter = 0
batch_points = []
BATCH_SIZE = 3

# Duyệt qua các file trong thư mục gốc
print("Bắt đầu xử lý các file text...")
for dirpath, dirnames, filenames in os.walk(root_path):
    for filename in tqdm(filenames, desc="Processing files"):
        if filename.endswith(".txt"):
            file_path = os.path.join(dirpath, filename)
            
            section, group = get_section_and_group(file_path, root_path)
            if not group:
                section = group = "CÔNG NGHỆ THÔNG TIN"
                print(f"Không tìm thấy nhóm tài liệu cho file: {file_path}")
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()
            except Exception as e:
                print(f"Lỗi khi đọc file {file_path}: {e}")
                continue
            
            # Trích xuất metadata từ file
            metadata = extract_metadata(text)
            chunks = split_text(text, chunk_size=1200, overlap=300)
            
            for idx, chunk in enumerate(chunks):
                try:
                    response = client.embeddings.create(
                        model="text-embedding-3-large",
                        input=chunk
                    )
                    vector = response.data[0].embedding
                except Exception as e:
                    print(f"Lỗi khi tạo embedding cho chunk {idx+1} của file {filename}: {e}")
                    continue
                
                rel_path = str(os.path.relpath(file_path, root_path)).replace(".txt", ".pdf")
                year = re.search(r'\b(20\d{2})\b', os.path.basename(file_path))
                payload = {
                    "content": chunk,
                    "metadata": {
                        "file_name": filename,
                        "section": section,
                        "department": "P.CNTT",
                        "group": group,
                        "company": "HBC",
                        "year": int(year.group(1)) if year else None,
                        "access_level": "internal",
                        "issue_number": metadata["issue_number"],
                        "effective_date": metadata["effective_date"],
                        "revision": metadata["revision"],
                        "issue_date": metadata["issue_date"],
                        "file_path": rel_path,
                    }
                }

                point = PointStruct(
                    id=counter,
                    vector=vector,
                    payload=payload
                )
                print(payload)
                batch_points.append(point)
                counter += 1
                
                if len(batch_points) == BATCH_SIZE:
                    try:
                        qdrant_client.upsert(
                            collection_name=COLLECTION_NAME,
                            points=batch_points
                        )
                        print(f"Đã upload batch {counter - BATCH_SIZE} đến {counter - 1}")
                    except Exception as e:
                        print(f"Lỗi khi upload batch {counter - BATCH_SIZE} đến {counter - 1}: {e}")
                    batch_points = []

# Upload batch cuối cùng nếu còn
if batch_points:
    try:
        qdrant_client.upsert(
            collection_name=COLLECTION_NAME,
            points=batch_points
        )
        print(f"Đã upload batch cuối cùng với {len(batch_points)} points")
    except Exception as e:
        print(f"Lỗi khi upload batch cuối cùng: {e}")

print("Hoàn tất quá trình embedding và upload!")