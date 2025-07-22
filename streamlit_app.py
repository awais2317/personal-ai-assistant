"""
Enhanced Standalone Streamlit App for Personal AI Assistant
Combines all functionality without requiring a separate FastAPI backend
"""

import streamlit as st
import os
import tempfile
import shutil
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Set page config first
st.set_page_config(
    page_title="Personal AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import after page config
try:
    from core.enhanced_chat_engine import EnhancedChatEngine
    from core.chat_manager import ChatManager
    from core.vector_store import VectorStore
    from core.document_processor import DocumentProcessor
    from utils.file_handlers import FileHandler
    from config.settings import Settings
    from utils.business_tools import BusinessAnalyzer
except ImportError as e:
    st.error(f"Import error: {e}")
    st.error("Please make sure all required modules are installed and accessible.")
    st.stop()

# Initialize settings
@st.cache_resource
def initialize_settings():
    """Initialize settings and create required directories"""
    settings = Settings()
    
    # Check for API key in Streamlit secrets first
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "your_openai_api_key_here":
        if hasattr(st, 'secrets') and 'OPENAI_API_KEY' in st.secrets:
            settings.OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
    
    # Create required directories
    os.makedirs("data/chroma_db", exist_ok=True)
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("chats", exist_ok=True)
    
    return settings

# Initialize components
@st.cache_resource
def initialize_components():
    """Initialize core components"""
    try:
        settings = initialize_settings()
        
        # Check OpenAI API key
        if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "your_openai_api_key_here":
            st.error("🔑 OpenAI API key not configured!")
            st.error("Please set your OpenAI API key in Streamlit secrets or environment variables.")
            st.info("Go to your Streamlit Cloud dashboard → App settings → Secrets and add: OPENAI_API_KEY = \"your_key_here\"")
            st.stop()
        
        # Initialize components with error handling
        try:
            enhanced_chat_engine = EnhancedChatEngine()
        except Exception as e:
            st.error(f"Failed to initialize chat engine: {str(e)}")
            st.error("This might be due to OpenAI API configuration issues.")
            st.stop()
            
        try:
            chat_manager = ChatManager()
            vector_store = VectorStore()
            document_processor = DocumentProcessor()
            file_handler = FileHandler()
            business_analyzer = BusinessAnalyzer()
        except Exception as e:
            st.error(f"Failed to initialize support components: {str(e)}")
            st.stop()
        
        return {
            'enhanced_chat_engine': enhanced_chat_engine,
            'chat_manager': chat_manager,
            'vector_store': vector_store,
            'document_processor': document_processor,
            'file_handler': file_handler,
            'business_analyzer': business_analyzer
        }
    except Exception as e:
        st.error(f"Failed to initialize components: {str(e)}")
        st.stop()

# Load components
components = initialize_components()

def upload_and_process_document(uploaded_file, custom_name=None):
    """Process uploaded document and add to vector store"""
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
            shutil.copyfileobj(uploaded_file, tmp_file)
            tmp_path = tmp_file.name
        
        # Process document
        file_name = custom_name or uploaded_file.name
        
        # Save to uploads directory
        upload_path = Path("uploads") / file_name
        shutil.copy2(tmp_path, upload_path)
        
        # Process with document processor
        processor = components['document_processor']
        result = processor.process_document(str(upload_path))
        
        # Add to vector store
        vector_store = components['vector_store']
        if result.get('chunks'):
            for chunk in result['chunks']:
                vector_store.add_document(
                    content=chunk['content'],
                    metadata={
                        'document_id': result.get('document_id'),
                        'filename': file_name,
                        'chunk_index': chunk.get('chunk_index', 0),
                        'upload_date': datetime.now().isoformat()
                    }
                )
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        return {
            'success': True,
            'chunks_created': len(result.get('chunks', [])),
            'document_id': result.get('document_id'),
            'message': f'Successfully processed {file_name}'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': f'Failed to process document: {str(e)}'
        }

def get_uploaded_documents():
    """Get list of uploaded documents"""
    try:
        uploads_dir = Path("uploads")
        if not uploads_dir.exists():
            return []
        
        documents = []
        for file_path in uploads_dir.glob("*"):
            if file_path.is_file():
                documents.append({
                    'name': file_path.name,
                    'size': file_path.stat().st_size,
                    'modified': datetime.fromtimestamp(file_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                })
        
        return sorted(documents, key=lambda x: x['modified'], reverse=True)
    except Exception as e:
        st.error(f"Error loading documents: {e}")
        return []

def get_chat_list():
    """Get list of saved chats"""
    try:
        chats_dir = Path("chats")
        if not chats_dir.exists():
            return []
        
        chats = []
        for chat_file in chats_dir.glob("*.json"):
            try:
                with open(chat_file, 'r', encoding='utf-8') as f:
                    chat_data = json.load(f)
                    chats.append({
                        'id': chat_file.stem,
                        'title': chat_data.get('title', 'Untitled Chat'),
                        'created': chat_data.get('created', ''),
                        'message_count': len(chat_data.get('messages', []))
                    })
            except Exception:
                continue
        
        return sorted(chats, key=lambda x: x.get('created', ''), reverse=True)
    except Exception:
        return []

def save_chat(chat_id: str, messages: List[Dict], title: str = ""):
    """Save chat to file"""
    try:
        chats_dir = Path("chats")
        chats_dir.mkdir(exist_ok=True)
        
        chat_data = {
            'id': chat_id,
            'title': title or f"Chat {chat_id[:8]}",
            'created': datetime.now().isoformat(),
            'messages': messages
        }
        
        chat_file = chats_dir / f"{chat_id}.json"
        with open(chat_file, 'w', encoding='utf-8') as f:
            json.dump(chat_data, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        st.error(f"Failed to save chat: {e}")
        return False

def load_chat(chat_id: str):
    """Load chat from file"""
    try:
        chat_file = Path("chats") / f"{chat_id}.json"
        if chat_file.exists():
            with open(chat_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return None

def main():
    """Main application"""
    
    # Title and description
    st.title("🤖 Personal AI Assistant")
    st.markdown("Your intelligent companion for document analysis, business insights, and personal organization")
    
    # Initialize session state
    if "current_chat_id" not in st.session_state:
        st.session_state.current_chat_id = None
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = {}
    if "selected_document" not in st.session_state:
        st.session_state.selected_document = None
    
    # Sidebar navigation
    st.sidebar.title("🧭 Navigation")
    page = st.sidebar.selectbox(
        "Choose a page:",
        ["💬 Chat Assistant", "📊 Business Analytics", "📁 Document Manager", "⚙️ System Stats"]
    )
    
    if page == "💬 Chat Assistant":
        chat_page()
    elif page == "📊 Business Analytics":
        business_analytics_page()
    elif page == "📁 Document Manager":
        document_manager_page()
    elif page == "⚙️ System Stats":
        system_stats_page()

def chat_page():
    """Enhanced chat interface"""
    
    # Sidebar for chat and document management
    with st.sidebar:
        st.subheader("🗂️ Chat Management")
        
        # Create new chat
        if st.button("➕ Create New Chat", key="create_chat"):
            import uuid
            chat_id = str(uuid.uuid4())
            st.session_state.current_chat_id = chat_id
            st.session_state.chat_messages[chat_id] = []
            st.success("Created new chat!")
            st.rerun()
        
        # Load existing chats
        chats = get_chat_list()
        if chats:
            st.subheader("💬 Saved Chats")
            for chat in chats[:10]:  # Show last 10 chats
                col1, col2 = st.columns([3, 1])
                with col1:
                    if st.button(
                        f"{chat['title'][:20]}...",
                        key=f"load_{chat['id']}",
                        help=f"Messages: {chat['message_count']}"
                    ):
                        st.session_state.current_chat_id = chat['id']
                        chat_data = load_chat(chat['id'])
                        if chat_data:
                            st.session_state.chat_messages[chat['id']] = chat_data.get('messages', [])
                        st.rerun()
                with col2:
                    if st.button("🗑️", key=f"del_{chat['id']}", help="Delete chat"):
                        try:
                            chat_file = Path("chats") / f"{chat['id']}.json"
                            if chat_file.exists():
                                chat_file.unlink()
                            st.success("Chat deleted!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to delete: {e}")
        
        # Document upload section
        st.subheader("📤 Upload Documents")
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=['txt', 'pdf', 'docx', 'doc', 'xlsx', 'xls', 'csv', 'md']
        )
        
        if uploaded_file and st.button("Upload Document"):
            with st.spinner("Processing document..."):
                result = upload_and_process_document(uploaded_file)
                if result['success']:
                    st.success("Document uploaded successfully!")
                    st.info(f"Created {result['chunks_created']} text chunks")
                else:
                    st.error(f"Upload failed: {result['message']}")
        
        # Document selection for context
        documents = get_uploaded_documents()
        if documents:
            st.subheader("📄 Document Context")
            doc_names = ["None"] + [doc['name'] for doc in documents]
            selected_doc_name = st.selectbox(
                "Select document for context:",
                doc_names,
                key="doc_context"
            )
            if selected_doc_name != "None":
                st.session_state.selected_document = selected_doc_name
            else:
                st.session_state.selected_document = None
    
    # Main chat interface
    if st.session_state.current_chat_id:
        chat_id = st.session_state.current_chat_id
        
        # Chat header with save option
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader(f"💬 Chat: {chat_id[:8]}...")
        with col2:
            if st.button("💾 Save Chat"):
                messages = st.session_state.chat_messages.get(chat_id, [])
                if save_chat(chat_id, messages):
                    st.success("Chat saved!")
        
        # Display context info
        if st.session_state.selected_document:
            st.info(f"📄 Document context: {st.session_state.selected_document}")
        
        # Display messages
        messages = st.session_state.chat_messages.get(chat_id, [])
        
        for i, message in enumerate(messages):
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                # Add suggestions for assistant messages
                if message["role"] == "assistant" and i == len(messages) - 1:
                    suggestions = [
                        "Can you explain this in more detail?",
                        "What are the key takeaways?",
                        "How can I apply this information?"
                    ]
                    
                    st.markdown("**💡 Quick follow-ups:**")
                    cols = st.columns(len(suggestions))
                    for j, suggestion in enumerate(suggestions):
                        with cols[j]:
                            if st.button(suggestion, key=f"suggestion_{i}_{j}"):
                                # Add suggestion as user message
                                st.session_state.chat_messages[chat_id].append({
                                    "role": "user",
                                    "content": suggestion
                                })
                                st.rerun()
        
        # Chat input
        if prompt := st.chat_input("Ask me anything..."):
            # Add user message
            with st.chat_message("user"):
                st.markdown(prompt)
            
            st.session_state.chat_messages[chat_id].append({
                "role": "user",
                "content": prompt
            })
            
            # Get AI response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        enhanced_chat_engine = components['enhanced_chat_engine']
                        
                        # Include document context if selected
                        context_params = {}
                        if st.session_state.selected_document:
                            context_params['document_id'] = st.session_state.selected_document
                        
                        response = enhanced_chat_engine.chat(
                            message=prompt,
                            chat_id=chat_id,
                            **context_params
                        )
                        
                        if response and response.get('success'):
                            ai_response = response['response']
                            st.markdown(ai_response)
                            
                            # Add to chat history
                            st.session_state.chat_messages[chat_id].append({
                                "role": "assistant",
                                "content": ai_response
                            })
                        else:
                            st.error("Failed to get AI response")
                    
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
    else:
        # Welcome screen
        st.markdown("""
        ## Welcome to your Personal AI Assistant! 👋
        
        ### Get started:
        1. **👈 Create a new chat** from the sidebar
        2. **📤 Upload documents** for context-aware conversations
        3. **💬 Ask questions** about your documents or anything else
        
        ### Features:
        - 🧠 **Smart conversations** with document context
        - 📊 **Business analytics** for your data
        - 📁 **Document management** and search
        - 💾 **Save and load** chat sessions
        """)
        
        # Quick actions
        st.subheader("🚀 Quick Actions")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💼 Business Analysis Chat"):
                import uuid
                chat_id = str(uuid.uuid4())
                st.session_state.current_chat_id = chat_id
                st.session_state.chat_messages[chat_id] = [{
                    "role": "assistant",
                    "content": "Hello! I'm ready to help with business analysis. Please upload your business documents (Excel, CSV) or ask me about financial planning, forecasting, or business insights."
                }]
                st.rerun()
        
        with col2:
            if st.button("📚 Academic Research Chat"):
                import uuid
                chat_id = str(uuid.uuid4())
                st.session_state.current_chat_id = chat_id
                st.session_state.chat_messages[chat_id] = [{
                    "role": "assistant",
                    "content": "Hi! I'm here to assist with academic research, paper writing, and study planning. Upload your research documents or ask me about any academic topic."
                }]
                st.rerun()

def business_analytics_page():
    """Business analytics and visualization"""
    st.header("📊 Business Analytics")
    
    # File upload for business data
    st.subheader("📤 Upload Business Data")
    uploaded_file = st.file_uploader(
        "Upload your business data (Excel, CSV)",
        type=['xlsx', 'xls', 'csv'],
        key="business_upload"
    )
    
    if uploaded_file:
        try:
            # Read the data
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            st.success(f"✅ Loaded data: {df.shape[0]} rows, {df.shape[1]} columns")
            
            # Display basic info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📊 Total Rows", df.shape[0])
            with col2:
                st.metric("📋 Columns", df.shape[1])
            with col3:
                numeric_cols = df.select_dtypes(include=['number']).columns
                st.metric("🔢 Numeric Columns", len(numeric_cols))
            
            # Show data preview
            st.subheader("📋 Data Preview")
            st.dataframe(df.head(10))
            
            # Basic analysis
            if len(numeric_cols) > 0:
                st.subheader("📈 Quick Analysis")
                
                # Column selection for analysis
                selected_col = st.selectbox("Select column for analysis:", numeric_cols)
                
                if selected_col:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Basic statistics
                        st.markdown("**📊 Statistics**")
                        stats = df[selected_col].describe()
                        st.dataframe(stats)
                    
                    with col2:
                        # Visualization
                        fig = px.histogram(df, x=selected_col, title=f"Distribution of {selected_col}")
                        st.plotly_chart(fig, use_container_width=True)
                
                # Time series analysis if date column exists
                date_cols = df.select_dtypes(include=['datetime64', 'object']).columns
                potential_date_cols = [col for col in date_cols if any(word in col.lower() for word in ['date', 'time', 'day', 'month', 'year'])]
                
                if potential_date_cols and len(numeric_cols) > 0:
                    st.subheader("📅 Time Series Analysis")
                    date_col = st.selectbox("Select date column:", potential_date_cols)
                    value_col = st.selectbox("Select value column:", numeric_cols, key="ts_value")
                    
                    if date_col and value_col:
                        try:
                            # Convert to datetime
                            df_ts = df.copy()
                            df_ts[date_col] = pd.to_datetime(df_ts[date_col])
                            df_ts = df_ts.sort_values(date_col)
                            
                            # Create time series plot
                            fig = px.line(df_ts, x=date_col, y=value_col, title=f"{value_col} over Time")
                            st.plotly_chart(fig, use_container_width=True)
                        except Exception as e:
                            st.error(f"Error creating time series: {e}")
            
            # AI-powered insights
            st.subheader("🤖 AI Insights")
            if st.button("🔍 Generate Business Insights"):
                with st.spinner("Analyzing your data..."):
                    try:
                        # Process document for AI analysis
                        temp_file = f"temp_business_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                        df.to_csv(temp_file, index=False)
                        
                        # Upload and process
                        with open(temp_file, 'rb') as f:
                            # Create a file-like object for upload_and_process_document
                            class FileObj:
                                def __init__(self, file_path):
                                    self.name = file_path
                                    with open(file_path, 'rb') as f:
                                        self.content = f.read()
                                def read(self):
                                    return self.content
                            
                            file_obj = FileObj(temp_file)
                            result = upload_and_process_document(file_obj, f"business_analysis_{uploaded_file.name}")
                            
                            if result['success']:
                                # Get AI insights
                                enhanced_chat_engine = components['enhanced_chat_engine']
                                response = enhanced_chat_engine.chat(
                                    message="Please analyze this business data and provide key insights, trends, and recommendations. Focus on actionable business intelligence.",
                                    document_id=result.get('document_id')
                                )
                                
                                if response and response.get('success'):
                                    st.markdown("### 🎯 Business Insights:")
                                    st.markdown(response['response'])
                                else:
                                    st.error("Failed to generate insights")
                            
                        # Clean up temp file
                        if os.path.exists(temp_file):
                            os.unlink(temp_file)
                            
                    except Exception as e:
                        st.error(f"Error generating insights: {e}")
        
        except Exception as e:
            st.error(f"Error loading data: {e}")
    
    else:
        st.info("👆 Upload your business data to get started with analytics and AI insights!")

def document_manager_page():
    """Document management interface"""
    st.header("📁 Document Manager")
    
    # Upload section
    st.subheader("📤 Upload New Documents")
    uploaded_files = st.file_uploader(
        "Choose files to upload",
        type=['txt', 'pdf', 'docx', 'doc', 'xlsx', 'xls', 'csv', 'md'],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        if st.button("Upload All Documents"):
            progress_bar = st.progress(0)
            success_count = 0
            
            for i, uploaded_file in enumerate(uploaded_files):
                with st.spinner(f"Processing {uploaded_file.name}..."):
                    result = upload_and_process_document(uploaded_file)
                    if result['success']:
                        success_count += 1
                        st.success(f"✅ {uploaded_file.name}")
                    else:
                        st.error(f"❌ {uploaded_file.name}: {result['message']}")
                
                progress_bar.progress((i + 1) / len(uploaded_files))
            
            st.success(f"Upload complete! {success_count}/{len(uploaded_files)} files processed successfully.")
    
    # Document list
    st.subheader("📋 Uploaded Documents")
    documents = get_uploaded_documents()
    
    if documents:
        for doc in documents:
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                st.write(f"📄 **{doc['name']}**")
            with col2:
                st.write(f"{doc['size']} bytes")
            with col3:
                st.write(doc['modified'])
            with col4:
                if st.button("🗑️", key=f"delete_{doc['name']}", help="Delete document"):
                    try:
                        file_path = Path("uploads") / doc['name']
                        if file_path.exists():
                            file_path.unlink()
                            st.success(f"Deleted {doc['name']}")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Failed to delete: {e}")
    else:
        st.info("No documents uploaded yet. Upload some documents to get started!")

def system_stats_page():
    """System statistics and information"""
    st.header("⚙️ System Statistics")
    
    try:
        # Basic statistics
        uploads_dir = Path("uploads")
        chats_dir = Path("chats")
        
        num_documents = len(list(uploads_dir.glob("*"))) if uploads_dir.exists() else 0
        num_chats = len(list(chats_dir.glob("*.json"))) if chats_dir.exists() else 0
        
        # Calculate total file sizes
        total_size = 0
        if uploads_dir.exists():
            for file_path in uploads_dir.glob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📄 Documents", num_documents)
        with col2:
            st.metric("💬 Chat Sessions", num_chats)
        with col3:
            st.metric("💾 Storage Used", f"{total_size / 1024 / 1024:.1f} MB")
        with col4:
            st.metric("🤖 AI Engine", "Active" if components else "Inactive")
        
        # Component status
        st.subheader("🔧 Component Status")
        component_status = {
            "Enhanced Chat Engine": "✅ Active",
            "Vector Store": "✅ Active", 
            "Document Processor": "✅ Active",
            "Business Analyzer": "✅ Active",
            "File Handler": "✅ Active"
        }
        
        for component, status in component_status.items():
            st.write(f"**{component}**: {status}")
        
        # Usage tips
        st.subheader("💡 Usage Tips")
        st.markdown("""
        ### Getting the Most from Your AI Assistant:
        
        **📄 Document Processing:**
        - Upload PDFs, Word docs, Excel files, and CSVs
        - Documents are automatically processed into searchable chunks
        - Use document context in chats for accurate, specific answers
        
        **💬 Chat Features:**
        - Create multiple chat sessions for different topics
        - Save important conversations for later reference
        - Use quick follow-up suggestions for deeper insights
        
        **📊 Business Analytics:**
        - Upload business data for automated analysis
        - Get AI-powered insights and recommendations
        - Visualize trends and patterns in your data
        
        **🔧 Best Practices:**
        - Keep document names descriptive and organized
        - Regularly save important chat sessions
        - Use specific questions for better AI responses
        - Try different document contexts for varied perspectives
        """)
        
        # Recent activity
        st.subheader("📈 Recent Activity")
        recent_docs = sorted(get_uploaded_documents(), key=lambda x: x['modified'], reverse=True)[:5]
        recent_chats = sorted(get_chat_list(), key=lambda x: x.get('created', ''), reverse=True)[:5]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📄 Recent Documents:**")
            for doc in recent_docs:
                st.write(f"• {doc['name']} ({doc['modified']})")
        
        with col2:
            st.markdown("**💬 Recent Chats:**")
            for chat in recent_chats:
                st.write(f"• {chat['title']} ({chat['message_count']} messages)")
        
    except Exception as e:
        st.error(f"Error loading system stats: {e}")

if __name__ == "__main__":
    main()
