"""
=== SCALABLE MULTI-TOOLKIT AI ORCHESTRATION ===

ARCHITECTURE:
1. DYNAMIC TOOLKIT LOADING
   - Add toolkits to line ~45: toolkits=["gmail", "googlecalendar", "slack", ...]
   - All connected toolkits automatically load their tools

2. GENERIC PARAMETER EXTRACTION
   - Parses tool descriptions to extract likely parameters
   - No hardcoding needed - works with any toolkit
   - Scales to 100+ tools automatically

3. SMART ERROR HANDLING
   - When tool fails, extracts missing fields from error message
   - Shows user exactly which parameters are missing
   - User can retry with correct parameters

4. UNIVERSAL AGENT PROMPT
   - Same prompt works for any toolkit
   - Agent reads tool descriptions to understand parameters
   - Guides agent to use EXACT tool names and formats

ADDING NEW TOOLKITS:
1. Go to Composio platform, connect the service (Slack, GitHub, etc.)
2. Edit main.py line ~45: toolkits=["gmail", "new_toolkit_name"]
3. That's it! The agent automatically has access to all new tools

SUPPORTED TOOLKITS:
- Gmail, Google Calendar, Google Drive, Google Docs
- Slack, Microsoft Outlook
- GitHub, Jira
- Notion, Trello, Asana
- ... and more!
"""

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
COMPOSIO_USER_ID = "pg-test-a40e9be6-01b3-4dc2-ba78-30d8c608e993"

try:
    # Try different toolkit names to find what works
    toolkit_names_to_try = [
        "gmail",
        "googlecalendar",
        "google_calendar", 
        "google-calendar",
        "calendar",
        "calendars",
        "google_calendars",
    ]
    
    print("\n📦 Testing toolkit names...")
    raw_tools = []
    working_toolkits = []
    
    for toolkit_name in toolkit_names_to_try:
        try:
            tools = client.tools.get(
                user_id=COMPOSIO_USER_ID,
                toolkits=[toolkit_name]
            )
            if tools and len(tools) > 0:
                raw_tools.extend(tools)
                working_toolkits.append(toolkit_name)
                print(f"  ✓ '{toolkit_name}': {len(tools)} tools")
        except Exception as e:
            pass
    
    print(f"✅ Total: {len(raw_tools)} tools")
    print(f"📝 Working toolkit names: {working_toolkits}")
    print(f"   → Copy this: toolkits={working_toolkits}\n")
    
    # Show how to add more toolkits
    print("📚 To add more toolkits, edit line ~45 and add to toolkit list:")
    print("   Available: gmail, googlecalendar, googledrive, slack, github, notion, jira, asana, trello, etc.")
    print("   (Make sure they're connected on Composio platform)\n")
    
    # Debug: Print individual tool names
    print("📋 Available tools:")
    calendar_tools = []
    for tool in raw_tools:
        print(f"   - {tool.name}")
        if "CALENDAR" in tool.name:
            calendar_tools.append(tool.name)
    
    # Helpful hint for calendar tools
    if calendar_tools:
        print(f"\n💡 Calendar tools available:")
        for cal_tool in calendar_tools[:10]:
            print(f"   • {cal_tool}")
        if len(calendar_tools) > 10:
            print(f"   ... and {len(calendar_tools) - 10} more")
    
    # FIX: Manually wrap tools to accept LangChain's argument format
    from langchain_core.tools import tool
    import re
    
    # Function to extract parameters from tool description
    def extract_params_from_description(description):
        """Extract likely parameters from tool description"""
        if not description:
            return []
        
        # Common patterns in descriptions
        patterns = [
            r'(?:requires?|needs?|parameters?)\s*:?\s*([^.]+)',  # "Requires: x, y, z"
            r'(?:pass|provide|input)\s*:?\s*([^.]+)',              # "Pass: x, y"
            r'\b(calendarId|calendar_id|eventId|event_id|message_id|messageId|userId|user_id)\b',  # Common field names
        ]
        
        params = set()
        for pattern in patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            for match in matches:
                # Clean up and split comma-separated values
                if isinstance(match, tuple):
                    match = match[0]
                items = re.split(r'[,\s]+', str(match))
                for item in items:
                    item = item.strip().strip('()[]{}')
                    if item and len(item) > 2:
                        params.add(item)
        
        return list(params)[:5]  # Return top 5
    
    tools = []
    tool_descriptions = {}  # Store descriptions for error help
    
    for raw_tool in raw_tools:
        # Store tool info for later error handling
        tool_descriptions[raw_tool.name] = raw_tool.description
        
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
                    
                    # Format tool responses nicely based on tool type
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
                    
                    # Format Google Calendar responses nicely
                    elif t.name.startswith("GOOGLE_CALENDAR_"):
                        try:
                            if isinstance(result, str):
                                result = json.loads(result)
                            
                            # Handle calendar events list
                            if isinstance(result, dict) and "items" in result:
                                events = result.get("items", [])
                                summary = f"📅 Found {len(events)} calendar events:\n\n"
                                for event in events[:5]:
                                    summary += f"Event: {event.get('summary', 'No title')}\n"
                                    summary += f"Time: {event.get('start', {}).get('dateTime', event.get('start', {}).get('date', 'TBD'))}\n"
                                    if event.get('description'):
                                        summary += f"Description: {event.get('description')[:80]}...\n"
                                    summary += "-" * 40 + "\n"
                                if len(events) > 5:
                                    summary += f"\n... and {len(events) - 5} more events"
                                return summary
                            else:
                                return str(result)
                        except Exception as e:
                            return str(result)
                    
                    
                    return str(result)
                except Exception as e:
                    # Smart error handling - extract missing fields from error
                    error_msg = str(e)
                    
                    # Try to extract missing field names from error
                    missing_fields = re.findall(r"'([^']+)'", error_msg)
                    
                    # Get parameter hints from tool description
                    tool_desc = tool_descriptions.get(t.name, "")
                    suggested_params = extract_params_from_description(tool_desc)
                    
                    error_response = f"❌ {t.name} failed\n\n"
                    error_response += f"Error: {error_msg[:200]}\n\n"
                    
                    if missing_fields:
                        error_response += f"💡 Missing fields: {', '.join(missing_fields[:5])}\n"
                    
                    if suggested_params:
                        error_response += f"💡 Suggested parameters: {', '.join(suggested_params)}\n"
                    else:
                        error_response += f"💡 Tool description: {tool_desc[:200]}...\n"
                    
                    return error_response
            
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

