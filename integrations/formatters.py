"""Response formatting for different tool types."""

import json
import re
import ast
from typing import Tuple


def format_agent_output(raw_output: str) -> str:
    """
    Parse and format raw agent output, handling Gmail API responses and other formats.
    
    This function detects raw Gmail/API responses and formats them cleanly,
    extracting structured data and presenting it in a user-friendly way.
    
    Args:
        raw_output: Raw output string from the agent
        
    Returns:
        Formatted output string
    """
    # Check if this is a raw Gmail API output that needs formatting
    if "messageText" in raw_output or "labelIds" in raw_output:
        return _format_gmail_response(raw_output)
    
    return raw_output


def _extract_dict_from_string(output: str) -> Tuple[bool, dict]:
    """
    Extract and parse Python dict or JSON from output string.
    
    Args:
        output: String potentially containing dict/JSON
        
    Returns:
        Tuple of (success, parsed_dict)
    """
    try:
        # Try to extract and parse Python dict or JSON
        dict_match = re.search(r'\{.*\}', output, re.DOTALL)
        if dict_match:
            try:
                # First try JSON parsing
                raw_data = json.loads(dict_match.group())
                return True, raw_data
            except json.JSONDecodeError:
                # Fallback to ast.literal_eval for Python dict strings
                raw_data = ast.literal_eval(dict_match.group())
                return True, raw_data
    except Exception:
        pass
    
    return False, {}


def _format_gmail_response(output: str) -> str:
    """
    Format raw Gmail API response into user-friendly text.
    
    Args:
        output: Raw Gmail response
        
    Returns:
        Formatted output string
    """
    try:
        success, raw_data = _extract_dict_from_string(output)
        if not success:
            return output
        
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
            return formatted
        
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
                return formatted
        
        return output
    except Exception:
        return output
