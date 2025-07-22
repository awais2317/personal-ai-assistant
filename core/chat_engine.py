import openai
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import json

from config.settings import settings
from core.vector_store import VectorStore
from core.document_processor import DocumentProcessor
from utils.business_tools import BusinessAnalyzer

logger = logging.getLogger(__name__)

class ChatEngine:
    """Main chat engine for the AI assistant"""
    
    def __init__(self):
        self.vector_store = VectorStore()
        self.document_processor = DocumentProcessor()
        self.business_analyzer = BusinessAnalyzer()
        self.conversation_history = []
        
        # Set up OpenAI client
        from openai import OpenAI
        self.openai_client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=30.0
        )
        
        # System prompt for the AI assistant
        self.system_prompt = """
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
    
    def process_message(self, 
                       message: str, 
                       conversation_id: str = None,
                       include_context: bool = True) -> Dict[str, Any]:
        """
        Process a chat message and generate a response
        
        Args:
            message: User's message
            conversation_id: Optional conversation identifier
            include_context: Whether to include document context
            
        Returns:
            Dictionary with response and metadata
        """
        try:
            # Detect if this is a business/financial query
            is_business_query = self._is_business_query(message)
            
            # Search for relevant context if enabled
            context_docs = []
            if include_context:
                search_results = self.vector_store.search_similar(
                    message, 
                    n_results=5
                )
                context_docs = search_results.get('documents', [])
            
            # Get business context if it's a business query
            business_context = ""
            if is_business_query:
                business_context = self.business_analyzer.get_insights_context()
            
            # Build the conversation context
            conversation_context = self._build_conversation_context(
                message, 
                context_docs, 
                business_context
            )
            
            # Generate response using OpenAI
            response = self._generate_response(conversation_context)
            
            # Store conversation
            self._store_conversation_turn(message, response, conversation_id)
            
            return {
                'response': response,
                'context_used': len(context_docs) > 0,
                'context_sources': len(context_docs),
                'business_analysis': is_business_query,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return {
                'response': "I apologize, but I encountered an error processing your message. Please try again.",
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _is_business_query(self, message: str) -> bool:
        """Detect if a message is related to business/financial topics"""
        business_keywords = [
            'expense', 'cost', 'budget', 'revenue', 'profit', 'loss',
            'forecast', 'trend', 'financial', 'business', 'sales',
            'marketing', 'roi', 'investment', 'pricing', 'bill',
            'receipt', 'invoice', 'tax', 'accounting', 'cash flow'
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in business_keywords)
    
    def _build_conversation_context(self, 
                                   message: str, 
                                   context_docs: List[str],
                                   business_context: str) -> List[Dict[str, str]]:
        """Build the conversation context for OpenAI API"""
        
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Add recent conversation history (last 10 exchanges)
        recent_history = self.conversation_history[-10:]
        for turn in recent_history:
            messages.append({"role": "user", "content": turn['user']})
            messages.append({"role": "assistant", "content": turn['assistant']})
        
        # Add document context if available
        if context_docs:
            context_content = "**Relevant Document Context:**\n\n"
            for i, doc in enumerate(context_docs[:3]):  # Limit to top 3 results
                context_content += f"Document {i+1}:\n{doc}\n\n"
            
            messages.append({
                "role": "system", 
                "content": context_content
            })
        
        # Add business context if available
        if business_context:
            messages.append({
                "role": "system",
                "content": f"**Business Data Context:**\n{business_context}"
            })
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        return messages
    
    def _generate_response(self, messages: List[Dict[str, str]]) -> str:
        """Generate response using OpenAI API"""
        try:
            response = self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=messages,
                temperature=settings.TEMPERATURE,
                max_tokens=settings.MAX_TOKENS
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating OpenAI response: {str(e)}")
            raise
    
    def _store_conversation_turn(self, 
                                user_message: str, 
                                assistant_response: str,
                                conversation_id: str = None):
        """Store a conversation turn in history"""
        turn = {
            'user': user_message,
            'assistant': assistant_response,
            'timestamp': datetime.now().isoformat(),
            'conversation_id': conversation_id
        }
        
        self.conversation_history.append(turn)
        
        # Keep only last 50 turns to manage memory
        if len(self.conversation_history) > 50:
            self.conversation_history = self.conversation_history[-50:]
    
    def upload_and_process_document(self, 
                                   file_path: str, 
                                   document_name: str = None) -> Dict[str, Any]:
        """
        Upload and process a document for the knowledge base
        
        Args:
            file_path: Path to the document file
            document_name: Optional custom name for the document
            
        Returns:
            Dictionary with processing results
        """
        try:
            # Process the document
            doc_data = self.document_processor.process_document(file_path)
            
            # Generate chunks
            chunks = self.document_processor.chunk_content(doc_data['content'])
            
            # Prepare metadata for each chunk
            document_id = document_name or doc_data['filename']
            metadatas = []
            for i, chunk in enumerate(chunks):
                metadata = {
                    'document_id': document_id,
                    'filename': doc_data['filename'],
                    'type': doc_data['type'],
                    'chunk_index': i,
                    'upload_timestamp': datetime.now().isoformat()
                }
                # Add document-specific metadata
                if doc_data['type'] == 'excel' and 'summary' in doc_data:
                    metadata['excel_summary'] = json.dumps(doc_data['summary'])
                elif doc_data['type'] in ['pdf', 'word'] and 'pages' in doc_data:
                    metadata['pages'] = doc_data.get('pages', 0)
                
                metadatas.append(metadata)
            
            # Add to vector store
            chunk_ids = self.vector_store.add_documents(
                texts=chunks,
                metadatas=metadatas,
                document_id=document_id
            )
            
            # If it's business-related data, add to business analyzer
            if doc_data['type'] in ['excel', 'csv']:
                self.business_analyzer.add_document_data(file_path, doc_data)
            
            return {
                'success': True,
                'document_id': document_id,
                'chunks_created': len(chunks),
                'chunk_ids': chunk_ids,
                'document_info': doc_data,
                'message': f"Successfully processed {doc_data['filename']} into {len(chunks)} chunks"
            }
            
        except Exception as e:
            logger.error(f"Error uploading document: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Failed to process document: {str(e)}"
            }
    
    def get_document_list(self) -> List[Dict[str, Any]]:
        """Get list of all uploaded documents"""
        try:
            all_docs = self.vector_store.get_all_documents()
            
            doc_list = []
            for doc_id, doc_info in all_docs.items():
                metadata = doc_info['metadata']
                doc_list.append({
                    'document_id': doc_id,
                    'filename': metadata.get('filename', doc_id),
                    'type': metadata.get('type', 'unknown'),
                    'chunks': len(doc_info['chunks']),
                    'upload_date': metadata.get('upload_timestamp', 'unknown')
                })
            
            return doc_list
            
        except Exception as e:
            logger.error(f"Error getting document list: {str(e)}")
            return []
    
    def search_documents(self, query: str, document_id: str = None) -> Dict[str, Any]:
        """Search within uploaded documents"""
        try:
            results = self.vector_store.search_similar(
                query=query,
                n_results=10,
                document_id=document_id
            )
            
            return {
                'query': query,
                'results': results['documents'],
                'sources': [meta.get('filename', 'unknown') for meta in results.get('metadatas', [])],
                'total_results': len(results['documents'])
            }
            
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return {'error': str(e)}
    
    def get_business_insights(self, query: str = None) -> Dict[str, Any]:
        """Get business insights from uploaded financial data"""
        try:
            return self.business_analyzer.generate_insights(query)
        except Exception as e:
            logger.error(f"Error generating business insights: {str(e)}")
            return {'error': str(e)}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        try:
            vector_stats = self.vector_store.get_collection_stats()
            business_stats = self.business_analyzer.get_stats()
            
            return {
                'vector_store': vector_stats,
                'business_data': business_stats,
                'conversation_turns': len(self.conversation_history),
                'system_status': 'operational'
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            return {'error': str(e)}
