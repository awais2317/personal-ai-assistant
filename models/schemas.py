from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime

class ChatMessage(BaseModel):
    """Model for chat messages"""
    message: str = Field(..., min_length=1, max_length=5000, description="User message")
    conversation_id: Optional[str] = Field(None, description="Optional conversation identifier")
    include_context: bool = Field(True, description="Whether to include document context")
    document_id: Optional[str] = Field(None, description="Specific document to reference")

class ChatResponse(BaseModel):
    """Model for chat responses"""
    response: str = Field(..., description="AI assistant response")
    context_used: bool = Field(False, description="Whether document context was used")
    context_sources: int = Field(0, description="Number of context sources used")
    business_analysis: bool = Field(False, description="Whether business analysis was performed")
    timestamp: str = Field(..., description="Response timestamp")
    error: Optional[str] = Field(None, description="Error message if any")
    chat_id: Optional[str] = Field(None, description="Chat session identifier")
    response_type: Optional[str] = Field("general", description="Type of response (document/business/general)")
    context_documents: List[str] = Field(default_factory=list, description="Documents used for context")
    suggestions: List[str] = Field(default_factory=list, description="Suggested follow-up questions")

class ChatSession(BaseModel):
    """Model for chat session information"""
    chat_id: str = Field(..., description="Unique chat identifier")
    title: str = Field(..., description="Chat title")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    message_count: int = Field(0, description="Number of messages in chat")
    has_documents: bool = Field(False, description="Whether chat references documents")

class ChatHistory(BaseModel):
    """Model for chat history"""
    chat_id: str = Field(..., description="Chat identifier")
    title: str = Field(..., description="Chat title")
    messages: List[Dict[str, Any]] = Field(default_factory=list, description="Chat messages")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    document_references: List[str] = Field(default_factory=list, description="Referenced documents")

class ChatSearchResult(BaseModel):
    """Model for chat search results"""
    chat_id: str = Field(..., description="Chat identifier")
    title: str = Field(..., description="Chat title")
    snippet: str = Field(..., description="Relevant text snippet")
    relevance_score: float = Field(..., description="Search relevance score")
    timestamp: str = Field(..., description="Chat timestamp")

class DocumentUpload(BaseModel):
    """Model for document upload requests"""
    custom_name: Optional[str] = Field(None, max_length=255, description="Custom name for the document")
    
    @validator('custom_name')
    def validate_custom_name(cls, v):
        if v is not None:
            # Remove invalid characters for filenames
            invalid_chars = '<>:"/\\|?*'
            for char in invalid_chars:
                v = v.replace(char, '_')
        return v

class DocumentInfo(BaseModel):
    """Model for document information"""
    document_id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    type: str = Field(..., description="Document type (pdf, word, excel, etc.)")
    chunks: int = Field(0, description="Number of text chunks created")
    upload_date: str = Field(..., description="Upload timestamp")
    size: Optional[int] = Field(None, description="File size in bytes")

class DocumentProcessResult(BaseModel):
    """Model for document processing results"""
    success: bool = Field(..., description="Whether processing was successful")
    document_id: Optional[str] = Field(None, description="Document identifier")
    chunks_created: int = Field(0, description="Number of chunks created")
    message: str = Field(..., description="Processing result message")
    error: Optional[str] = Field(None, description="Error message if processing failed")
    document_info: Optional[Dict[str, Any]] = Field(None, description="Additional document information")

class SearchRequest(BaseModel):
    """Model for document search requests"""
    query: str = Field(..., min_length=1, max_length=1000, description="Search query")
    document_id: Optional[str] = Field(None, description="Optional document ID to search within")
    limit: int = Field(10, ge=1, le=50, description="Maximum number of results")

class SearchResult(BaseModel):
    """Model for search results"""
    query: str = Field(..., description="Original search query")
    results: List[str] = Field([], description="List of matching text chunks")
    sources: List[str] = Field([], description="List of source filenames")
    total_results: int = Field(0, description="Total number of results found")
    error: Optional[str] = Field(None, description="Error message if search failed")

