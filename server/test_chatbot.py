#!/usr/bin/env python
import os
import sys
import asyncio
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Thêm thư mục gốc vào sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Đảm bảo thư mục hiện tại cũng có trong sys.path
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from server.chat_with_RAG import RAGAgent
except ImportError:
    try:
        from chat_with_RAG import RAGAgent
    except ImportError:
        print("Không thể import RAGAgent. Kiểm tra cấu trúc thư mục.")
        sys.exit(1)

# Load biến môi trường
load_dotenv()

class ChatbotTester:
    def __init__(self):
        self.agent = None
        self.session_id = None
        self.email = None
        self.expertor = None
        self.session_name = None
        self.mode = "normal"
    
    def initialize_agent(self) -> None:
        """Khởi tạo RAG Agent"""
        print("\n=== Khởi tạo RAG Agent ===")
        try:
            self.agent = RAGAgent(
                model_name=os.getenv("MODEL_NAME"),
                temperature=float(os.getenv("TEMPERATURE", "0.7")),
                qdrant_host=os.getenv("QDRANT_HOST", "localhost"),
                qdrant_port=int(os.getenv("QDRANT_PORT", "6333")),
                collection_name=os.getenv("QDRANT_COLLECTION", "HBC_P_HCNS_KNOWLEDGE_BASE"),
                provider=os.getenv("LLM_PROVIDER", "openai"),
                use_postgres_memory=True
            )
            print("Khởi tạo RAG Agent thành công")
        except Exception as e:
            print(f"Lỗi khi khởi tạo RAG Agent: {e}")
            sys.exit(1)
    
    def setup_session(self) -> None:
        """Thiết lập phiên chat"""
        print("\n=== Thiết lập phiên chat ===")
        self.email = input("Nhập email (Enter để dùng mặc định 'guest'): ").strip() or "guest"
        self.expertor = input("Nhập tên chatbot (Enter để dùng mặc định 'default'): ").strip() or "default"
        self.session_name = input("Nhập tên phiên chat: ").strip()
        
        while not self.session_name:
            print("Tên phiên chat không được để trống.")
            self.session_name = input("Nhập tên phiên chat: ").strip()
        
        mode_input = input("Chọn chế độ (normal/think, Enter để dùng mặc định 'normal'): ").strip().lower()
        self.mode = mode_input if mode_input in ["normal", "think"] else "normal"
        
        try:
            # Khởi tạo phiên chat trong PostgreSQL
            self.session_id = self.agent.llm.init_session(
                session_name=self.session_name,
                email=self.email,
                expertor=self.expertor
            )
            
            if self.session_id:
                print(f"Đã khởi tạo phiên chat '{self.session_name}' thành công với ID: {self.session_id}")
                # Lấy lịch sử chat (nếu phiên đã tồn tại)
                history = self.agent.llm.get_history()
                if history and len(history) > 0:
                    print(f"Đã tìm thấy {len(history)} tin nhắn trong lịch sử")
            else:
                print("Không thể khởi tạo phiên chat trong PostgreSQL, sẽ sử dụng bộ nhớ tạm thời")
        except Exception as e:
            print(f"Lỗi khi khởi tạo phiên chat: {e}")
    
    def chat_loop(self) -> None:
        """Vòng lặp chat"""
        print("\n=== Bắt đầu chat ===")
        print(f"Chế độ: {self.mode}")
        print("Nhập 'exit', 'quit' hoặc 'q' để thoát")
        print("Nhập 'clear' để xóa lịch sử hội thoại")
        print("Nhập 'mode normal' hoặc 'mode think' để chuyển chế độ")
        
        while True:
            try:
                # Hiển thị prompt với thông tin phiên
                prompt = input(f"\n[{self.email}/{self.expertor}/{self.session_name}] > ")
                
                # Kiểm tra lệnh đặc biệt
                if prompt.lower() in ["exit", "quit", "q"]:
                    print("Tạm biệt!")
                    break
                elif prompt.lower() == "clear":
                    self.agent.clear_memory()
                    print("Đã xóa lịch sử hội thoại")
                    continue
                elif prompt.lower().startswith("mode "):
                    new_mode = prompt.lower().split(" ")[1]
                    if new_mode in ["normal", "think"]:
                        self.mode = new_mode
                        print(f"Đã chuyển sang chế độ '{self.mode}'")
                    else:
                        print(f"Chế độ không hợp lệ: {new_mode}. Chỉ hỗ trợ 'normal' hoặc 'think'")
                    continue
                elif not prompt.strip():
                    continue
                
                # Gửi tin nhắn và hiển thị phản hồi
                print("\nBot đang xử lý...")
                response = self.agent.chat(prompt, mode=self.mode)
                print(f"\nBot: {response['result']}")
                
            except KeyboardInterrupt:
                print("\nĐã ngắt bởi người dùng")
                break
            except Exception as e:
                print(f"Lỗi: {e}")
    
    async def stream_chat_loop(self) -> None:
        """Vòng lặp chat với stream"""
        print("\n=== Bắt đầu chat ===")
        print(f"Chế độ: {self.mode} (stream)")
        print("Nhập 'exit', 'quit' hoặc 'q' để thoát")
        print("Nhập 'clear' để xóa lịch sử hội thoại")
        print("Nhập 'mode normal' hoặc 'mode think' để chuyển chế độ")
        
        while True:
            try:
                # Hiển thị prompt với thông tin phiên
                prompt = input(f"\n[{self.email}/{self.expertor}/{self.session_name}] > ")
                
                # Kiểm tra lệnh đặc biệt
                if prompt.lower() in ["exit", "quit", "q"]:
                    print("Tạm biệt!")
                    break
                elif prompt.lower() == "clear":
                    self.agent.clear_memory()
                    print("Đã xóa lịch sử hội thoại")
                    continue
                elif prompt.lower().startswith("mode "):
                    new_mode = prompt.lower().split(" ")[1]
                    if new_mode in ["normal", "think"]:
                        self.mode = new_mode
                        print(f"Đã chuyển sang chế độ '{self.mode}'")
                    else:
                        print(f"Chế độ không hợp lệ: {new_mode}. Chỉ hỗ trợ 'normal' hoặc 'think'")
                    continue
                elif not prompt.strip():
                    continue
                
                # Gửi tin nhắn và hiển thị phản hồi stream
                print("\nBot: ", end="", flush=True)
                async for chunk in self.agent.stream_chat(prompt, mode=self.mode):
                    print(chunk, end="", flush=True)
                print()  # Xuống dòng sau khi stream hoàn tất
                
            except KeyboardInterrupt:
                print("\nĐã ngắt bởi người dùng")
                break
            except Exception as e:
                print(f"Lỗi: {e}")
    
    def run(self, use_stream: bool = True) -> None:
        """Chạy trình kiểm tra chatbot"""
        self.initialize_agent()
        self.setup_session()
        
        if use_stream:
            asyncio.run(self.stream_chat_loop())
        else:
            self.chat_loop()

if __name__ == "__main__":
    print("=== Chương trình test chatbot ===")
    
    # Kiểm tra tham số dòng lệnh
    use_stream = True
    if len(sys.argv) > 1 and sys.argv[1].lower() == "--no-stream":
        use_stream = False
    
    tester = ChatbotTester()
    tester.run(use_stream=use_stream) 