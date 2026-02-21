"""LLM initialization and configuration."""

from langchain_ollama import ChatOllama


def get_llm() -> ChatOllama:
    """
    Initialize and return the Qwen 2.5 Coder LLM.
    
    Returns:
        ChatOllama: Configured Qwen model instance
    """
    print("3. Initializing Local Qwen Agent...")
    
    llm = ChatOllama(
        model="qwen2.5-coder:latest",  # Or just "qwen2.5-coder" if you have >8GB VRAM
        temperature=0,                  # 0 is critical for strict JSON generation
        num_ctx=4096                    # Reasonable context window for speed
    )
    
    return llm
