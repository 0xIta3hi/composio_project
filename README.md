# Autonomous Local AI Agent

### A Privacy-First, Air-Gapped Capable Email & Calendar Assistant

## 📋 Executive Summary

**Nexus** is a vertical slice of a next-generation AI Personal Assistant. Unlike standard chatbots, Nexus possesses **Agentic Capabilities**—it can reason, plan, and execute actions in the real world (reading emails, checking calendars) using a secure authentication layer.

The system is architected to run **100% Locally** using quantized Small Language Models (SLMs) like `Qwen 2.5 Coder`, proving that high-utility AI agents do not require massive cloud dependencies or GPU farms.

### Key Technical Decisions

- **Local-First AI:** Optimized to run on consumer hardware (RTX 3050 / 4GB VRAM) using `qwen2.5-coder:3b`.
    
- **Strict Tooling Protocol:** Utilizes **Composio** for managed OAuth2 authentication, eliminating the need for brittle token maintenance.
    
- **ReAct Pattern:** Implements "Reason + Act" loops, allowing the agent to self-correct if an API call fails or returns unexpected data.
    
- **API-First Design:** Backend is fully decoupled from the frontend, allowing for future React/Next.js integrations.

## 🚀 Features

- **📧 Autonomous Email Management:** Can fetch, filter, and summarize emails without user intervention.
    
- **📅 Calendar Intelligence:** Checks availability and cross-references dates naturally.
    
- **🔒 Privacy Centric:** All reasoning happens locally. Only specific API calls leave the machine.
    
- **⚡ Zero-Latency UI:** Streamlit frontend providing real-time feedback on the agent's "Thought Process."


Note: The Backend is build so as to allow user to connect any app of their choice they want ( as long as it is in the composio ToolKit )
