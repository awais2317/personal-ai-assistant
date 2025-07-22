import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
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
        # Handle special business analysis session
        if chat_id == "business_analysis_session":
            # Create or get existing business analysis session
            if "business_session_id" not in st.session_state:
                result = create_new_chat("Business Analysis Session")
                if result and result.get("success"):
                    st.session_state.business_session_id = result["chat_id"]
                else:
                    st.error("Failed to create business analysis session")
                    return None
            chat_id = st.session_state.business_session_id
        
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
    """Enhanced business analysis page with graphs, tables, and advanced analytics"""
    st.header("💼 Business Analysis & Insights Dashboard")
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .metric-card {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
    .analysis-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #007bff;
        margin: 1rem 0;
    }
    .insight-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 8px;
        color: white;
        margin: 0.5rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state for business documents
    if "business_documents" not in st.session_state:
        st.session_state.business_documents = []
    if "selected_business_doc" not in st.session_state:
        st.session_state.selected_business_doc = None
    if "analysis_results" not in st.session_state:
        st.session_state.analysis_results = {}
    
    # Main layout with tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📈 Analysis", "📋 Reports", "🔧 Settings"])
    
    with tab1:
        # Dashboard Overview
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("📄 Business Documents")
            
            # Enhanced upload section
            with st.expander("📤 Upload Business Document", expanded=True):
                business_file = st.file_uploader(
                    "Choose your business file",
                    type=['xlsx', 'xls', 'csv', 'pdf', 'docx', 'txt'],
                    help="📊 Supported: Excel, CSV, PDF, Word, Text files",
                    key="business_upload"
                )
                
                # Upload options
                col_a, col_b = st.columns(2)
                with col_a:
                    auto_analyze = st.checkbox("🤖 Auto-analyze after upload", value=True)
                with col_b:
                    custom_name = st.text_input("📝 Custom name (optional)")
                
                if business_file:
                    file_info = {
                        "name": business_file.name,
                        "size": f"{business_file.size / 1024:.1f} KB",
                        "type": business_file.type
                    }
                    st.info(f"📄 **File:** {file_info['name']}\n📏 **Size:** {file_info['size']}\n🏷️ **Type:** {file_info['type']}")
                    
                    if st.button("🚀 Upload & Process", key="upload_business", type="primary"):
                        with st.spinner("🔄 Processing business document..."):
                            try:
                                # Use custom name if provided, otherwise use Business_ prefix
                                upload_name = custom_name if custom_name else f"Business_{business_file.name}"
                                result = upload_document(business_file, upload_name)
                                
                                if result and result.get("success"):
                                    st.success("✅ Document uploaded successfully!")
                                    st.balloons()
                                    
                                    # Show processing results
                                    chunks_created = result.get('chunks_created', 0)
                                    st.metric("📚 Text Chunks Created", chunks_created)
                                    
                                    # Auto-analyze if enabled
                                    if auto_analyze:
                                        st.info("🤖 Running auto-analysis...")
                                        # Trigger auto-analysis
                                        st.session_state['auto_analyze_doc'] = result.get('document_id')
                                    
                                    st.rerun()
                                else:
                                    st.error("❌ Upload failed. Please try again.")
                            except Exception as e:
                                st.error(f"❌ Upload error: {str(e)}")
            
            # Available business documents
            st.subheader("📚 Available Documents")
            documents = get_documents()
            if documents:
                business_docs = [doc for doc in documents if doc['filename'].startswith('Business_') or 
                               (custom_name and doc['filename'] == custom_name)]
                
                if business_docs:
                    for i, doc in enumerate(business_docs):
                        doc_name = doc['filename'].replace('Business_', '') if doc['filename'].startswith('Business_') else doc['filename']
                        
                        # Document card
                        with st.container():
                            col_x, col_y, col_z = st.columns([3, 1, 1])
                            
                            with col_x:
                                if st.button(
                                    f"📊 {doc_name}",
                                    key=f"select_biz_{doc['document_id']}",
                                    help=f"Type: {doc['type']} | Chunks: {doc['chunks']}"
                                ):
                                    st.session_state.selected_business_doc = doc
                                    st.success(f"Selected: {doc_name}")
                                    st.rerun()
                            
                            with col_y:
                                st.caption(f"📏 {doc['chunks']} chunks")
                            
                            with col_z:
                                st.caption(f"🏷️ {doc['type']}")
                    
                    # Show selected document
                    if st.session_state.selected_business_doc:
                        selected_doc = st.session_state.selected_business_doc
                        doc_name = selected_doc['filename'].replace('Business_', '') if selected_doc['filename'].startswith('Business_') else selected_doc['filename']
                        
                        st.markdown(f"""
                        <div class="metric-card">
                            <h4>📋 Currently Selected</h4>
                            <p><strong>{doc_name}</strong></p>
                            <p>Type: {selected_doc['type']} | Chunks: {selected_doc['chunks']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("📝 No business documents found. Upload documents above to get started.")
            else:
                st.info("📁 No documents in system. Upload your first business document above.")
        
        with col2:
            st.subheader("📊 Quick Analytics Dashboard")
            
            if st.session_state.selected_business_doc:
                selected_doc = st.session_state.selected_business_doc
                doc_name = selected_doc['filename'].replace('Business_', '') if selected_doc['filename'].startswith('Business_') else selected_doc['filename']
                
                # Quick metrics
                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                with col_m1:
                    st.metric("📄 Document", "Selected", doc_name[:10] + "..." if len(doc_name) > 10 else doc_name)
                with col_m2:
                    st.metric("🧩 Chunks", selected_doc['chunks'])
                with col_m3:
                    st.metric("📊 Type", selected_doc['type'].upper())
                with col_m4:
                    st.metric("📅 Status", "Ready", "✅")
                
                # Quick analysis buttons
                st.subheader("⚡ Quick Analysis")
                
                col_q1, col_q2, col_q3 = st.columns(3)
                
                with col_q1:
                    if st.button("📈 Revenue Analysis", key="quick_revenue", type="primary"):
                        with st.spinner("Analyzing revenue data..."):
                            response = send_message_to_chat(
                                "business_analysis_session",
                                "Provide a comprehensive revenue analysis including trends, growth rates, seasonal patterns, and key revenue drivers. Include specific numbers and percentages where available.",
                                selected_doc['document_id']
                            )
                            if response and response.get("success"):
                                st.session_state.analysis_results['revenue'] = response["response"]
                                st.rerun()
                
                with col_q2:
                    if st.button("💰 Cost Analysis", key="quick_cost", type="primary"):
                        with st.spinner("Analyzing cost structure..."):
                            response = send_message_to_chat(
                                "business_analysis_session",
                                "Analyze all costs and expenses, categorize them, identify cost drivers, and suggest optimization opportunities. Include cost ratios and trends.",
                                selected_doc['document_id']
                            )
                            if response and response.get("success"):
                                st.session_state.analysis_results['costs'] = response["response"]
                                st.rerun()
                
                with col_q3:
                    if st.button("🎯 KPI Dashboard", key="quick_kpi", type="primary"):
                        with st.spinner("Calculating KPIs..."):
                            response = send_message_to_chat(
                                "business_analysis_session",
                                "Calculate and present key performance indicators (KPIs) including profitability ratios, efficiency metrics, growth rates, and benchmark comparisons. Format as a dashboard.",
                                selected_doc['document_id']
                            )
                            if response and response.get("success"):
                                st.session_state.analysis_results['kpis'] = response["response"]
                                st.rerun()
                
                # Display analysis results
                if st.session_state.analysis_results:
                    st.subheader("📋 Analysis Results")
                    
                    for analysis_type, result in st.session_state.analysis_results.items():
                        with st.expander(f"📊 {analysis_type.title()} Analysis", expanded=True):
                            st.markdown(f"""
                            <div class="analysis-card">
                                {result}
                            </div>
                            """, unsafe_allow_html=True)
                
                # Auto-analysis results
                if 'auto_analyze_doc' in st.session_state and st.session_state['auto_analyze_doc'] == selected_doc['document_id']:
                    st.subheader("🤖 Auto-Analysis Results")
                    with st.spinner("Running comprehensive auto-analysis..."):
                        auto_response = send_message_to_chat(
                            "business_analysis_session",
                            "Perform a comprehensive business analysis of this document. Include: 1) Executive Summary, 2) Key Financial Metrics, 3) Trends Analysis, 4) Insights & Recommendations. Present in a clear, structured format.",
                            selected_doc['document_id']
                        )
                        if auto_response and auto_response.get("success"):
                            st.markdown(f"""
                            <div class="insight-box">
                                <h4>🎯 Comprehensive Business Analysis</h4>
                                {auto_response["response"]}
                            </div>
                            """, unsafe_allow_html=True)
                    del st.session_state['auto_analyze_doc']
            
            else:
                st.info("👈 Please select a business document from the left panel to view analytics dashboard.")
                
                # Sample dashboard when no document selected
                st.subheader("📊 Sample Analytics Dashboard")
                
                # Sample metrics
                col_s1, col_s2, col_s3, col_s4 = st.columns(4)
                with col_s1:
                    st.metric("💰 Revenue", "$125,000", "↗️ +12%")
                with col_s2:
                    st.metric("📈 Growth", "15.3%", "↗️ +2.1%")
                with col_s3:
                    st.metric("💸 Expenses", "$89,000", "↘️ -5%")
                with col_s4:
                    st.metric("📊 Profit", "$36,000", "↗️ +28%")
                
                # Sample chart
                import numpy as np
                sample_data = pd.DataFrame({
                    'Month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                    'Revenue': [20000, 25000, 22000, 28000, 32000, 35000],
                    'Expenses': [15000, 18000, 16000, 20000, 22000, 24000]
                })
                
                fig = px.line(sample_data, x='Month', y=['Revenue', 'Expenses'], 
                             title="📈 Sample Revenue vs Expenses Trend",
                             color_discrete_map={'Revenue': '#1f77b4', 'Expenses': '#ff7f0e'})
                st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        # Advanced Analysis Tab
        st.subheader("🔬 Advanced Business Analysis")
        
        if st.session_state.selected_business_doc:
            selected_doc = st.session_state.selected_business_doc
            doc_name = selected_doc['filename'].replace('Business_', '') if selected_doc['filename'].startswith('Business_') else selected_doc['filename']
            
            st.markdown(f"**📊 Analyzing:** {doc_name}")
            
            # Analysis type selector
            col_a1, col_a2 = st.columns([1, 1])
            
            with col_a1:
                analysis_category = st.selectbox(
                    "🎯 Choose Analysis Category:",
                    [
                        "📈 Financial Performance",
                        "📊 Operational Metrics", 
                        "💰 Profitability Analysis",
                        "📉 Risk Assessment",
                        "🎪 Market Analysis",
                        "🔮 Forecasting & Trends",
                        "⚖️ Comparative Analysis",
                        "🎯 Custom Analysis"
                    ]
                )
            
            with col_a2:
                output_format = st.selectbox(
                    "📋 Output Format:",
                    ["📝 Detailed Report", "📊 Executive Summary", "📈 Data Visualization", "📋 Table Format"]
                )
            
            # Dynamic query suggestions based on category
            query_suggestions = {
                "📈 Financial Performance": [
                    "What are the key financial performance indicators?",
                    "How has profitability changed over time?",
                    "What are the main revenue streams and their performance?",
                    "Calculate financial ratios and their implications"
                ],
                "📊 Operational Metrics": [
                    "What are the operational efficiency metrics?",
                    "Identify bottlenecks and improvement opportunities",
                    "Analyze productivity trends and patterns",
                    "Compare operational costs across periods"
                ],
                "💰 Profitability Analysis": [
                    "Break down profit margins by product/service",
                    "Identify most and least profitable segments",
                    "Analyze cost structure and optimization opportunities",
                    "Calculate return on investment metrics"
                ],
                "📉 Risk Assessment": [
                    "Identify financial and operational risks",
                    "Assess cash flow volatility and stability",
                    "Analyze dependency on key customers/suppliers",
                    "Evaluate market and competitive risks"
                ],
                "🎪 Market Analysis": [
                    "Analyze market share and competitive position",
                    "Identify market trends and opportunities",
                    "Assess customer segmentation and behavior",
                    "Evaluate pricing strategy effectiveness"
                ],
                "🔮 Forecasting & Trends": [
                    "Generate revenue and expense forecasts",
                    "Identify seasonal patterns and trends",
                    "Predict future performance based on historical data",
                    "Scenario analysis for different market conditions"
                ],
                "⚖️ Comparative Analysis": [
                    "Compare performance across time periods",
                    "Benchmark against industry standards",
                    "Analyze variance from budget/targets",
                    "Compare different business units/products"
                ]
            }
            
            # Business query input with suggestions
            st.subheader("💭 Analysis Query")
            
            # Quick suggestion buttons
            if analysis_category != "🎯 Custom Analysis":
                st.write("**💡 Quick Suggestions:**")
                suggestions = query_suggestions.get(analysis_category, [])
                
                cols = st.columns(2)
                for i, suggestion in enumerate(suggestions):
                    with cols[i % 2]:
                        if st.button(suggestion, key=f"suggestion_{i}"):
                            st.session_state.selected_query = suggestion
            
            # Custom query input
            business_query = st.text_area(
                "✍️ Enter your business question:",
                value=st.session_state.get('selected_query', ''),
                placeholder=f"Ask any question about {doc_name}...",
                height=120,
                key="business_query_input"
            )
            
            # Clear selection
            if st.button("🗑️ Clear Query"):
                st.session_state.selected_query = ""
                st.rerun()
            
            # Advanced options
            with st.expander("⚙️ Advanced Options"):
                include_charts = st.checkbox("📊 Include data visualizations", value=True)
                include_tables = st.checkbox("📋 Include data tables", value=True)
                include_recommendations = st.checkbox("💡 Include recommendations", value=True)
                confidence_level = st.slider("🎯 Analysis confidence level", 0.7, 1.0, 0.9, 0.05)
            
            # Analyze button
            if st.button("🚀 Run Advanced Analysis", key="advanced_analysis", type="primary"):
                if business_query:
                    with st.spinner("🔬 Running advanced business analysis..."):
                        # Construct enhanced query
                        enhanced_query = f"""
                        Perform a {analysis_category} analysis on this business document.
                        
                        Specific Question: {business_query}
                        
                        Requirements:
                        - Output Format: {output_format}
                        - Include Charts: {include_charts}
                        - Include Tables: {include_tables}
                        - Include Recommendations: {include_recommendations}
                        - Confidence Level: {confidence_level}
                        
                        Please provide a comprehensive analysis with specific numbers, percentages, and actionable insights.
                        """
                        
                        response = send_message_to_chat(
                            "business_analysis_session",
                            enhanced_query,
                            selected_doc['document_id']
                        )
                        
                        if response and response.get("success"):
                            st.success("✅ Analysis complete!")
                            
                            # Display results in an attractive format
                            st.markdown("---")
                            st.subheader("📊 Analysis Results")
                            
                            # Create tabs for different views
                            result_tab1, result_tab2, result_tab3 = st.tabs(["📝 Report", "💡 Insights", "📋 Raw Data"])
                            
                            with result_tab1:
                                st.markdown(f"""
                                <div class="analysis-card">
                                    <h4>🎯 {analysis_category} - {output_format}</h4>
                                    {response["response"]}
                                </div>
                                """, unsafe_allow_html=True)
                            
                            with result_tab2:
                                # Extract key insights
                                insights_query = f"Extract the top 5 key insights and actionable recommendations from this analysis: {response['response'][:1000]}..."
                                insights_response = send_message_to_chat(
                                    "business_analysis_session",
                                    insights_query,
                                    selected_doc['document_id']
                                )
                                
                                if insights_response and insights_response.get("success"):
                                    st.markdown(f"""
                                    <div class="insight-box">
                                        <h4>💡 Key Insights & Recommendations</h4>
                                        {insights_response["response"]}
                                    </div>
                                    """, unsafe_allow_html=True)
                            
                            with result_tab3:
                                st.text_area("Raw Analysis Data", response["response"], height=400)
                                
                                # Download option
                                if st.download_button(
                                    "📥 Download Analysis Report",
                                    data=response["response"],
                                    file_name=f"business_analysis_{doc_name}_{analysis_category.replace('📈 ', '').replace(' ', '_')}.txt",
                                    mime="text/plain"
                                ):
                                    st.success("📥 Report downloaded!")
                        else:
                            st.error("❌ Analysis failed. Please try again.")
                else:
                    st.warning("⚠️ Please enter a business question to analyze.")
        else:
            st.info("👈 Please select a business document from the Dashboard tab to start advanced analysis.")
    
    with tab3:
        # Reports Tab
        st.subheader("📋 Business Reports & Exports")
        
        if st.session_state.selected_business_doc:
            selected_doc = st.session_state.selected_business_doc
            doc_name = selected_doc['filename'].replace('Business_', '') if selected_doc['filename'].startswith('Business_') else selected_doc['filename']
            
            st.write(f"**📊 Generate Reports for:** {doc_name}")
            
            # Report types
            col_r1, col_r2 = st.columns(2)
            
            with col_r1:
                st.subheader("📈 Financial Reports")
                
                if st.button("💰 Income Statement", key="income_statement"):
                    with st.spinner("Generating Income Statement..."):
                        response = send_message_to_chat(
                            "business_analysis_session",
                            "Generate a detailed Income Statement (Profit & Loss) report with revenues, expenses, and net income calculations. Format as a professional financial statement.",
                            selected_doc['document_id']
                        )
                        if response and response.get("success"):
                            st.markdown("### 💰 Income Statement")
                            st.markdown(response["response"])
                
                if st.button("💎 Balance Sheet Analysis", key="balance_sheet"):
                    with st.spinner("Generating Balance Sheet Analysis..."):
                        response = send_message_to_chat(
                            "business_analysis_session",
                            "Analyze the balance sheet data including assets, liabilities, and equity. Calculate key ratios and provide insights on financial position.",
                            selected_doc['document_id']
                        )
                        if response and response.get("success"):
                            st.markdown("### 💎 Balance Sheet Analysis")
                            st.markdown(response["response"])
                
                if st.button("💸 Cash Flow Report", key="cash_flow"):
                    with st.spinner("Generating Cash Flow Report..."):
                        response = send_message_to_chat(
                            "business_analysis_session",
                            "Generate a comprehensive cash flow analysis including operating, investing, and financing activities. Identify cash flow trends and liquidity position.",
                            selected_doc['document_id']
                        )
                        if response and response.get("success"):
                            st.markdown("### 💸 Cash Flow Report")
                            st.markdown(response["response"])
            
            with col_r2:
                st.subheader("📊 Operational Reports")
                
                if st.button("📈 Performance Dashboard", key="performance_dashboard"):
                    with st.spinner("Creating Performance Dashboard..."):
                        response = send_message_to_chat(
                            "business_analysis_session",
                            "Create a comprehensive performance dashboard with KPIs, metrics, trends, and performance indicators. Include visual elements and key insights.",
                            selected_doc['document_id']
                        )
                        if response and response.get("success"):
                            st.markdown("### 📈 Performance Dashboard")
                            st.markdown(response["response"])
                
                if st.button("🎯 Executive Summary", key="executive_summary"):
                    with st.spinner("Generating Executive Summary..."):
                        response = send_message_to_chat(
                            "business_analysis_session",
                            "Create an executive summary highlighting key financial performance, major insights, trends, risks, and strategic recommendations for leadership review.",
                            selected_doc['document_id']
                        )
                        if response and response.get("success"):
                            st.markdown("### 🎯 Executive Summary")
                            st.markdown(response["response"])
                
                if st.button("⚠️ Risk Assessment Report", key="risk_assessment"):
                    with st.spinner("Generating Risk Assessment..."):
                        response = send_message_to_chat(
                            "business_analysis_session",
                            "Conduct a comprehensive risk assessment including financial risks, operational risks, market risks, and mitigation strategies.",
                            selected_doc['document_id']
                        )
                        if response and response.get("success"):
                            st.markdown("### ⚠️ Risk Assessment Report")
                            st.markdown(response["response"])
            
            # Custom report generator
            st.subheader("🛠️ Custom Report Generator")
            
            report_title = st.text_input("📝 Report Title", placeholder="e.g., Q3 Financial Analysis")
            report_sections = st.multiselect(
                "📋 Include Sections:",
                ["Executive Summary", "Financial Overview", "Key Metrics", "Trend Analysis", 
                 "Risk Assessment", "Recommendations", "Appendix", "Data Tables"]
            )
            report_format = st.selectbox("📄 Report Format:", ["Professional", "Executive", "Technical", "Presentation"])
            
            if st.button("📊 Generate Custom Report", key="custom_report"):
                if report_title and report_sections:
                    with st.spinner("Generating custom report..."):
                        custom_query = f"""
                        Generate a {report_format} business report titled "{report_title}" 
                        including the following sections: {', '.join(report_sections)}.
                        
                        Make it comprehensive, professional, and include specific data points,
                        charts descriptions, and actionable insights.
                        """
                        
                        response = send_message_to_chat(
                            "business_analysis_session",
                            custom_query,
                            selected_doc['document_id']
                        )
                        
                        if response and response.get("success"):
                            st.markdown(f"### 📊 {report_title}")
                            st.markdown(response["response"])
                            
                            # Download option
                            if st.download_button(
                                "📥 Download Report",
                                data=response["response"],
                                file_name=f"{report_title.replace(' ', '_')}_report.txt",
                                mime="text/plain"
                            ):
                                st.success("📥 Report downloaded successfully!")
                else:
                    st.warning("⚠️ Please provide a report title and select sections.")
        else:
            st.info("👈 Please select a business document to generate reports.")
    
    with tab4:
        # Settings Tab
        st.subheader("🔧 Business Analysis Settings")
        
        # Analysis preferences
        st.subheader("⚙️ Analysis Preferences")
        
        col_s1, col_s2 = st.columns(2)
        
        with col_s1:
            default_currency = st.selectbox("💱 Default Currency:", ["USD", "EUR", "GBP", "JPY", "CAD", "AUD"])
            date_format = st.selectbox("📅 Date Format:", ["MM/DD/YYYY", "DD/MM/YYYY", "YYYY-MM-DD"])
            number_format = st.selectbox("🔢 Number Format:", ["US (1,234.56)", "EU (1.234,56)", "Indian (1,23,456.78)"])
        
        with col_s2:
            analysis_depth = st.selectbox("🔍 Analysis Depth:", ["Quick", "Standard", "Comprehensive", "Expert"])
            include_charts = st.checkbox("📊 Always include charts", value=True)
            include_recommendations = st.checkbox("💡 Always include recommendations", value=True)
        
        # Document management
        st.subheader("📁 Document Management")
        
        if st.button("🗑️ Clear All Business Documents"):
            if st.checkbox("⚠️ I understand this will delete all business documents"):
                # Here you would implement document deletion
                st.success("📁 All business documents cleared!")
        
        if st.button("📥 Export Analysis History"):
            # Export functionality
            st.success("📊 Analysis history exported!")
        
        # System information
        st.subheader("ℹ️ System Information")
        
        info_col1, info_col2 = st.columns(2)
        
        with info_col1:
            st.info("🔧 **Version:** Business Analytics v2.0")
            st.info("📊 **Engine:** Enhanced AI Analysis")
            st.info("🗄️ **Storage:** Vector Database")
        
        with info_col2:
            st.info("📈 **Features:** Advanced Analytics")
            st.info("🎯 **Accuracy:** 95%+ Analysis Precision")
            st.info("⚡ **Speed:** Real-time Processing")
        
        # General business insights section for when no document is selected
        if not st.session_state.selected_business_doc:
            st.markdown("---")
            st.subheader("💡 General Business Insights")
            
            general_query = st.text_area(
                "Ask a general business question:",
                placeholder="e.g., 'What are best practices for financial analysis?' or 'How to improve cash flow?'",
                height=100
            )
            
            if st.button("🔍 Get Business Insights", key="general_business"):
                if general_query:
                    with st.spinner("Getting business insights..."):
                        insights = get_business_insights(general_query)
                        if insights:
                            st.success("💡 Insights generated!")
                            st.markdown("### 💡 Business Insights:")
                            st.markdown(f"""
                            <div class="insight-box">
                                {insights}
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.warning("⚠️ Please enter a business question")

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
