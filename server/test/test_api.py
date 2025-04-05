import os
import sys
import unittest
import time
import json
import requests

# Thêm thư mục cha vào sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Cấu hình API URL
API_URL = os.getenv("API_URL", "http://localhost:8000")

class TestRagAPI(unittest.TestCase):
    """
    Kiểm tra RAG API
    """
    
    def test_health_endpoint(self):
        """Kiểm tra endpoint health"""
        response = requests.get(f"{API_URL}/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
    
    def test_config_endpoint(self):
        """Kiểm tra endpoint config"""
        response = requests.get(f"{API_URL}/api/config")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("model_name", data)
        self.assertIn("qdrant_status", data)
        self.assertIn("api_keys", data)
    
    def test_chat_endpoint(self):
        """Kiểm tra endpoint chat"""
        # Gửi tin nhắn đơn giản
        payload = {
            "message": "Xin chào, tôi muốn biết thông tin về chính sách lương",
            "conversation_id": None
        }
        response = requests.post(f"{API_URL}/api/chat", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        self.assertIn("conversation_id", data)
        
        # Lưu conversation_id để sử dụng trong các test tiếp theo
        conversation_id = data["conversation_id"]
        
        # Gửi tin nhắn tiếp theo trong cùng cuộc hội thoại
        payload = {
            "message": "Còn chế độ phụ cấp thì sao?",
            "conversation_id": conversation_id
        }
        response = requests.post(f"{API_URL}/api/chat", json=payload)
        self.assertEqual(response.status_code, 200)
        
        # Xóa lịch sử hội thoại
        response = requests.post(f"{API_URL}/api/chat/clear", params={"conversation_id": conversation_id})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
    
    def test_change_provider(self):
        """Kiểm tra endpoint đổi provider"""
        # Tạo một phiên hội thoại mới
        payload = {
            "message": "Xin chào",
            "conversation_id": None
        }
        response = requests.post(f"{API_URL}/api/chat", json=payload)
        conversation_id = response.json()["conversation_id"]
        
        # Đổi provider cho phiên này
        payload = {
            "provider": "gemini",
            "conversation_id": conversation_id
        }
        response = requests.post(f"{API_URL}/api/provider/change", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        
        # Kiểm tra config sau khi đổi
        response = requests.get(f"{API_URL}/api/config")
        data = response.json()
        
        # Xóa phiên hội thoại
        response = requests.delete(f"{API_URL}/api/sessions/{conversation_id}")
        self.assertEqual(response.status_code, 200)
    
    def test_sessions_list(self):
        """Kiểm tra danh sách phiên hội thoại"""
        # Tạo một vài phiên hội thoại
        sessions = []
        for i in range(3):
            payload = {
                "message": f"Tin nhắn test {i}",
                "conversation_id": None
            }
            response = requests.post(f"{API_URL}/api/chat", json=payload)
            sessions.append(response.json()["conversation_id"])
        
        # Kiểm tra danh sách phiên
        response = requests.get(f"{API_URL}/api/sessions")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("sessions", data)
        self.assertIn("count", data)
        self.assertGreaterEqual(data["count"], 3)
        
        # Xóa các phiên đã tạo
        for session_id in sessions:
            requests.delete(f"{API_URL}/api/sessions/{session_id}")

if __name__ == "__main__":
    # Kiểm tra xem server đã chạy chưa
    try:
        requests.get(f"{API_URL}/api/health")
        # Chạy test nếu server đã hoạt động
        unittest.main()
    except requests.exceptions.ConnectionError:
        print(f"Không thể kết nối tới API tại {API_URL}")
        print("Hãy đảm bảo server đang chạy trước khi chạy test")
        sys.exit(1) 