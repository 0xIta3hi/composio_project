"""
=== SCALABLE MULTI-TOOLKIT AI ORCHESTRATION ===

Modular Production-Grade Architecture

STRUCTURE:
- core/llm.py: LLM initialization (Qwen 2.5 Coder)
- core/prompts.py: ReAct prompt templates
- integrations/composio_tools.py: Composio toolkit loading and tool wrapping
- integrations/formatters.py: Response formatting and parsing
- api/routes.py: FastAPI routes and chat endpoint

CONFIGURATION:
1. Set environment variables:
   - COMPOSIO_API_KEY: Your Composio API key
   - COMPOSIO_USER_ID: Your Composio user ID

2. To add more toolkits, edit integrations/composio_tools.py:
   - Add toolkit names to TOOLKIT_NAMES_TO_TRY list
   - Make sure services are connected on Composio platform

SUPPORTED TOOLKITS:
- Gmail, Google Calendar, Google Drive, Google Docs
- Slack, Microsoft Outlook
- GitHub, Jira
- Notion, Trello, Asana
- ... and more!
"""

import uvicorn
from fastapi import FastAPI

from api.routes import router


# Create FastAPI app
app = FastAPI(
    title="AI Orchestration API",
    description="Multi-toolkit AI agent powered by LangChain + Composio + Qwen",
    version="1.0.0"
)

# Include routes
app.include_router(router, tags=["chat"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    print(__doc__)
    uvicorn.run(app, host="0.0.0.0", port=8000)
