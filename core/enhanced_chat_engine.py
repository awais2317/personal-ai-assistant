"""
Enhanced Chat Engine for Personal AI Assistant

Provides document-aware conversations with intelligent context switching
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import openai

from config.settings import settings
from core.vector_store import VectorStore
from core.chat_manager import ChatManager

logger = logging.getLogger(__name__)

class EnhancedChatEngine:
    """Enhanced chat engine with document context and conversation management"""
    
    def __init__(self):
        # Initialize OpenAI client with proper configuration
        self.client = openai.OpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=30.0
        )
        self.vector_store = VectorStore()
        self.chat_manager = ChatManager()
        
        # System prompts for different contexts
        self.base_system_prompt = """
You are a highly capable personal AI assistant specializing in:

1. **Document Analysis**: Process and analyze XLS, Word, PDF files
2. **Business Support**: Expense tracking, forecasting, planning, marketing analysis
3. **Academic Research**: Help with grad school preparation, research papers, analysis
4. **Personal Organization**: Diary organization, note-taking, idea structuring
5. **Writing Assistance**: Essays, reports, creative writing, homework help

**Your Capabilities:**
- Analyze uploaded documents and answer questions about their content
- Provide business insights from financial data
- Help organize and structure ideas and plans
- Assist with research and academic writing
- Track expenses and create forecasts
- Maintain context across conversations

**Communication Style:**
- Be helpful, professional, and thorough
- Provide actionable insights and recommendations
- Ask clarifying questions when needed
- Offer multiple perspectives on complex issues
- Structure responses clearly with headers and bullet points

**Context Awareness:**
- Remember previous conversations and uploaded documents
- Reference specific data points from user's files
- Build on previous discussions and analyses
- Maintain continuity in ongoing projects

Always be ready to help with any aspect of the user's business, academic, or personal needs.
        """
        
        self.document_context_prompt = """
**DOCUMENT CONTEXT AVAILABLE:**
You have access to relevant content from the user's uploaded documents. When answering questions:

1. **Prioritize document content** - If the answer exists in the provided document context, use it as your primary source
2. **Reference specific information** - Quote or paraphrase relevant sections from the documents
3. **Combine with general knowledge** - Supplement document information with your general knowledge when helpful
4. **Indicate sources** - Clearly distinguish between information from documents vs. your general knowledge
5. **Be accurate** - Don't make up information that isn't in the documents

