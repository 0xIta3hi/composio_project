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
                        user_id="pg-test-a40e9be6-01b3-4dc2-ba78-30d8c608e993",
                        dangerously_skip_version_check=True
                    )
                    
                    # Format Gmail responses nicely
                    if t.name == "GMAIL_FETCH_EMAILS":
                        try:
                            import json
                            
                            # Parse result - could be dict or JSON string
                            if isinstance(result, str):
                                result = json.loads(result)
                            
                            # Debug info in response
                            debug_info = f"🔍 DEBUG:\n"
                            debug_info += f"  Result type: {type(result)}\n"
                            debug_info += f"  Result keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}\n"
                            
                            data = result.get("data", {})
                            debug_info += f"  Data type: {type(data)}\n"
                            debug_info += f"  Data keys: {list(data.keys()) if isinstance(data, dict) else 'N/A'}\n"
                            
                            # Try to extract emails from different possible locations
                            emails = None
                            
                            # Method 1: data.emails
                            if isinstance(data, dict) and "emails" in data:
                                emails = data.get("emails", [])
                                debug_info += f"  ✓ Found emails in data['emails']: {len(emails)} items\n"
                            
                            # Method 2: data is a list
                            elif isinstance(data, list):
                                emails = data
                                debug_info += f"  ✓ Data is a list: {len(emails)} items\n"
                            
                            # Method 3: Check all keys in data
                            elif isinstance(data, dict):
                                debug_info += f"  Data content preview: {str(data)[:500]}\n"
                                for key, value in data.items():
                                    if isinstance(value, list) and value:
                                        debug_info += f"    Found list at data['{key}']: {len(value)} items\n"
                                        if key not in ["nextPageToken"]:
                                            emails = value
                                            break
                            
                            if emails is None:
                                emails = []
                            
                            summary = debug_info + "\n" + "="*50 + "\n\n"
                            
                            if emails:
                                summary += f"📧 Found {len(emails)} emails:\n\n"
                                for email in emails[:3]:  # Show first 3
                                    summary += f"From: {email.get('sender', 'Unknown')}\n"
                                    summary += f"Subject: {email.get('subject', 'No subject')}\n"
                                    preview = email.get('preview', {}).get('body', '')[:80] if isinstance(email.get('preview'), dict) else str(email.get('preview', ''))[:80]
                                    summary += f"Preview: {preview}...\n"
                                    summary += "-" * 40 + "\n"
                                if len(emails) > 3:
                                    summary += f"... and {len(emails) - 3} more emails"
                            else:
                                summary += "❌ No emails found\n"
                            
                            return summary
                        except Exception as e:
                            import traceback
                            return f"❌ Email error: {str(e)}\n{traceback.format_exc()}\n\nResult: {str(result)[:500]}"
                    
                    
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
You are a helpful AI assistant running locally. Today is Feb 20, 2026.
You have access to the following tools:

{tools}

CRITICAL INSTRUCTIONS:
1. To use a tool, you MUST use the exact format below.
2. The "Action Input" MUST be a valid JSON object.
3. Do not invent tools. Only use the ones listed.
4. For GMAIL_FETCH_EMAILS: Pass {{"max_results": 10}} to get all emails, not just unread ones.

Format:
Question: the input question you must answer
Thought: I need to use a tool to get information.
Action: the action to take, should be one of [{tool_names}]
Action Input: {{ "max_results": 10 }}
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
        
        # Get the final answer
        output = result.get("output", "")
        
        # Clean up raw Gmail responses if they appear in the output
        if "messageText" in output or "labelIds" in output:
            # This is raw Gmail API output, parse and format it
            try:
                import json
                import re
                import ast
                
                # Try to extract and parse Python dict or JSON
                dict_match = re.search(r'\{.*\}', output, re.DOTALL)
                if dict_match:
                    try:
                        # First try JSON parsing
                        raw_data = json.loads(dict_match.group())
                    except json.JSONDecodeError:
                        # Fallback to ast.literal_eval for Python dict strings
                        raw_data = ast.literal_eval(dict_match.group())
                    
                    # Handle single email response
                    if "sender" in raw_data and "subject" in raw_data:
                        formatted = f"📧 Email found:\n\n"
                        formatted += f"From: {raw_data.get('sender', 'Unknown')}\n"
                        formatted += f"Subject: {raw_data.get('subject', 'No subject')}\n"
                        formatted += f"To: {raw_data.get('to', 'Unknown')}\n"
                        message_text = raw_data.get('messageText', '')
                        preview = raw_data.get('preview', {})
                        if isinstance(preview, dict):
                            preview_text = preview.get('body', '')[:150]
                        else:
                            preview_text = str(message_text)[:150]
                        formatted += f"Preview: {preview_text}...\n"
                        output = formatted
                    
                    # Handle email list response
                    else:
                        emails = raw_data.get("data", {}).get("emails", []) or \
                                 raw_data.get("emails", []) or []
                        
                        if emails:
                            formatted = f"📧 Found {len(emails)} emails:\n\n"
                            for email in emails[:5]:
                                formatted += f"From: {email.get('sender', 'Unknown')}\n"
                                formatted += f"Subject: {email.get('subject', 'No subject')}\n"
                                preview = email.get('preview', {}).get('body', '')[:100] if isinstance(email.get('preview'), dict) else str(email.get('preview', ''))[:100]
                                formatted += f"Preview: {preview}...\n"
                                formatted += "-" * 50 + "\n"
                            if len(emails) > 5:
                                formatted += f"\n... and {len(emails) - 5} more emails"
                            output = formatted
            except Exception as e:
                print(f"⚠️ Formatter error: {e}")
                pass  # If parsing fails, return original output
        
        return {"reply": output}
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

# --- RUNNER ---
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)