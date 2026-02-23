"""
Nexus AI | Local Agent - Streamlit Frontend
Professional UI for local AI orchestration with Qwen 2.5 Coder + Composio
"""

import streamlit as st
import requests
import json
from typing import Dict, List

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="Nexus AI | Local Agent",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================
if "messages" not in st.session_state:
    st.session_state.messages: List[Dict[str, str]] = []

# ============================================================================
# SIDEBAR - SYSTEM STATUS
# ============================================================================
with st.sidebar:
    st.header("🔧 System Status")
    
    # Visual indicators
    st.success("✅ **Qwen 2.5 Coder (Local)** - Running")
    st.info("🔐 **Composio OAuth (Air-gapped)** - Ready")
    
    st.divider()
    
    # Information section
    st.subheader("📊 About This System")
    st.markdown("""
    **Nexus AI** is a production-grade local intelligence orchestration system:
    
    - 🧠 **Qwen 2.5 Coder** - Local LLM (zero cloud dependency)
    - 🛠️ **Composio** - Multi-toolkit integration platform
    - ⛓️ **LangChain** - Agent reasoning framework
    - ⚡ **Streamlit** - Real-time web interface
    
    **Connected Toolkits:**
    - 📧 Gmail (email management)
    - 📅 Google Calendar (scheduling)
    - 📁 Google Drive (file operations)
    - ... extensible architecture for more
    """)

# ============================================================================
# MAIN CONTENT - CHAT INTERFACE
# ============================================================================
st.title("⚡ Nexus AI")
st.subheader("Local Intelligence Agent")
st.markdown("---")

# Display existing chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input field
user_input = st.chat_input("Ask me anything... (Enter to send)")

if user_input:
    # Step 1: Add user message to session state and display immediately
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })
    
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # Step 2: Show loading indicator while waiting for backend response
    with st.spinner("🤖 Agent is reasoning and executing tools..."):
        try:
            # Step 3: Make POST request to FastAPI backend
            response = requests.post(
                "http://localhost:8000/chat",
                json={"message": user_input},
                timeout=30
            )
            
            # Step 4: Handle successful response
            if response.status_code == 200:
                response_data = response.json()
                assistant_reply = response_data.get("reply", "No response received.")
                
                # Step 5: Add assistant response to session state and display
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": assistant_reply
                })
                
                with st.chat_message("assistant"):
                    st.markdown(assistant_reply)
            
            else:
                # Handle HTTP errors from backend
                error_msg = f"❌ Backend returned error (HTTP {response.status_code})"
                st.error(error_msg)
        
        # Step 6: Graceful error handling
        except requests.exceptions.ConnectionError:
            error_message = (
                "❌ **Backend Connection Failed**\n\n"
                "The FastAPI server is not running. Please start it with:\n\n"
                "```bash\n"
                "cd d:\\Projects\\AI_Projects\\AI_orchastration\n"
                "python main.py\n"
                "```\n\n"
                "The server will start on `http://localhost:8000`"
            )
            st.error(error_message)
        
        except requests.exceptions.Timeout:
            st.error(
                "⏱️ **Request Timeout**\n\n"
                "The backend is taking longer than expected. "
                "It might be processing a complex task with multiple tool calls."
            )
        
        except requests.exceptions.RequestException as e:
            st.error(f"❌ **Request Error**: {str(e)}")
        
        except json.JSONDecodeError:
            st.error("❌ **Invalid Response Format** - Backend returned malformed JSON")
        
        except KeyError:
            st.error("❌ **Invalid Response Structure** - Missing 'reply' field in response")
        
        except Exception as e:
            st.error(f"❌ **Unexpected Error**: {str(e)}")

# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.caption(
    "🚀 Nexus AI | Built with Streamlit, LangChain, Composio, and Qwen 2.5 Coder\n"
    "💡 Tip: Check the sidebar for system status and supported toolkits"
)
