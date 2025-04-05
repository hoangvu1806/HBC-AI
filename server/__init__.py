# """
# Chat HCNS Server package với RAG (Retrieval Augmented Generation)

# Package này chứa các module cần thiết để tạo ứng dụng trợ lý AI với khả năng
# tìm kiếm thông tin trong cơ sở dữ liệu Qdrant.
# """

# __version__ = "1.0.0"

# # Import các thành phần chính để dễ dàng sử dụng
# try:
#     from .model import LLM
#     from .agent_tools import AgentTools
#     from .chat_with_RAG import RAGAgent
#     from .agent_creator import create_langchain_agent
# except ImportError as e:
#     print(f"Không thể import một số component: {e}")
#     # Không raise exception để package vẫn có thể được import
