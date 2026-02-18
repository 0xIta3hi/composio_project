import os
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# 1. LangChain & Gemini Imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

# 2. THE FIX: New Composio Import Pattern
# We import the main Client + the LangChain Adapter
from composio import Composio
from composio_langchain import LangchainProvider

# --- CONFIGURATION ---
# Replace with your real keys
os.environ["COMPOSIO_API_KEY"] = "" 
os.environ["GOOGLE_API_KEY"] = ""

app = FastAPI()

# --- INITIALIZATION ---
print("1. Initializing Composio (New Provider Pattern)...")

# OLD WAY (Deleted): toolset = ComposioToolSet()
# NEW WAY: Inject LangchainProvider into the main client
client = Composio(
    api_key=os.environ.get("COMPOSIO_API_KEY"),
    provider=LangchainProvider()
)

print("2. Fetching Tools...")
try:
    # We fetch tools for the 'default' user we connected earlier
    # The 'provider' automatically formats them for LangChain
    tools = client.tools.get(
        user_id="default", 
        toolkits=["gmail", "googlecalendar"]
    )
    print(f"✅ Loaded {len(tools)} tools (e.g., {tools[0].name})")
except Exception as e:
    print(f"❌ Error fetching tools: {e}")
    tools = []

print("3. Initializing Gemini Agent...")
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0
)

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful AI assistant. Today is Feb 15, 2026."),
    ("placeholder", "{chat_history}"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

# Create the Agent
if tools:
    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
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