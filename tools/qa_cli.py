#!/usr/bin/env python3
import os
import sys
import argparse
from typing import List, Dict, Any
import logging
from tabulate import tabulate

# Thêm thư mục gốc vào sys.path để import các module
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from embedding.retrieve_qa import QARetriever, COLLECTION_NAME
from qdrant_client import QdrantClient

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('qa_cli')

def setup_qdrant_client() -> QdrantClient:
    """Thiết lập kết nối tới Qdrant"""
    return QdrantClient(host="localhost", port=6333)

def display_collection_info(retriever: QARetriever) -> None:
    """Hiển thị thông tin về collection"""
    info = retriever.get_collection_info()
    print("\n===== THÔNG TIN COLLECTION =====")
    print(f"Tên:           {info['name']}")
    print(f"Vector size:   {info['vector_size']}")
    print(f"Distance:      {info['distance']}")
    print(f"Số điểm dữ liệu: {info['total_points']}")
    print(f"Trạng thái:    {info['status']}")
    print("===============================\n")

def display_qa_list(qa_list: List[Dict[str, Any]], limit: int = None) -> None:
    """Hiển thị danh sách Q&A dưới dạng bảng"""
    if not qa_list:
        print("Không có dữ liệu Q&A để hiển thị.")
        return
    
    # Giới hạn số lượng kết quả nếu cần
    if limit and len(qa_list) > limit:
        qa_list = qa_list[:limit]
    
    # Tạo dữ liệu cho bảng
    headers = ["ID", "Câu hỏi", "Trả lời (tóm tắt)", "Chủ đề"]
    data = []
    
    for qa in qa_list:
        # Tóm tắt câu trả lời nếu quá dài
        answer_summary = qa['answer'][:100] + "..." if len(qa['answer']) > 100 else qa['answer']
        question_summary = qa['question'][:100] + "..." if len(qa['question']) > 100 else qa['question']
        
        data.append([
            qa['id'],
            question_summary,
            answer_summary,
            qa['topic']
        ])
    
    # Hiển thị bảng
    print(tabulate(data, headers=headers, tablefmt="fancy_grid"))
    print(f"\nTổng số: {len(qa_list)} mục")

def display_single_qa(qa: Dict[str, Any]) -> None:
    """Hiển thị chi tiết một Q&A"""
    if not qa:
        print("Không tìm thấy dữ liệu Q&A.")
        return
    
    print("\n===== CHI TIẾT Q&A =====")
    print(f"ID:       {qa['id']}")
    print(f"Chủ đề:   {qa['topic']}")
    print(f"File:     {qa['file_name']}")
    print(f"Tags:     {', '.join(qa['tags']) if qa['tags'] else 'Không có'}")
    if 'score' in qa:
        print(f"Điểm số: {qa['score']:.4f}")
    
    print("\n>>> CÂU HỎI:")
    print(qa['question'])
    
    print("\n>>> TRẢ LỜI:")
    print(qa['answer'])
    print("=======================\n")

def main() -> None:
    parser = argparse.ArgumentParser(description="Công cụ quản lý Q&A từ dòng lệnh")
    subparsers = parser.add_subparsers(dest="command", help="Lệnh")
    
    # Lệnh info - lấy thông tin collection
    info_parser = subparsers.add_parser("info", help="Hiển thị thông tin collection")
    
    # Lệnh list - liệt kê Q&A
    list_parser = subparsers.add_parser("list", help="Liệt kê các cặp Q&A")
    list_parser.add_argument("--limit", type=int, default=10, help="Số lượng kết quả tối đa")
    list_parser.add_argument("--offset", type=int, default=0, help="Vị trí bắt đầu")
    
    # Lệnh get - lấy thông tin một Q&A theo ID
    get_parser = subparsers.add_parser("get", help="Lấy thông tin một Q&A theo ID")
    get_parser.add_argument("id", help="ID của Q&A cần lấy")
    
    # Lệnh search - tìm kiếm Q&A theo từ khóa
    search_parser = subparsers.add_parser("search", help="Tìm kiếm Q&A theo từ khóa")
    search_parser.add_argument("query", help="Từ khóa tìm kiếm")
    search_parser.add_argument("--limit", type=int, default=5, help="Số lượng kết quả tối đa")
    
    # Lệnh topic - lọc Q&A theo chủ đề
    topic_parser = subparsers.add_parser("topic", help="Lọc Q&A theo chủ đề")
    topic_parser.add_argument("topic", help="Chủ đề cần lọc")
    topic_parser.add_argument("--limit", type=int, default=10, help="Số lượng kết quả tối đa")
    
    # Xử lý tham số
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Khởi tạo retriever
    client = setup_qdrant_client()
    retriever = QARetriever(client, COLLECTION_NAME)
    
    # Xử lý các lệnh
    if args.command == "info":
        display_collection_info(retriever)
    
    elif args.command == "list":
        qa_list = retriever.get_all_qa(limit=args.limit, offset=args.offset)
        display_qa_list(qa_list)
    
    elif args.command == "get":
        qa = retriever.get_qa_by_id(args.id)
        display_single_qa(qa)
    
    elif args.command == "search":
        qa_list = retriever.search_by_keywords(args.query, limit=args.limit)
        print(f"\nKết quả tìm kiếm cho: '{args.query}'")
        if qa_list:
            display_qa_list(qa_list)
            
            # Hiển thị chi tiết kết quả đầu tiên
            print("\nChi tiết kết quả tốt nhất:")
            display_single_qa(qa_list[0])
        else:
            print("Không tìm thấy kết quả nào.")
    
    elif args.command == "topic":
        qa_list = retriever.search_by_topic(args.topic, limit=args.limit)
        print(f"\nKết quả lọc theo chủ đề: '{args.topic}'")
        display_qa_list(qa_list)

if __name__ == "__main__":
    main() 