"""
DeepSeek LLM wrapper using LangChain
"""
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from typing import Optional, List, Dict, Any

from backend.config import get_settings

settings = get_settings()


def get_llm(
    temperature: float = 0.7,
    max_tokens: int = 2048,
    model: str = "deepseek-chat"
) -> ChatOpenAI:
    """
    Get a DeepSeek LLM instance.
    
    DeepSeek API is compatible with OpenAI API format.
    
    Args:
        temperature: Sampling temperature (0-1)
        max_tokens: Maximum tokens in response
        model: Model name (deepseek-chat or deepseek-coder)
    
    Returns:
        ChatOpenAI instance configured for DeepSeek
    """
    return ChatOpenAI(
        model=model,
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        temperature=temperature,
        max_tokens=max_tokens
    )


async def chat_completion(
    messages: List[Dict[str, str]],
    temperature: float = 0.7,
    max_tokens: int = 2048,
    model: str = "deepseek-chat"
) -> str:
    """
    Simple chat completion function.
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        temperature: Sampling temperature
        max_tokens: Maximum tokens
        model: Model name
    
    Returns:
        Generated response text
    """
    llm = get_llm(temperature=temperature, max_tokens=max_tokens, model=model)
    
    # Convert to LangChain message format
    lc_messages = []
    for msg in messages:
        if msg["role"] == "system":
            lc_messages.append(SystemMessage(content=msg["content"]))
        else:
            lc_messages.append(HumanMessage(content=msg["content"]))
    
    response = await llm.ainvoke(lc_messages)
    return response.content


# Pre-configured LLM instances
def get_chat_llm() -> ChatOpenAI:
    """Get LLM optimized for chat"""
    return get_llm(temperature=0.7, model="deepseek-chat")


def get_code_llm() -> ChatOpenAI:
    """Get LLM optimized for code tasks"""
    return get_llm(temperature=0.2, model="deepseek-coder")


def get_quiz_llm() -> ChatOpenAI:
    """Get LLM for quiz generation (more creative)"""
    return get_llm(temperature=0.8, max_tokens=4096, model="deepseek-chat")
