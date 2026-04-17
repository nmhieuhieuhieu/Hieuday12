import os
import logging
from openai import OpenAI
from .mock_llm import ask as mock_ask

logger = logging.getLogger(__name__)

# Khởi tạo client OpenAI nếu có key
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None

def ask(question: str) -> str:
    """Gọi LLM thật (GPT-4o-mini) nếu có API key, ngược lại dùng mock."""
    if not client:
        logger.info("OPENAI_API_KEY không được tìm thấy. Đang sử dụng mock LLM fallback.")
        return mock_ask(question)
        
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful, smart, and enthusiastic AI assistant deployed on the cloud. Always format your responses clearly."},
                {"role": "user", "content": question}
            ],
            max_tokens=800,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Lỗi khi gọi OpenAI API: {str(e)}")
        return f"Lỗi nội bộ khi gọi LLM: {str(e)}. Hãy chắc chắn là key của bạn hợp lệ và còn tiền nhé!"
