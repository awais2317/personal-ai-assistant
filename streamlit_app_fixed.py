import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
from pathlib import Path

# Configure page
st.set_page_config(
    page_title="Personal AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API base URL
API_BASE = "http://localhost:8000/api/v1"

def check_api_health():
    """Check if API is running"""
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def send_chat_message(message, conversation_id=None, include_context=True):
    """Send a message to the chat API"""
    try:
        payload = {
            "message": message,
            "conversation_id": conversation_id,
            "include_context": include_context
        }
        response = requests.post(f"{API_BASE}/chat", json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error sending message: {str(e)}")
        return None

# Enhanced Chat Management Functions
def create_new_chat(title=None):
    """Create a new chat session"""
    try:
        payload = {"title": title} if title else {}
        response = requests.post(f"{API_BASE}/chat/new", json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error creating new chat: {str(e)}")
        return None

def get_chat_list(limit=20):
    """Get list of chat sessions"""
    try:
        response = requests.get(f"{API_BASE}/chat/list", params={"limit": limit})
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error getting chat list: {str(e)}")
        return None

def get_chat_history(chat_id):
    """Get chat history for a specific chat"""
    try:
        response = requests.get(f"{API_BASE}/chat/{chat_id}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error getting chat history: {str(e)}")
        return None

def send_message_to_chat(chat_id, message, document_id=None):
    """Send a message to a specific chat session"""
    try:
        payload = {
            "message": message,
            "document_id": document_id
        }
        response = requests.post(f"{API_BASE}/chat/{chat_id}/message", json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error sending message to chat: {str(e)}")
        return None

def update_chat_title(chat_id, title):
    """Update chat title"""
    try:
        response = requests.put(f"{API_BASE}/chat/{chat_id}/title", params={"title": title})
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error updating chat title: {str(e)}")
        return None

def delete_chat(chat_id):
    """Delete a chat session"""
    try:
        response = requests.delete(f"{API_BASE}/chat/{chat_id}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error deleting chat: {str(e)}")
        return None

def search_chats(query, limit=10):
    """Search chats by content"""
    try:
        response = requests.get(f"{API_BASE}/chats/search", params={"query": query, "limit": limit})
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error searching chats: {str(e)}")
        return None

def get_chat_suggestions(chat_id):
    """Get chat suggestions"""
    try:
        response = requests.get(f"{API_BASE}/chat/{chat_id}/suggestions")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error getting chat suggestions: {str(e)}")
        return None

def upload_document(file, custom_name=None):
    """Upload a document to the API"""
    try:
        files = {"file": (file.name, file, file.type)}
        data = {"custom_name": custom_name} if custom_name else {}
        
        response = requests.post(f"{API_BASE}/upload", files=files, data=data)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error uploading file: {str(e)}")
        return None

def get_documents():
    """Get list of uploaded documents"""
    try:
        response = requests.get(f"{API_BASE}/documents")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error retrieving documents: {str(e)}")
        return []

def search_documents(query, document_id=None, limit=10):
    """Search within documents"""
    try:
        payload = {
            "query": query,
            "document_id": document_id,
            "limit": limit
        }
        response = requests.post(f"{API_BASE}/search", json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error searching documents: {str(e)}")
        return None

def get_business_insights(query=None):
    """Get business insights"""
    try:
        payload = {"query": query} if query else {}
        response = requests.post(f"{API_BASE}/analyze/business", json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error getting business insights: {str(e)}")
        return None

def get_system_stats():
    """Get system statistics"""
    try:
        response = requests.get(f"{API_BASE}/stats")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error getting system stats: {str(e)}")
        return None

def main():
    """Main Streamlit application"""
    
    # Title and description
    st.title("🤖 Personal AI Assistant")
    st.markdown("Your intelligent companion for document analysis, business insights, and personal organization")
    
    # Check API status
    if not check_api_health():
        st.error("⚠️ API server is not running. Please start the FastAPI server first.")
        st.code("python main.py")
        return
    
    # Sidebar navigation (Fixed - removed Simple Chat and Documents)
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page:",
        ["💬 Enhanced Chat", "💼 Business Analysis", "📊 System Stats"]
    )
    
    if page == "💬 Enhanced Chat":
        enhanced_chat_page()
    elif page == "💼 Business Analysis":
        business_page()
    elif page == "📊 System Stats":
        stats_page()

def enhanced_chat_page():
    """Enhanced chat interface with session management"""
    st.header("💬 Enhanced Chat with Session Management")
    
    # Initialize session state for enhanced chat
    if "current_chat_id" not in st.session_state:
        st.session_state.current_chat_id = None
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = {}
    if "selected_document" not in st.session_state:
        st.session_state.selected_document = None
    
    # Sidebar for chat management
    with st.sidebar:
        st.subheader("🗂️ Chat Management")
        
        # Create new chat
        with st.expander("➕ New Chat", expanded=False):
            new_chat_title = st.text_input("Chat Title (optional)", key="new_chat_title")
            if st.button("Create New Chat", key="create_chat"):
                result = create_new_chat(new_chat_title if new_chat_title else None)
                if result and result.get("success"):
                    st.session_state.current_chat_id = result["chat_id"]
                    st.session_state.chat_messages[result["chat_id"]] = []
                    st.success(f"Created new chat: {result['title']}")
                    st.rerun()
        
        # Document upload section
        st.subheader("📤 Upload Documents")
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=['txt', 'pdf', 'docx', 'doc', 'xlsx', 'xls', 'csv', 'md'],
            help="Supported formats: TXT, PDF, DOCX, XLSX, CSV, MD"
        )
        
        if uploaded_file and st.button("Upload Document"):
            with st.spinner("Uploading document..."):
                result = upload_document(uploaded_file)
                if result and result.get("success"):
                    st.success(f"Document uploaded successfully!")
                    st.info(f"Created {result.get('chunks_created', 0)} chunks")
        
        # Chat history
        st.subheader("📜 Chat History")
        chat_list_data = get_chat_list(limit=50)
        
        if chat_list_data and chat_list_data.get("success"):
            chats = chat_list_data.get("chats", [])
            
            # Search chats
            search_query = st.text_input("🔍 Search chats...", key="chat_search")
            if search_query:
                search_results = search_chats(search_query)
                if search_results and search_results.get("success"):
                    chats = search_results.get("results", [])
            
            # Display chats
            for chat in chats[:20]:  # Limit to 20 for performance
                chat_id = chat.get("chat_id")
                title = chat.get("title", f"Chat {chat_id[:8]}")
                message_count = chat.get("message_count", 0)
                
                # Chat selection button
                if st.button(
                    f"💬 {title} ({message_count} msgs)", 
                    key=f"chat_{chat_id}",
                    help=f"Created: {chat.get('created_at', 'Unknown')}"
                ):
                    st.session_state.current_chat_id = chat_id
                    # Load chat history
                    chat_history = get_chat_history(chat_id)
                    if chat_history and chat_history.get("success"):
                        messages = chat_history["chat"]["messages"]
                        st.session_state.chat_messages[chat_id] = messages
                    st.rerun()
                
                # Chat management buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🗑️", key=f"del_{chat_id}", help="Delete chat"):
                        if delete_chat(chat_id):
                            st.success("Chat deleted!")
                            if st.session_state.current_chat_id == chat_id:
                                st.session_state.current_chat_id = None
                            st.rerun()
                
                with col2:
                    if st.button("✏️", key=f"edit_{chat_id}", help="Edit title"):
                        st.session_state[f"editing_{chat_id}"] = True
                
                # Title editing
                if st.session_state.get(f"editing_{chat_id}", False):
                    new_title = st.text_input(
                        "New title:", 
                        value=title,
                        key=f"title_{chat_id}"
                    )
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅", key=f"save_{chat_id}"):
                            if update_chat_title(chat_id, new_title):
                                st.success("Title updated!")
                                st.session_state[f"editing_{chat_id}"] = False
                                st.rerun()
                    with col2:
                        if st.button("❌", key=f"cancel_{chat_id}"):
                            st.session_state[f"editing_{chat_id}"] = False
                            st.rerun()
        
        # Document selection for context
        st.subheader("📄 Document Context")
        documents = get_documents()
        if documents:
            doc_options = {"None": None}
            for doc in documents:
                doc_options[f"{doc['filename']} ({doc['type']})"] = doc['document_id']
            
            selected_doc_name = st.selectbox(
                "Select document for context:",
                options=list(doc_options.keys()),
                key="doc_selector"
            )
            st.session_state.selected_document = doc_options[selected_doc_name]
    
    # Main chat interface
    if st.session_state.current_chat_id:
        st.subheader(f"Current Chat: {st.session_state.current_chat_id[:8]}...")
        
        # Display current chat messages
        current_messages = st.session_state.chat_messages.get(st.session_state.current_chat_id, [])
        
        # Create a container for messages
        message_container = st.container()
        
        with message_container:
            for message in current_messages:
                role = message.get("role", "user")
                content = message.get("content", "")
                
                with st.chat_message(role):
                    st.markdown(content)
                    
                    # Show metadata for assistant messages (Fixed the error)
                    if role == "assistant" and "metadata" in message:
                        metadata = message["metadata"]
                        context_docs = metadata.get("context_documents", [])
                        # Fix: Ensure context_documents is a list before joining
                        if isinstance(context_docs, list) and context_docs:
                            st.caption(f"📄 Used documents: {', '.join(context_docs)}")
                        elif context_docs:  # If it's a string or other type
                            st.caption(f"📄 Used documents: {context_docs}")
                        
                        response_type = metadata.get("response_type", "general")
                        if response_type != "general":
                            st.caption(f"🏷️ Response type: {response_type}")
        
        # Chat input
        if prompt := st.chat_input("Ask me anything..."):
            # Add user message to display
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Update session state
            if st.session_state.current_chat_id not in st.session_state.chat_messages:
                st.session_state.chat_messages[st.session_state.current_chat_id] = []
            
            st.session_state.chat_messages[st.session_state.current_chat_id].append({
                "role": "user",
                "content": prompt
            })
            
            # Get AI response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = send_message_to_chat(
                        st.session_state.current_chat_id,
                        prompt,
                        st.session_state.selected_document
                    )
                    
                    if response and response.get("success"):
                        ai_response = response["response"]
                        st.markdown(ai_response)
                        
                        # Show context information (Fixed the error)
                        context_docs = response.get("context_documents", [])
                        if isinstance(context_docs, list) and context_docs:
                            st.caption(f"📄 Used documents: {', '.join(context_docs)}")
                        elif context_docs:  # If it's a string or other type
                            st.caption(f"📄 Used documents: {context_docs}")
                        
                        response_type = response.get("response_type", "general")
                        if response_type != "general":
                            st.caption(f"🏷️ Response type: {response_type}")
                        
                        # Show suggestions
                        suggestions = response.get("suggestions", [])
                        if suggestions:
                            st.subheader("💡 Suggested Questions:")
                            for i, suggestion in enumerate(suggestions[:3]):  # Show top 3
                                if st.button(suggestion, key=f"suggestion_{i}"):
                                    # Auto-fill the suggestion
                                    st.session_state.suggestion_clicked = suggestion
                        
                        # Add assistant message to session state (Fixed metadata structure)
                        st.session_state.chat_messages[st.session_state.current_chat_id].append({
                            "role": "assistant",
                            "content": ai_response,
                            "metadata": {
                                "context_documents": context_docs,
                                "response_type": response_type,
                                "timestamp": response.get("timestamp")
                            }
                        })
                    else:
                        st.error("Failed to get response from AI assistant")
        
        # Handle suggestion clicks
        if hasattr(st.session_state, 'suggestion_clicked'):
            st.text_input("Suggested question:", value=st.session_state.suggestion_clicked, key="suggestion_input")
            del st.session_state.suggestion_clicked
    
    else:
        st.info("👈 Create a new chat or select an existing one from the sidebar to start chatting!")
        
        # Quick start options
        st.subheader("🚀 Quick Start")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💼 Business Analysis Chat"):
                result = create_new_chat("Business Analysis")
                if result and result.get("success"):
                    st.session_state.current_chat_id = result["chat_id"]
                    st.session_state.chat_messages[result["chat_id"]] = []
                    st.rerun()
        
        with col2:
            if st.button("📚 Document Q&A Chat"):
                result = create_new_chat("Document Q&A")
                if result and result.get("success"):
                    st.session_state.current_chat_id = result["chat_id"]
                    st.session_state.chat_messages[result["chat_id"]] = []
                    st.rerun()
        
        with col3:
            if st.button("🎯 General Purpose Chat"):
                result = create_new_chat("General Chat")
                if result and result.get("success"):
                    st.session_state.current_chat_id = result["chat_id"]
                    st.session_state.chat_messages[result["chat_id"]] = []
                    st.rerun()

def business_page():
    """Business analysis page"""
    st.header("💼 Business Analysis & Insights")
    
    # Business query input
    st.subheader("📊 Business Query")
    business_query = st.text_area(
        "Ask a business question or request analysis:",
        placeholder="e.g., 'Analyze my expenses for this month' or 'Show me revenue trends'"
    )
    
    if st.button("🔍 Analyze", key="business_analyze"):
        if business_query:
            with st.spinner("Analyzing..."):
                insights = get_business_insights(business_query)
                if insights:
                    st.success("Analysis complete!")
                    st.write(insights)
        else:
            st.warning("Please enter a business query")
    
    # Quick business actions
    st.subheader("⚡ Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📈 Revenue Analysis"):
            with st.spinner("Analyzing revenue..."):
                insights = get_business_insights("Analyze revenue trends and patterns")
                if insights:
                    st.write(insights)
    
    with col2:
        if st.button("💰 Expense Breakdown"):
            with st.spinner("Analyzing expenses..."):
                insights = get_business_insights("Breakdown and categorize expenses")
                if insights:
                    st.write(insights)
    
    with col3:
        if st.button("🔮 Forecasting"):
            with st.spinner("Generating forecast..."):
                insights = get_business_insights("Generate financial forecasts based on historical data")
                if insights:
                    st.write(insights)

def stats_page():
    """System statistics page"""
    st.header("📊 System Statistics")
    
    # Get and display system stats
    with st.spinner("Loading system statistics..."):
        stats = get_system_stats()
        if stats:
            # Display stats in columns
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Documents", stats.get("document_count", 0))
            
            with col2:
                st.metric("Total Chunks", stats.get("chunk_count", 0))
            
            with col3:
                st.metric("Chat Sessions", stats.get("chat_count", 0))
            
            with col4:
                st.metric("Storage Used", f"{stats.get('storage_mb', 0):.1f} MB")
            
            # Additional stats
            st.subheader("📈 Detailed Statistics")
            if "document_types" in stats:
                st.write("**Document Types:**")
                for doc_type, count in stats["document_types"].items():
                    st.write(f"- {doc_type}: {count}")
            
            if "recent_activity" in stats:
                st.write("**Recent Activity:**")
                for activity in stats["recent_activity"][:5]:
                    st.write(f"- {activity}")
        
        else:
            st.error("Failed to load system statistics")

if __name__ == "__main__":
    main()
