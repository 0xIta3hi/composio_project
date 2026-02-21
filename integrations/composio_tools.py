"""Composio integration and tool management."""

import re
import json
import os
from typing import List, Callable, Dict

from composio import Composio
from composio_langchain import LangchainProvider
from langchain_core.tools import tool


# Configuration
COMPOSIO_API_KEY = os.environ.get("COMPOSIO_API_KEY", "")
COMPOSIO_USER_ID = os.environ.get("COMPOSIO_USER_ID", "")

# Toolkit names to try
TOOLKIT_NAMES_TO_TRY = [
    "gmail",
    "googlecalendar",
    "google_calendar",
    "google-calendar",
    "calendar",
    "calendars",
    "google_calendars",
    "googledrive",
    "google_drive",
    "google-drive",
    "drive",
]


def extract_params_from_description(description: str) -> List[str]:
    """
    Extract likely parameters from tool description using regex patterns.
    
    Args:
        description: Tool description string
        
    Returns:
        List of likely parameter names
    """
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


def create_composio_client() -> Composio:
    """
    Initialize and return Composio client.
    
    Returns:
        Composio: Configured Composio client instance
    """
    print("1. Initializing Composio (New Provider Pattern)...")
    
    client = Composio(
        api_key=COMPOSIO_API_KEY,
        provider=LangchainProvider()
    )
    
    return client


def fetch_raw_tools(client: Composio) -> tuple[List, List]:
    """
    Fetch raw tools from Composio by trying various toolkit names.
    
    Args:
        client: Composio client instance
        
    Returns:
        Tuple of (raw_tools list, working_toolkits list)
    """
    print("2. Fetching Tools...")
    
    print("\n📦 Testing toolkit names...")
    raw_tools = []
    working_toolkits = []
    
    for toolkit_name in TOOLKIT_NAMES_TO_TRY:
        try:
            tools = client.tools.get(
                user_id=COMPOSIO_USER_ID,
                toolkits=[toolkit_name]
            )
            if tools and len(tools) > 0:
                raw_tools.extend(tools)
                working_toolkits.append(toolkit_name)
                print(f"  ✓ '{toolkit_name}': {len(tools)} tools")
        except Exception:
            pass
    
    print(f"\n✅ Total: {len(raw_tools)} tools")
    print(f"📝 Working toolkit names: {working_toolkits}")
    
    return raw_tools, working_toolkits


def print_tool_categories(raw_tools: List) -> None:
    """
    Print available tools organized by category.
    
    Args:
        raw_tools: List of raw tool objects
    """
    print("\n📋 Available tools:")
    calendar_tools = []
    drive_tools = []
    
    for tool_obj in raw_tools:
        print(f"   - {tool_obj.name}")
        if "CALENDAR" in tool_obj.name:
            calendar_tools.append(tool_obj.name)
        if "DRIVE" in tool_obj.name or "GDRIVE" in tool_obj.name:
            drive_tools.append(tool_obj.name)
    
    # Helpful hint for calendar tools
    if calendar_tools:
        print(f"\n💡 Calendar tools available:")
        for cal_tool in calendar_tools[:10]:
            print(f"   • {cal_tool}")
        if len(calendar_tools) > 10:
            print(f"   ... and {len(calendar_tools) - 10} more")
    
    # Helpful hint for drive tools
    if drive_tools:
        print(f"\n💡 Google Drive tools available:")
        for drive_tool in drive_tools[:10]:
            print(f"   • {drive_tool}")
        if len(drive_tools) > 10:
            print(f"   ... and {len(drive_tools) - 10} more")


def create_tool_wrapper(
    raw_tool,
    client: Composio,
    tool_descriptions: Dict[str, str]
) -> Callable:
    """
    Create a wrapped LangChain-compatible tool from a Composio tool.
    
    Args:
        raw_tool: Raw Composio tool object
        client: Composio client instance
        tool_descriptions: Dictionary of tool descriptions
        
    Returns:
        Wrapped tool callable
    """
    def create_wrapper(t):
        @tool
        def wrapped_tool(input_data: str) -> str:
            """Execute Composio tool"""
            try:
                args = json.loads(input_data) if isinstance(input_data, str) else input_data
                result = client.tools.execute(
                    slug=t.name,
                    arguments=args,
                    user_id=COMPOSIO_USER_ID,
                    dangerously_skip_version_check=True
                )
                
                # Format tool responses nicely based on tool type
                if t.name == "GMAIL_FETCH_EMAILS":
                    try:
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
                    except Exception:
                        return str(result)
                
                # Format Google Drive responses nicely
                elif t.name.startswith("GDRIVE_") or "drive" in t.name.lower():
                    try:
                        if isinstance(result, str):
                            result = json.loads(result)
                        
                        # Handle file/folder search results
                        if isinstance(result, dict) and "files" in result:
                            files = result.get("files", [])
                            summary = f"📁 Found {len(files)} items on Google Drive:\n\n"
                            for file in files[:10]:
                                file_type = "📄" if file.get('mimeType', '').startswith('text') else "📁" if 'folder' in file.get('mimeType', '').lower() else "📎"
                                summary += f"{file_type} {file.get('name', 'Unnamed')}\n"
                                if file.get('description'):
                                    summary += f"   Description: {file.get('description')[:60]}...\n"
                                summary += f"   ID: {file.get('id', 'N/A')}\n"
                                summary += "-" * 40 + "\n"
                            if len(files) > 10:
                                summary += f"\n... and {len(files) - 10} more items"
                            return summary
                        # Handle single file response
                        elif isinstance(result, dict) and "name" in result:
                            summary = f"📄 File: {result.get('name', 'Unknown')}\n"
                            summary += f"ID: {result.get('id', 'N/A')}\n"
                            summary += f"Type: {result.get('mimeType', 'N/A')}\n"
                            if result.get('webViewLink'):
                                summary += f"Link: {result.get('webViewLink')}\n"
                            return summary
                        else:
                            return str(result)
                    except Exception:
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
    
    return create_wrapper(raw_tool)


def get_tools() -> tuple[List, Composio]:
    """
    Initialize and return list of wrapped LangChain tools from Composio.
    
    Returns:
        Tuple of (wrapped_tools list, composio_client)
    """
    try:
        client = create_composio_client()
        raw_tools, working_toolkits = fetch_raw_tools(client)
        
        print_tool_categories(raw_tools)
        
        # Store tool descriptions for error handling
        tool_descriptions = {tool.name: tool.description for tool in raw_tools}
        
        # Create wrapped tools
        tools = []
        for raw_tool in raw_tools:
            wrapped = create_tool_wrapper(raw_tool, client, tool_descriptions)
            tools.append(wrapped)
        
        return tools, client
    
    except Exception as e:
        print(f"❌ Error fetching tools: {e}")
        return [], None
