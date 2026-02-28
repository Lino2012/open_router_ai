import openai
from .config import get_settings

settings = get_settings()

# Configure OpenAI client to use OpenRouter
client = openai.OpenAI(
    base_url=settings.OPENROUTER_BASE_URL,
    api_key=settings.OPENROUTER_API_KEY,
    default_headers={
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "Nova AI Chatbot",
    }
)

__all__ = ["client"]