# 4. Dynamic Prompt - works with ANY toolkit
template = """
You are a helpful AI assistant running locally. Today is Feb 20, 2026.
You have access to many different tools across multiple platforms.

{tools}

CRITICAL INSTRUCTIONS:
1. To use a tool, you MUST use the exact format below - this is MANDATORY.
2. The "Action Input" MUST be a valid JSON object {{ }}.
3. Only use tools listed above (available: {tool_names}).
4. Use EXACT tool names from the list - do not modify or guess names.
5. Extract required parameters from each tool's DESCRIPTION above.
6. Common parameter patterns:
   - ID fields: Usually need "Id" or "id" suffix (e.g., eventId, calendarId, messageId)
   - List/Get operations: May need resource identifiers like "primary" for calendars
   - Primary ID is usually "primary" for Google services
7. When a tool fails, the error message will tell you which fields are missing.

Format (MUST follow exactly):
Question: the input question you must answer
Thought: I need to use a tool to solve this. Let me check the tool description for parameters.
Action: [Should be one of {tool_names}]
Action Input: {{"parameter1": "value1", "parameter2": "value2"}}
Observation: [Tool output will appear here]
... (repeat Thought/Action/Action Input/Observation as needed)
Thought: I now have the answer
Final Answer: [Your final response to the user]

Begin!

Question: {input}
Thought:{agent_scratchpad}
"""

prompt = PromptTemplate(
    template=template,
    input_variables=["tools", "tool_names", "input", "agent_scratchpad"]
)

# Verify prompt has all required variables
print(f"✅ Prompt variables: {prompt.input_variables}")

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