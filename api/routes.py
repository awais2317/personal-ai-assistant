from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional
import logging
from datetime import datetime

from models.schemas import (
    ChatMessage, ChatResponse, DocumentInfo, DocumentProcessResult,
    SearchRequest, SearchResult, BusinessInsightRequest, BusinessInsight,
    ForecastRequest, ForecastResult, SystemStats, FileInfo,
    ErrorResponse, SuccessResponse, HealthCheck
)
from core.chat_engine import ChatEngine
from core.enhanced_chat_engine import EnhancedChatEngine
from core.chat_manager import ChatManager
from utils.file_handlers import file_handler

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Initialize chat engine
chat_engine = ChatEngine()
enhanced_chat_engine = EnhancedChatEngine()
chat_manager = ChatManager()

@router.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    try:
        # Check various components
        components = {
            "chat_engine": "healthy",
            "vector_store": "healthy",
            "file_system": "healthy"
        }
        
        # Test vector store
        try:
            stats = chat_engine.vector_store.get_collection_stats()
            if stats:
                components["vector_store"] = "healthy"
            else:
                components["vector_store"] = "warning"
        except Exception:
            components["vector_store"] = "unhealthy"
        
        # Test file system
        try:
            file_handler.get_storage_stats()
            components["file_system"] = "healthy"
        except Exception:
            components["file_system"] = "unhealthy"
        
        overall_status = "healthy"
        if any(status == "unhealthy" for status in components.values()):
            overall_status = "unhealthy"
        elif any(status == "warning" for status in components.values()):
            overall_status = "warning"
        
        return HealthCheck(
            status=overall_status,
            components=components
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthCheck(
            status="unhealthy",
            components={"error": str(e)}
        )

@router.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Send a message to the AI assistant"""
    try:
        result = chat_engine.process_message(
            message=message.message,
            conversation_id=message.conversation_id,
            include_context=message.include_context
        )
        
        return ChatResponse(**result)
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat message: {str(e)}"
        )

# Enhanced Chat Management Endpoints
@router.post("/chat/new")
async def create_new_chat(title: Optional[str] = None):
    """Create a new chat session"""
    try:
        chat_id = chat_manager.create_new_chat(title)
        # Get the actual title from the chat manager
        chat_data = chat_manager.load_chat(chat_id)
        actual_title = chat_data.get("title", title) if chat_data else title
        
        return {
            "success": True,
            "chat_id": chat_id,
            "title": actual_title or f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        }
    except Exception as e:
        logger.error(f"Error creating new chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/list")
async def list_chats(limit: int = 20):
    """List all chat sessions"""
    try:
        chats = chat_manager.list_chats(limit)
        return {
            "success": True,
            "chats": chats,
            "total": len(chats)
        }
    except Exception as e:
        logger.error(f"Error listing chats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/{chat_id}")
async def get_chat(chat_id: str):
    """Get chat details and history"""
    try:
        chat_data = chat_manager.load_chat(chat_id)
        if not chat_data:
            raise HTTPException(status_code=404, detail="Chat not found")
        
        return {
            "success": True,
            "chat": chat_data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat {chat_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/{chat_id}/message")
async def send_message_to_chat(
    chat_id: str,
    message: ChatMessage
):
    """Send a message in a specific chat session using enhanced engine"""
    try:
        response = enhanced_chat_engine.chat(
            message=message.message,
            chat_id=chat_id,
            document_id=getattr(message, 'document_id', None)
        )
        
        if not response['success']:
            raise HTTPException(status_code=500, detail=response.get('error', 'Chat processing failed'))
        
        # Get suggestions for follow-up questions
        suggestions = enhanced_chat_engine.get_chat_suggestions(chat_id)
        
        return {
            "success": True,
            "response": response['response'],
            "chat_id": response['chat_id'],
            "response_type": response.get('response_type', 'general'),
            "context_documents": response.get('context_documents', []),
            "suggestions": suggestions,
            "tokens_used": response.get('tokens_used', 0),
            "timestamp": response['timestamp']
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message to chat {chat_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/chat/{chat_id}/title")
async def update_chat_title(chat_id: str, title: str):
    """Update chat title"""
    try:
        success = chat_manager.update_chat_title(chat_id, title)
        if not success:
            raise HTTPException(status_code=404, detail="Chat not found")
        
        return {
            "success": True,
            "message": "Chat title updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating chat title {chat_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/chat/{chat_id}")
async def delete_chat(chat_id: str):
    """Delete a chat session"""
    try:
        success = chat_manager.delete_chat(chat_id)
        if not success:
            raise HTTPException(status_code=404, detail="Chat not found")
        
        return {
            "success": True,
            "message": "Chat deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting chat {chat_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/{chat_id}/suggestions")
async def get_chat_suggestions(chat_id: str):
    """Get suggested follow-up questions for a chat"""
    try:
        suggestions = enhanced_chat_engine.get_chat_suggestions(chat_id)
        return {
            "success": True,
            "suggestions": suggestions
        }
    except Exception as e:
        logger.error(f"Error getting suggestions for chat {chat_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chats/search")
async def search_chats(query: str, limit: int = 10):
    """Search chats by content"""
    try:
        results = chat_manager.search_chats(query, limit)
        return {
            "success": True,
            "results": results,
            "query": query,
            "total": len(results)
        }
    except Exception as e:
        logger.error(f"Error searching chats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/stats")
async def get_chat_stats():
    """Get chat statistics"""
    try:
        stats = chat_manager.get_chat_stats()
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error getting chat stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload", response_model=DocumentProcessResult)
async def upload_document(
    file: UploadFile = File(...),
    custom_name: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = None
):
    """Upload and process a document"""
    try:
        # Validate file
        if not file_handler.is_allowed_file(file.filename):
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {', '.join(file_handler.allowed_extensions)}"
            )
        
        # Check file size
        file_size = 0
        if hasattr(file.file, 'seek'):
            file.file.seek(0, 2)  # Seek to end
            file_size = file.file.tell()
            file.file.seek(0)  # Reset to beginning
        
        if file_size > file_handler.max_file_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {file_handler._format_file_size(file_handler.max_file_size)}"
            )
        
        # Save file
        save_result = file_handler.save_uploaded_file(file, custom_name)
        
        if not save_result['success']:
            raise HTTPException(
                status_code=400,
                detail=save_result['error']
            )
        
        # Process document
        result = chat_engine.upload_and_process_document(
            file_path=save_result['file_path'],
            document_name=custom_name or save_result['saved_filename']
        )
        
        return DocumentProcessResult(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading document: {str(e)}"
        )

@router.get("/documents", response_model=List[DocumentInfo])
async def list_documents():
    """Get list of all uploaded documents"""
    try:
        documents = chat_engine.get_document_list()
        return [DocumentInfo(**doc) for doc in documents]
        
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving documents: {str(e)}"
        )

@router.post("/search", response_model=SearchResult)
async def search_documents(search_request: SearchRequest):
    """Search within uploaded documents"""
    try:
        result = chat_engine.search_documents(
            query=search_request.query,
            document_id=search_request.document_id
        )
        
        if 'error' in result:
            raise HTTPException(
                status_code=500,
                detail=result['error']
            )
        
        # Limit results
        result['results'] = result['results'][:search_request.limit]
        result['sources'] = result['sources'][:search_request.limit]
        
        return SearchResult(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error searching documents: {str(e)}"
        )

@router.post("/analyze/business", response_model=BusinessInsight)
async def analyze_business_data(request: BusinessInsightRequest):
    """Analyze business data and generate insights"""
    try:
        result = chat_engine.get_business_insights(request.query)
        
        if 'error' in result:
            raise HTTPException(
                status_code=500,
                detail=result['error']
            )
        
        return BusinessInsight(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Business analysis error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing business data: {str(e)}"
        )

@router.post("/forecast", response_model=ForecastResult)
async def generate_forecast(request: ForecastRequest):
    """Generate forecast from time series data"""
    try:
        result = chat_engine.business_analyzer.generate_forecast(
            document_id=request.document_id,
            periods=request.periods
        )
        
        if 'error' in result:
            raise HTTPException(
                status_code=400,
                detail=result['error']
            )
        
        return ForecastResult(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Forecast error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating forecast: {str(e)}"
        )

@router.get("/stats", response_model=SystemStats)
async def get_system_stats():
    """Get system statistics"""
    try:
        stats = chat_engine.get_stats()
        
        # Add storage stats
        storage_stats = file_handler.get_storage_stats()
        stats['storage_stats'] = storage_stats
        
        return SystemStats(**stats)
        
    except Exception as e:
        logger.error(f"Stats error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving statistics: {str(e)}"
        )

@router.get("/files", response_model=List[FileInfo])
async def list_files():
    """List all uploaded files"""
    try:
        files = file_handler.list_uploaded_files()
        return [FileInfo(**file_info) for file_info in files]
        
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error listing files: {str(e)}"
        )

@router.delete("/files/{filename}", response_model=SuccessResponse)
async def delete_file(filename: str):
    """Delete an uploaded file"""
    try:
        result = file_handler.delete_file(filename)
        
        if not result['success']:
            raise HTTPException(
                status_code=404,
                detail=result['error']
            )
        
        # Also remove from vector store if it exists
        try:
            chat_engine.vector_store.delete_document(filename)
        except Exception as e:
            logger.warning(f"Could not remove {filename} from vector store: {str(e)}")
        
        return SuccessResponse(
            message=result['message'],
            data={"filename": filename}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting file: {str(e)}"
        )

@router.delete("/documents/{document_id}", response_model=SuccessResponse)
async def delete_document(document_id: str):
    """Delete a document from the knowledge base"""
    try:
        success = chat_engine.vector_store.delete_document(document_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Document not found"
            )
        
        return SuccessResponse(
            message=f"Document {document_id} deleted successfully",
            data={"document_id": document_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting document: {str(e)}"
        )

@router.post("/reset", response_model=SuccessResponse)
async def reset_system():
    """Reset the entire system (use with caution!)"""
    try:
        # Reset vector store
        vector_reset = chat_engine.vector_store.reset_collection()
        
        # Clear conversation history
        chat_engine.conversation_history = []
        
        # Clear business data
        chat_engine.business_analyzer.financial_data = {}
        
        if not vector_reset:
            raise HTTPException(
                status_code=500,
                detail="Failed to reset vector store"
            )
        
        return SuccessResponse(
            message="System reset successfully",
            data={
                "vector_store_reset": True,
                "conversation_history_cleared": True,
                "business_data_cleared": True
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting system: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error resetting system: {str(e)}"
        )
