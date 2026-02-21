# 🧠 Nexus: Universal Local AI Agent Orchestrator

### A Privacy-First, Air-Gapped Backend for Dynamic App Integration

## 📋 Executive Summary

**Nexus** is a production-grade, local-first AI orchestration backend. Instead of hardcoding integrations for specific apps, Nexus utilizes a **Dynamic Tool Loading** architecture. It can seamlessly connect to and execute actions across 1,000+ external applications (Google Workspace, GitHub, Slack, Notion, CRMs) based strictly on user configuration and intent.

The system is architected to run the reasoning engine **100% Locally** using quantized Small Language Models (SLMs) like `Qwen 2.5 Coder` on consumer hardware. This ensures that the AI's "thought process" remains entirely private, with only explicit, authorized tool executions touching the cloud.

---

## 🏗️ System Architecture

Nexus follows a **Provider Pattern**, decoupling the local reasoning engine from the execution layer.

### Key Technical Decisions

- **Universal Tool Orchestration:** Powered by Composio, the backend dynamically loads toolkits (e.g., `github`, `gmail`, `slack`) at runtime. Users can swap or add new apps without altering the core reasoning logic.
    
- **Managed Authentication:** Eliminates brittle token management. OAuth2 flows, token refreshes, and API key management are handled securely via the Composio gateway, abstracting auth complexities away from the LLM.
    
- **Local-First AI:** Optimized for hardware constraints (e.g., RTX 3050 / 4GB VRAM) using `qwen2.5-coder:3b`, proving that high-utility, agentic workflows don't require massive GPU clusters.
    
- **Strict ReAct Protocol:** Implements robust "Reason + Act" loops via LangChain, forcing the local SLM to output strict JSON for reliable, deterministic API execution.
    

---

## 🚀 Core Capabilities

- **🔌 Plug-and-Play Integrations:** Supports seamless connection to any app in the Composio ecosystem (Productivity, DevOps, Social Media, CRMs). If it has an API, Nexus can control it.
    
- **🔒 Zero-Leakage Reasoning:** The LLM processes all contextual data and makes decisions locally. PII and sensitive workflows are never sent to third-party model providers like OpenAI or Anthropic.
    
- **🔄 Autonomous Error Correction:** If an external API rejects a request (e.g., missing parameters), the ReAct loop catches the error, adjusts the payload, and retries without user intervention.
    
- **⚡ API-First Design:** Exposes clean, RESTful FastAPI endpoints, making it trivial to attach custom frontends (React/Next.js, Streamlit, or Slack bots).
    

---

## 🛠️ Tech Stack

|**Component**|**Technology**|**Rationale**|
|---|---|---|
|**Backend API**|`FastAPI`|High-performance, async Python routing.|
|**Tool Gateway**|`Composio`|Enterprise-grade OAuth management and tool registry.|
|**Orchestration**|`LangChain`|Managing the ReAct loop, memory, and prompt templates.|
|**LLM Inference**|`Ollama`|Local inference server for quantized models.|
|**Model**|`Qwen 2.5 Coder`|Best-in-class syntax generation for reliable tool calling.|

---

## ⚡ Getting Started

### Prerequisites

- Python 3.10+
    
- [Ollama](https://ollama.com/) installed and running.
    
- A [Composio](https://composio.dev/) API Key.
    

### 1. Clone & Setup



```bash
git clone https://github.com/yourusername/nexus-agent.git
cd nexus-agent
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file (or set system variables):



```bash
export COMPOSIO_API_KEY="your_key_here"
```

### 3. Initialize the Local Brain

Pull the syntax-optimized SLM.



```bash
ollama pull qwen2.5-coder:3b
```

### 4. Connect Your Apps (Dynamic Tooling)

Authenticate the apps you want your agent to control. You can add any supported toolkit:



```bash
composio add gmail -e "default"
composio add github -e "default"
composio add slack -e "default"
```

### 5. Run the Engine

Bash

```
python main.py
```

_(Access the interactive Swagger UI at `http://localhost:8000/docs` to test endpoints)._

---

## 🔮 Roadmap

- [ ] **Entity Isolation:** Map distinct `user_id`s to unique Composio entities for multi-tenant SaaS deployments.
    
- [ ] **Long-Term Memory:** Integrate a vector store (ChromaDB/Pinecone) to persist user preferences across sessions.
    
- [ ] **Human-in-the-Loop (HITL):** Add interrupt nodes for sensitive actions (e.g., sending emails, deleting repositories) requiring explicit user approval.
    

---

## 📄 License

This project is open-source and available under the MIT License.