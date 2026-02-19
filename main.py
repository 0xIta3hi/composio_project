import os
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# 1. NEW IMPORTS: Ollama & ReAct Agent
from langchain_ollama import ChatOllama
from langchain_classic.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate

# 2. Composio Imports (Kept exactly as you had them)
from composio import Composio
from composio_langchain import LangchainProvider

# --- CONFIGURATION ---
os.environ["COMPOSIO_API_KEY"] = "ak_GiG5fj7cc1S7h3V9MBxc" 
# Google API Key removed - we are fully local now!

app = FastAPI()

# --- INITIALIZATION ---
print("1. Initializing Composio (New Provider Pattern)...")
client = Composio(
    api_key=os.environ.get("COMPOSIO_API_KEY"),
    provider=LangchainProvider()
)

print("2. Fetching Tools...")
try:
    raw_tools = client.tools.get(
        user_id="default", 
        toolkits=["gmail", "googlecalendar"]
    )
    print(f"✅ Loaded {len(raw_tools)} tools natively.")
    
    # FIX: Manually wrap tools to accept LangChain's argument format
    from langchain_core.tools import tool
    
    tools = []
    for raw_tool in raw_tools:
        # Create wrapper function with proper argument handling
        def create_wrapper(t):
            @tool
            def wrapped_tool(input_data: str) -> str:
                """Execute Composio tool"""
                try:
                    import json
                    args = json.loads(input_data) if isinstance(input_data, str) else input_data
                    result = client.tools.execute(
                        slug=t.name,
                        arguments=args,
                        user_id="default",
                        dangerously_skip_version_check=True  # FIX: Skip version check for manual execution
                    )
                    return str(result)
                except Exception as e:
                    return f"Error executing {t.name}: {str(e)}"
            
            wrapped_tool.name = t.name
            wrapped_tool.description = t.description
            return wrapped_tool
        
        tools.append(create_wrapper(raw_tool))
    
except Exception as e:
    print(f"❌ Error fetching tools: {e}")
    tools = []

print("3. Initializing Local Qwen Agent...")
# Swapped Gemini for Local Qwen
llm = ChatOllama(
    model="qwen2.5-coder:latest", # Or just "qwen2.5-coder" if you have >8GB VRAM
    temperature=0,            # 0 is critical for strict JSON generation
    num_ctx=4096              # Reasonable context window for speed
)

# 4. THE FIX: Strict ReAct Prompt for Local LLMs
# Local models MUST be forced to output valid JSON for tools.
template = """
You are a helpful AI assistant running locally. Today is Feb 19, 2026.
You have access to the following tools:

{tools}

CRITICAL INSTRUCTIONS:
1. To use a tool, you MUST use the exact format below.
2. The "Action Input" MUST be a valid JSON object.
3. Do not invent tools. Only use the ones listed.

Format:
Question: the input question you must answer
Thought: I need to use a tool to get information.
Action: the action to take, should be one of [{tool_names}]
Action Input: {{ "arg_name": "value" }}
Observation: [Tool output will appear here]
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: [Your final response to the user]

Begin!

Question: {input}
Thought:{agent_scratchpad}
"""

prompt = PromptTemplate.from_template(template)

# Create the ReAct Agent
if tools:
    agent = create_react_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=tools, 
        verbose=True, 
        handle_parsing_errors=True, # Automatically fixes bad JSON from Qwen
        max_iterations=5            # Prevents infinite loops if the model gets confused
    )
else:
    agent_executor = None

# --- API ENDPOINT ---
class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    if not agent_executor:
        raise HTTPException(status_code=500, detail="Agent failed to initialize tools")
    
    try:
        print(f"\n📩 User: {request.message}")
        result = agent_executor.invoke({"input": request.message})
        return {"reply": result["output"]}
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"error": str(e)}

# --- RUNNER ---
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)