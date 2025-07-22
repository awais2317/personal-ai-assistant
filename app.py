"""
Standalone Streamlit App for Personal AI Assistant
This version runs without the separate FastAPI backend for easier deployment
"""

import streamlit as st
import os
import tempfile
import shutil
from pathlib import Path

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
except ImportError as e:
    st.error(f"Import error: {e}")
    st.error("Please make sure all required modules are installed and accessible.")
    st.stop()

# Initialize settings
@st.cache_resource
def initialize_settings():
    """Initialize settings and create required directories"""
    settings = Settings()
    
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
            st.stop()
        
        enhanced_chat_engine = EnhancedChatEngine()
        chat_manager = ChatManager()
        vector_store = VectorStore()
        document_processor = DocumentProcessor()
        file_handler = FileHandler()
        
        return {
            'enhanced_chat_engine': enhanced_chat_engine,
            'chat_manager': chat_manager,
            'vector_store': vector_store,
            'document_processor': document_processor,
            'file_handler': file_handler
        }
    except Exception as e:
        st.error(f"Failed to initialize components: {str(e)}")
        st.stop()

# Load components
components = initialize_components()

def upload_and_process_document(uploaded_file, custom_name=None):
    """Process uploaded document"""
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

def main():
    """Main application"""
    
    # Title
    st.title("🤖 Personal AI Assistant")
    st.markdown("Your intelligent companion for document analysis, business insights, and personal organization")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page:",
        ["💬 Enhanced Chat", "💼 Business Analysis", "📊 System Stats"]
    )
    
    if page == "💬 Enhanced Chat":
        enhanced_chat_page()
    elif page == "💼 Business Analysis":
        business_analysis_page()
    elif page == "📊 System Stats":
        system_stats_page()

def enhanced_chat_page():
    """Enhanced chat interface"""
    st.header("💬 Enhanced Chat with AI Assistant")
    
    # Initialize session state
    if "current_chat_id" not in st.session_state:
        st.session_state.current_chat_id = None
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = {}
    
    # Sidebar for chat management
    with st.sidebar:
        st.subheader("🗂️ Chat Management")
        
        # Create new chat
        if st.button("➕ Create New Chat"):
            chat_manager = components['chat_manager']
            chat_id = chat_manager.create_new_chat("New Chat")
            st.session_state.current_chat_id = chat_id
            st.session_state.chat_messages[chat_id] = []
            st.success("Created new chat!")
            st.rerun()
        
        # Document upload
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
    
    # Main chat interface
    if st.session_state.current_chat_id:
        st.subheader(f"Current Chat: {st.session_state.current_chat_id[:8]}...")
        
        # Display messages
        messages = st.session_state.chat_messages.get(st.session_state.current_chat_id, [])
        
        for message in messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask me anything..."):
            # Add user message
            with st.chat_message("user"):
                st.markdown(prompt)
            
            st.session_state.chat_messages[st.session_state.current_chat_id].append({
                "role": "user",
                "content": prompt
            })
            
            # Get AI response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        enhanced_chat_engine = components['enhanced_chat_engine']
                        response = enhanced_chat_engine.chat(
                            message=prompt,
                            chat_id=st.session_state.current_chat_id
                        )
                        
                        if response and response.get('success'):
                            ai_response = response['response']
                            st.markdown(ai_response)
                            
                            # Add to chat history
                            st.session_state.chat_messages[st.session_state.current_chat_id].append({
                                "role": "assistant",
                                "content": ai_response
                            })
                        else:
                            st.error("Failed to get AI response")
                    
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
    else:
        st.info("👈 Create a new chat from the sidebar to start!")

def business_analysis_page():
    """Business analysis interface"""
    st.header("💼 Business Analysis")
    
    st.info("🚧 Business analysis features are available in the full version with FastAPI backend.")
    
    # Simple document upload for analysis
    uploaded_file = st.file_uploader(
        "Upload business document for analysis",
        type=['xlsx', 'xls', 'csv']
    )
    
    if uploaded_file:
        if st.button("Analyze Document"):
            with st.spinner("Analyzing..."):
                result = upload_and_process_document(uploaded_file, f"Business_{uploaded_file.name}")
                if result['success']:
                    st.success("Document processed!")
                    
                    # Simple analysis query
                    query = st.text_input("Ask a question about your business document:")
                    if query and st.button("Get Analysis"):
                        try:
                            enhanced_chat_engine = components['enhanced_chat_engine']
                            response = enhanced_chat_engine.chat(
                                message=f"Analyze this business document: {query}",
                                document_id=result.get('document_id')
                            )
                            
                            if response and response.get('success'):
                                st.markdown("### Analysis Results:")
                                st.markdown(response['response'])
                        except Exception as e:
                            st.error(f"Analysis error: {str(e)}")

def system_stats_page():
    """System statistics"""
    st.header("📊 System Statistics")
    
    try:
        # Basic stats
        uploads_dir = Path("uploads")
        chats_dir = Path("chats")
        
        num_documents = len(list(uploads_dir.glob("*"))) if uploads_dir.exists() else 0
        num_chats = len(list(chats_dir.glob("*.json"))) if chats_dir.exists() else 0
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📄 Documents", num_documents)
        with col2:
            st.metric("💬 Chat Sessions", num_chats)
        with col3:
            st.metric("🤖 AI Engine", "Active")
            
        st.subheader("💡 Usage Tips")
        st.markdown("""
        - **Upload documents** to get context-aware responses
        - **Create chat sessions** to organize conversations
        - **Ask specific questions** about your documents
        - **Use business analysis** for financial data insights
        """)
        
    except Exception as e:
        st.error(f"Error loading stats: {str(e)}")

if __name__ == "__main__":
    main()
