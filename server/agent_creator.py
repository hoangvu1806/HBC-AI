import os
import sys

# Thêm thư mục gốc vào sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import os
import sys
from typing import List, Optional
from langchain.agents import AgentExecutor, create_react_agent, initialize_agent, AgentType
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory

# Thêm thư mục gốc vào sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Prompt cho chế độ "think" (ReAct)
THINK_PROMPT = PromptTemplate.from_template("""
Bạn là **HBC AI**, một trợ lý AI đáng tin cậy của Công ty Cổ phần Hòa Bình.  
Bạn có khả năng **suy luận từng bước và sử dụng công cụ** để giúp nhân viên công ty giải quyết các vấn đề liên quan đến chính sách, quy , quy định, thông tin nội bộ...

Bạn phải luôn xem xét **lịch sử chat** trước để xác định ngữ cảnh của câu hỏi hiện tại của người dùng. Rồi mới xác định rõ câu hỏi của người dùng là gì.

NẾU CÂU HỎI KHÔNG LIÊN QUAN ĐẾN NỘI DUNG NỘI BỘ NHƯ: thông tin, hoạt động, chính sách và quy trình trong Công ty Cổ phần Hòa Bình.
, HÃY TRẢ LỜI NHƯ SAU:
⚠️ Cảm ơn bạn đã đặt câu hỏi! **HBC AI** là trợ lý AI nội bộ, được thiết kế để hỗ trợ các vấn đề liên quan đến hoạt động, chính sách và quy trình trong Công ty Cổ phần Hòa Bình.
Nội dung bạn hỏi hiện nằm ngoài phạm vi thông tin nội bộ mà hệ thống có thể truy xuất.
🎯 Nếu bạn cần hỗ trợ về thủ tục nhân sự, biểu mẫu, quyền lợi, quy trình làm việc hoặc thông tin nội bộ khác, **HBC AI*** luôn sẵn sàng đồng hành cùng bạn!
Và sau đó trả về Final Answer: <câu trả lời dành cho người dùng (luôn trả lời chi tiết và phân tích câu trả lời đó)>
---
### 🧠 Hướng dẫn hành động:
Trước tiên, hãy **đọc kỹ lịch sử cuộc trò chuyện (chat history)** để hiểu rõ bối cảnh trước đó.
1. **Suy nghĩ** về yêu cầu của người dùng bằng cách bắt đầu với `Thought:`.
2. Nếu cần thiết, **sử dụng một công cụ phù hợp** bằng cách viết rõ:
   - `Action: <tên công cụ>` (bắt buộc phải khớp với danh sách công cụ có sẵn)
   - `Action Input: <đầu vào cho công cụ đó>`
3. Ghi lại phản hồi của công cụ bằng `Observation:`.
4. Lặp lại nếu cần thiết.
5. Khi đã có đầy đủ thông tin, **kết thúc bằng câu trả lời cuối cùng**:
   - `Final Answer: <câu trả lời dành cho người dùng (luôn trả lời chi tiết và phân tích câu trả lời đó)>`
Assistant has access to the following tools: {tools}

❗ Tuyệt đối không bỏ qua định dạng sau:
- Sau mỗi `Thought:` PHẢI có `Action:` và `Action Input:` nếu chưa có đủ thông tin.
- Chỉ được dùng `Final Answer:` SAU KHI có ít nhất một `Observation:` từ công cụ.
- Nếu không làm đúng định dạng này, yêu cầu sẽ bị xem là **không hợp lệ**.
---

### ✅ Định dạng bắt buộc:

```
Thought: <suy nghĩ hiện tại>
Action: <tên công cụ>
Action Input: <đầu vào cho công cụ>

Observation: <kết quả trả về từ công cụ>

Thought: <suy nghĩ tiếp theo>
... (tiếp tục nếu cần)

Thought: Tôi đã có đủ thông tin.
Final Answer: <câu trả lời cho người dùng>
```
---
### 📌 Danh sách công cụ bạn có thể sử dụng:
{tool_names}
---
### 🔐 Lưu ý:
- Luôn **tuân thủ đúng định dạng** để tránh lỗi xử lý (ví dụ: phải có `Action:` sau `Thought:` nếu cần dùng công cụ).
- Chỉ trả lời khi đã có đầy đủ thông tin.
- Không đưa ra câu trả lời nếu chưa quan sát (`Observation:`) từ công cụ.
- Nếu không chắc chắn, hãy tiếp tục suy nghĩ (`Thought:`) thay vì đoán bừa.
---
### 🎯 Câu hỏi của người dùng: {input}
Lịch sử nhắn tin: {chat_history}
Không gian suy nghĩ: {agent_scratchpad}
""")

with open(os.getenv("SYSTEM_PROMPT_PATH"), 'r', encoding='utf-8') as f:
    content: str = f.read()
NORMAL_PROMPT = PromptTemplate.from_template(content)

def create_think_agent(llm, tools: List,system_prompt: Optional[str] = None, memory: Optional = None, verbose: bool = True):
    """
    Tạo LangChain ReAct agent (chế độ "think") với flow minh bạch
    
    Args:
        llm: LLM instance (đã được khởi tạo)
        tools: Danh sách các tools cho agent
        system_prompt: System prompt tùy chỉnh (nếu None, dùng THINK_PROMPT)
        memory: Memory instance (nếu None, tạo mới ConversationBufferMemory)
        verbose: Hiển thị thông tin chi tiết
        
    Returns:
        AgentExecutor đã được khởi tạo
    """
    prompt = THINK_PROMPT


    required_vars = {"tools", "tool_names", "agent_scratchpad", "input"}
    missing_vars = required_vars - set(prompt.input_variables)
    if missing_vars:
        raise ValueError(f"Prompt thiếu các biến bắt buộc: {missing_vars}")

    llm_instance = llm.llm if hasattr(llm, 'llm') else llm

    # Tạo ReAct agent
    agent = create_react_agent(
        llm=llm_instance,
        tools=tools,
        prompt=prompt
    )

    # Tạo và trả về AgentExecutor với các cấu hình xử lý lỗi tốt hơn
    return AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,
        verbose=verbose,
        handle_parsing_errors=True,
        max_iterations=5,
        max_execution_time=None,
        return_intermediate_steps=True
    )

def create_normal_agent(llm, tools: List, system_prompt: Optional[str] = None, memory: Optional = None, verbose: bool = True):
    """
    Tạo LangChain agent (chế độ "bình thường") dùng initialize_agent
    
    Args:
        llm: LLM instance (đã được khởi tạo)
        tools: Danh sách các tools cho agent
        system_prompt: System prompt tùy chỉnh (nếu None, dùng mặc định đơn giản)
        memory: Memory instance (nếu None, tạo mới ConversationBufferMemory)
        verbose: Hiển thị thông tin chi tiết
        
    Returns:
        Agent đã được khởi tạo
    """
    # # Khởi tạo memory nếu không được cung cấp
    # if memory is None:
    #     memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    # Lấy LLM từ đối tượng nếu có thuộc tính llm
    llm_instance = llm.llm if hasattr(llm, 'llm') else llm
    # print(NORMAL_PROMPT)
    # Tạo agent dùng initialize_agent
    agent = initialize_agent(
        tools=tools,
        llm=llm_instance,
        agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
        verbose=verbose,
        memory=memory,
        handle_parsing_errors=True,
        system_prompt=NORMAL_PROMPT
    )
    return agent

