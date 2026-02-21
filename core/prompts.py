"""Prompt templates for the ReAct agent."""

from langchain_core.prompts import PromptTemplate


REACT_PROMPT_TEMPLATE = """
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


def get_prompt() -> PromptTemplate:
    """
    Create and return the ReAct prompt template.
    
    Returns:
        PromptTemplate: Configured prompt with all required variables
    """
    prompt = PromptTemplate(
        template=REACT_PROMPT_TEMPLATE,
        input_variables=["tools", "tool_names", "input", "agent_scratchpad"]
    )
    
    print(f"✅ Prompt variables: {prompt.input_variables}")
    
    return prompt
