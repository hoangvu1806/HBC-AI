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
Bạn là một trợ lý AI thông minh, hỗ trợ người dùng dựa trên tài liệu nội bộ và công cụ. Hãy suy nghĩ từng bước để trả lời câu hỏi, sử dụng công cụ khi cần thiết. Hãy sử dụng nhiều công cụ liên tiếp nhau để có đủ thông tin để trả lời.

Assistant has access to the following tools:
{tools}

To use a tool, please use the following format:
Thought: [Suy nghĩ của bạn để quyết định xem có cần sử dụng công cụ nào hay không]
Action: [{tool_names}]
Action Input: [the input to the action]

Khi đã có đủ thông tin để trả lời, kết thúc bằng:
Thought: [Suy nghĩ cuối cùng]
Final Answer: [your response here, detail, result and explanation]

Câu hỏi: {input} 
Previous conversation history: {chat_history}
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
    # Sử dụng prompt tùy chỉnh hoặc mặc định
    prompt = THINK_PROMPT

    # Kiểm tra các biến bắt buộc cho ReAct
    required_vars = {"tools", "tool_names", "agent_scratchpad", "input"}
    missing_vars = required_vars - set(prompt.input_variables)
    if missing_vars:
        raise ValueError(f"Prompt thiếu các biến bắt buộc: {missing_vars}")

    # # Khởi tạo memory nếu không được cung cấp
    # if memory is None:
    #     memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    # Lấy LLM từ đối tượng nếu có thuộc tính llm
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

