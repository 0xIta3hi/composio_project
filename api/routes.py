"""FastAPI routes for the chat endpoint."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from langchain.agents import create_react_agent, AgentExecutor

from core.llm import get_llm
from core.prompts import get_prompt
from integrations.composio_tools import get_tools
from integrations.formatters import format_agent_output


# Router
router = APIRouter()

# Models
class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str


# Initialize agent components (singleton-like pattern)
_agent_executor = None


def _initialize_agent() -> AgentExecutor:
    """
    Initialize the agent executor with LLM, prompt, and tools.
    
    Returns:
        AgentExecutor instance ready to process queries
    """
    global _agent_executor
    
    if _agent_executor is not None:
        return _agent_executor
    
    # Get components
    llm = get_llm()
    prompt = get_prompt()
    tools, composio_client = get_tools()
    
    if not tools:
        return None
    
    # Create ReAct agent
    agent = create_react_agent(llm, tools, prompt)
    
    _agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,  # Automatically fixes bad JSON from Qwen
        max_iterations=5               # Prevents infinite loops if the model gets confused
    )
    
    return _agent_executor


@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Main chat endpoint that processes user messages through the AI agent.
    
    Args:
        request: ChatRequest containing the user message
        
    Returns:
        Dict with 'reply' key containing the formatted response
        
    Raises:
        HTTPException 500 if agent initialization fails
    """
    agent_executor = _initialize_agent()
    
    if not agent_executor:
        raise HTTPException(status_code=500, detail="Agent failed to initialize tools")
    
    try:
        print(f"\n📩 User: {request.message}")
        
        # Execute agent
        result = agent_executor.invoke({"input": request.message})
        
        # Get and format the final answer
        output = result.get("output", "")
        formatted_output = format_agent_output(output)
        
        return {"reply": formatted_output}
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}