class BusinessInsightRequest(BaseModel):
    """Model for business insight requests"""
    query: Optional[str] = Field(None, max_length=1000, description="Specific insight query")
    document_id: Optional[str] = Field(None, description="Specific document to analyze")

class BusinessInsight(BaseModel):
    """Model for business insights"""
    message: str = Field(..., description="Summary message")
    insights: List[Dict[str, Any]] = Field([], description="List of insights by document")
    query: Optional[str] = Field(None, description="Original query")
    error: Optional[str] = Field(None, description="Error message if analysis failed")

class ForecastRequest(BaseModel):
    """Model for forecast requests"""
    document_id: str = Field(..., description="Document ID containing time series data")
    periods: int = Field(12, ge=1, le=60, description="Number of periods to forecast")

class ForecastResult(BaseModel):
    """Model for forecast results"""
    forecast_values: List[float] = Field([], description="Forecasted values")
    periods: int = Field(..., description="Number of periods forecasted")
    trend: str = Field(..., description="Overall trend direction")
    confidence_interval: float = Field(..., description="95% confidence interval")
    r_squared: float = Field(..., description="R-squared value for model fit")
    error: Optional[str] = Field(None, description="Error message if forecasting failed")

class SystemStats(BaseModel):
    """Model for system statistics"""
    vector_store: Dict[str, Any] = Field({}, description="Vector store statistics")
    business_data: Dict[str, Any] = Field({}, description="Business data statistics")
    conversation_turns: int = Field(0, description="Number of conversation turns")
    system_status: str = Field("operational", description="System status")
    storage_stats: Optional[Dict[str, Any]] = Field(None, description="File storage statistics")

class FileInfo(BaseModel):
    """Model for file information"""
    filename: str = Field(..., description="File name")
    size: int = Field(..., description="File size in bytes")
    size_human: str = Field(..., description="Human readable file size")
    extension: str = Field(..., description="File extension")
    mime_type: Optional[str] = Field(None, description="MIME type")
    created: float = Field(..., description="Creation timestamp")
    modified: float = Field(..., description="Modification timestamp")
    path: str = Field(..., description="File path")

class ErrorResponse(BaseModel):
    """Model for error responses"""
    error: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Additional error details")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Error timestamp")

class SuccessResponse(BaseModel):
    """Model for success responses"""
    success: bool = Field(True, description="Success indicator")
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional data")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Response timestamp")

# Configuration models
class ChatEngineConfig(BaseModel):
    """Configuration for chat engine"""
    openai_model: str = Field("gpt-4", description="OpenAI model to use")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Response creativity")
    max_tokens: int = Field(2000, ge=100, le=4000, description="Maximum response tokens")
    context_limit: int = Field(5, ge=1, le=20, description="Maximum context documents")

class VectorStoreConfig(BaseModel):
    """Configuration for vector store"""
    collection_name: str = Field("personal_assistant", description="Collection name")
    chunk_size: int = Field(1000, ge=100, le=5000, description="Text chunk size")
    chunk_overlap: int = Field(200, ge=0, le=500, description="Chunk overlap size")
    embedding_model: str = Field("text-embedding-ada-002", description="Embedding model")

# Health check model
class HealthCheck(BaseModel):
    """Health check response"""
    status: str = Field("healthy", description="Service status")
    version: str = Field("1.0.0", description="API version")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Check timestamp")
    components: Dict[str, str] = Field({}, description="Component status")

# Export all models
__all__ = [
    "ChatMessage",
    "ChatResponse",
    "DocumentUpload",
    "DocumentInfo",
    "DocumentProcessResult",
    "SearchRequest",
    "SearchResult",
    "BusinessInsightRequest",
    "BusinessInsight",
    "ForecastRequest",
    "ForecastResult",
    "SystemStats",
    "FileInfo",
    "ErrorResponse",
    "SuccessResponse",
    "ChatEngineConfig",
    "VectorStoreConfig",
    "HealthCheck"
]