If a question cannot be answered from the document context, provide a helpful general response and suggest what information might be found in the documents.
        """
    
    def get_document_context(self, query: str, document_id: str = None, max_chunks: int = 5) -> Tuple[List[str], List[str]]:
        """Get relevant document context for a query"""
        try:
            # Search for relevant document chunks
            search_results = self.vector_store.search_similar(
                query=query,
                n_results=max_chunks,
                document_id=document_id
            )
            
            context_chunks = []
            source_documents = []
            
            if search_results and search_results.get('documents'):
                for i, doc in enumerate(search_results['documents']):
                    if doc and doc.strip():
                        context_chunks.append(doc)
                        
                        # Extract document source from metadata
                        if (search_results.get('metadatas') and 
                            i < len(search_results['metadatas']) and 
                            search_results['metadatas'][i]):
                            
                            metadata = search_results['metadatas'][i]
                            doc_id = metadata.get('document_id', 'Unknown Document')
                            if doc_id not in source_documents:
                                source_documents.append(doc_id)
            
            return context_chunks, source_documents
        except Exception as e:
            logger.error(f"Error getting document context: {str(e)}")
            return [], []
    
    def create_context_aware_prompt(self, query: str, context_chunks: List[str], 
                                  chat_history: List[Dict] = None) -> List[Dict]:
        """Create a context-aware prompt with document information"""
        messages = []
        
        # System message
        system_content = self.base_system_prompt
        
        if context_chunks:
            system_content += "\n\n" + self.document_context_prompt
            system_content += "\n\n**RELEVANT DOCUMENT CONTENT:**\n"
            for i, chunk in enumerate(context_chunks, 1):
                system_content += f"\n--- Document Excerpt {i} ---\n{chunk}\n"
        
        messages.append({"role": "system", "content": system_content})
        
        # Add recent chat history (last 10 messages to stay within token limits)
        if chat_history:
            recent_history = chat_history[-10:] if len(chat_history) > 10 else chat_history
            for msg in recent_history:
                if msg['role'] in ['user', 'assistant']:
                    messages.append({
                        "role": msg['role'],
                        "content": msg['content']
                    })
        
        # Add current query
        messages.append({"role": "user", "content": query})
        
        return messages
    
    def chat(self, message: str, chat_id: str = None, document_id: str = None) -> Dict[str, Any]:
        """
        Process a chat message with document context awareness
        
        Args:
            message: User's message
            chat_id: Optional chat session ID
            document_id: Optional specific document to focus on
            
        Returns:
            Dictionary with response and metadata
        """
        try:
            # Create new chat if none provided
            if not chat_id:
                chat_id = self.chat_manager.create_new_chat()
            
            # Get document context if query seems to be asking about documents
            context_chunks, source_documents = self.get_document_context(
                query=message, 
                document_id=document_id
            )
            
            # Get chat history
            chat_history = self.chat_manager.get_chat_history(chat_id)
            
            # Create context-aware prompt
            messages = self.create_context_aware_prompt(
                query=message,
                context_chunks=context_chunks,
                chat_history=chat_history
            )
            
            # Generate response
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=messages,
                max_tokens=settings.MAX_TOKENS,
                temperature=settings.TEMPERATURE
            )
            
            assistant_message = response.choices[0].message.content
            
            # Save messages to chat history
            self.chat_manager.add_message(
                chat_id=chat_id,
                role="user",
                content=message,
                document_context=source_documents
            )
            
            self.chat_manager.add_message(
                chat_id=chat_id,
                role="assistant",
                content=assistant_message,
                document_context=source_documents,
                metadata={
                    'model': settings.OPENAI_MODEL,
                    'tokens_used': response.usage.total_tokens,
                    'has_document_context': len(context_chunks) > 0,
                    'context_documents': len(source_documents)
                }
            )
            
            # Determine response type
            response_type = "document_based" if context_chunks else "general"
            
            return {
                'success': True,
                'response': assistant_message,
                'chat_id': chat_id,
                'response_type': response_type,
                'context_documents': source_documents,
                'context_chunks_used': len(context_chunks),
                'tokens_used': response.usage.total_tokens,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in chat processing: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'chat_id': chat_id
            }
    
    def get_chat_suggestions(self, chat_id: str) -> List[str]:
        """Get suggested follow-up questions based on chat history and context"""
        try:
            chat_data = self.chat_manager.load_chat(chat_id)
            if not chat_data:
                return []
            
            # Get context documents
            context_docs = chat_data.get('context_documents', [])
            recent_messages = chat_data.get('messages', [])[-5:]  # Last 5 messages
            
            suggestions = []
            
            # Document-based suggestions
            if context_docs:
                suggestions.extend([
                    "Can you summarize the main points from the uploaded document?",
                    "What are the key findings or recommendations?",
                    "Are there any specific details I should pay attention to?",
                    "How does this relate to similar topics?"
                ])
            
            # Context-aware suggestions based on recent conversation
            if recent_messages:
                last_assistant_msg = None
                for msg in reversed(recent_messages):
                    if msg['role'] == 'assistant':
                        last_assistant_msg = msg['content']
                        break
                
                if last_assistant_msg:
                    # Business-related suggestions
                    if any(word in last_assistant_msg.lower() for word in ['business', 'revenue', 'profit', 'expense', 'financial']):
                        suggestions.extend([
                            "Can you create a forecast based on this data?",
                            "What are the business implications?",
                            "How can I improve these metrics?"
                        ])
                    
                    # Academic suggestions
                    if any(word in last_assistant_msg.lower() for word in ['research', 'study', 'analysis', 'academic']):
                        suggestions.extend([
                            "Can you help me outline this for a paper?",
                            "What additional research might be needed?",
                            "How should I cite this information?"
                        ])
            
            # Generic helpful suggestions if no specific context
            if not suggestions:
                suggestions = [
                    "Upload a document to get started with analysis",
                    "What would you like help with today?",
                    "Tell me about your current project",
                    "How can I assist with your work?"
                ]
            
            return suggestions[:4]  # Return top 4 suggestions
            
        except Exception as e:
            logger.error(f"Error getting chat suggestions: {str(e)}")
            return []
    
    def analyze_document_content(self, document_id: str, analysis_type: str = "summary") -> Dict[str, Any]:
        """Analyze document content for specific insights"""
        try:
            # Get all chunks for the document
            search_results = self.vector_store.search_similar(
                query="document content summary analysis",
                document_id=document_id,
                n_results=20  # Get more chunks for comprehensive analysis
            )
            
            if not search_results or not search_results.get('documents'):
                return {
                    'success': False,
                    'error': 'No document content found'
                }
            
            # Combine document chunks
            full_content = "\n\n".join(search_results['documents'])
            
            # Create analysis prompt based on type
            analysis_prompts = {
                "summary": "Provide a comprehensive summary of this document, highlighting the main points, key findings, and important details.",
                "key_points": "Extract and list the key points, main arguments, and important information from this document.",
                "insights": "Analyze this document and provide insights, implications, and potential applications of the information.",
                "questions": "Based on this document content, suggest important questions that should be explored further."
            }
            
            prompt = analysis_prompts.get(analysis_type, analysis_prompts["summary"])
            
            messages = [
                {"role": "system", "content": self.base_system_prompt},
                {"role": "user", "content": f"{prompt}\n\nDocument Content:\n{full_content}"}
            ]
            
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=messages,
                max_tokens=settings.MAX_TOKENS,
                temperature=0.3  # Lower temperature for analysis
            )
            
            return {
                'success': True,
                'analysis': response.choices[0].message.content,
                'analysis_type': analysis_type,
                'document_id': document_id,
                'tokens_used': response.usage.total_tokens
            }
            
        except Exception as e:
            logger.error(f"Error analyzing document: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
