"""
Chat Manager - Enhanced chat functionality with document context and history management
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

from config.settings import settings

logger = logging.getLogger(__name__)

class ChatManager:
    """Manage chat sessions, history, and document context"""
    
    def __init__(self):
        self.chats_folder = Path(settings.UPLOAD_FOLDER).parent / "chats"
        self.chats_folder.mkdir(exist_ok=True)
        
    def create_new_chat(self, title: str = None) -> str:
        """Create a new chat session"""
        chat_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        chat_data = {
            'chat_id': chat_id,
            'title': title or f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            'created_at': timestamp,
            'updated_at': timestamp,
            'messages': [],
            'context_documents': [],
            'metadata': {
                'message_count': 0,
                'document_count': 0,
                'total_tokens': 0
            }
        }
        
        self.save_chat(chat_id, chat_data)
        logger.info(f"Created new chat session: {chat_id}")
        return chat_id
    
    def save_chat(self, chat_id: str, chat_data: Dict[str, Any]) -> bool:
        """Save chat data to file"""
        try:
            chat_file = self.chats_folder / f"{chat_id}.json"
            chat_data['updated_at'] = datetime.now().isoformat()
            
            with open(chat_file, 'w', encoding='utf-8') as f:
                json.dump(chat_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            logger.error(f"Error saving chat {chat_id}: {str(e)}")
            return False
    
    def load_chat(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """Load chat data from file"""
        try:
            chat_file = self.chats_folder / f"{chat_id}.json"
            if not chat_file.exists():
                return None
                
            with open(chat_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading chat {chat_id}: {str(e)}")
            return None
    
    def add_message(self, chat_id: str, role: str, content: str, 
                   document_context: List[str] = None, metadata: Dict = None) -> bool:
        """Add a message to chat history"""
        try:
            chat_data = self.load_chat(chat_id)
            if not chat_data:
                return False
            
            message = {
                'id': str(uuid.uuid4()),
                'role': role,
                'content': content,
                'timestamp': datetime.now().isoformat(),
                'document_context': document_context or [],
                'metadata': metadata or {}
            }
            
            chat_data['messages'].append(message)
            chat_data['metadata']['message_count'] = len(chat_data['messages'])
            
            # Update context documents if provided
            if document_context:
                for doc in document_context:
                    if doc not in chat_data['context_documents']:
                        chat_data['context_documents'].append(doc)
                chat_data['metadata']['document_count'] = len(chat_data['context_documents'])
            
            return self.save_chat(chat_id, chat_data)
        except Exception as e:
            logger.error(f"Error adding message to chat {chat_id}: {str(e)}")
            return False
    
    def get_chat_history(self, chat_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get chat message history"""
        chat_data = self.load_chat(chat_id)
        if not chat_data:
            return []
        
        messages = chat_data['messages']
        return messages[-limit:] if limit else messages
    
    def list_chats(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List all chat sessions"""
        try:
            chats = []
            for chat_file in self.chats_folder.glob("*.json"):
                try:
                    with open(chat_file, 'r', encoding='utf-8') as f:
                        chat_data = json.load(f)
                        
                    chat_summary = {
                        'chat_id': chat_data['chat_id'],
                        'title': chat_data['title'],
                        'created_at': chat_data['created_at'],
                        'updated_at': chat_data['updated_at'],
                        'message_count': chat_data['metadata']['message_count'],
                        'document_count': chat_data['metadata']['document_count'],
                        'last_message': chat_data['messages'][-1]['content'][:100] + "..." if chat_data['messages'] else "No messages yet"
                    }
                    chats.append(chat_summary)
                except Exception as e:
                    logger.error(f"Error reading chat file {chat_file}: {str(e)}")
                    continue
            
            # Sort by updated_at descending
            chats.sort(key=lambda x: x['updated_at'], reverse=True)
            return chats[:limit]
        except Exception as e:
            logger.error(f"Error listing chats: {str(e)}")
            return []
    
    def delete_chat(self, chat_id: str) -> bool:
        """Delete a chat session"""
        try:
            chat_file = self.chats_folder / f"{chat_id}.json"
            if chat_file.exists():
                chat_file.unlink()
                logger.info(f"Deleted chat session: {chat_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting chat {chat_id}: {str(e)}")
            return False
    
    def update_chat_title(self, chat_id: str, new_title: str) -> bool:
        """Update chat title"""
        chat_data = self.load_chat(chat_id)
        if not chat_data:
            return False
        
        chat_data['title'] = new_title
        return self.save_chat(chat_id, chat_data)
    
    def get_chat_context_documents(self, chat_id: str) -> List[str]:
        """Get list of documents referenced in this chat"""
        chat_data = self.load_chat(chat_id)
        if not chat_data:
            return []
        
        return chat_data.get('context_documents', [])
    
    def search_chats(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search chats by content"""
        try:
            results = []
            for chat_file in self.chats_folder.glob("*.json"):
                try:
                    with open(chat_file, 'r', encoding='utf-8') as f:
                        chat_data = json.load(f)
                    
                    # Search in title and messages
                    search_text = f"{chat_data['title']} "
                    for message in chat_data['messages']:
                        search_text += f"{message['content']} "
                    
                    if query.lower() in search_text.lower():
                        chat_summary = {
                            'chat_id': chat_data['chat_id'],
                            'title': chat_data['title'],
                            'created_at': chat_data['created_at'],
                            'updated_at': chat_data['updated_at'],
                            'message_count': chat_data['metadata']['message_count'],
                            'last_message': chat_data['messages'][-1]['content'][:100] + "..." if chat_data['messages'] else "No messages yet"
                        }
                        results.append(chat_summary)
                except Exception as e:
                    continue
            
            # Sort by relevance (updated_at for now)
            results.sort(key=lambda x: x['updated_at'], reverse=True)
            return results[:limit]
        except Exception as e:
            logger.error(f"Error searching chats: {str(e)}")
            return []
    
    def get_chat_stats(self) -> Dict[str, Any]:
        """Get statistics about all chats"""
        try:
            total_chats = 0
            total_messages = 0
            total_documents = 0
            
            for chat_file in self.chats_folder.glob("*.json"):
                try:
                    with open(chat_file, 'r', encoding='utf-8') as f:
                        chat_data = json.load(f)
                    
                    total_chats += 1
                    total_messages += chat_data['metadata']['message_count']
                    total_documents += chat_data['metadata']['document_count']
                except Exception:
                    continue
            
            return {
                'total_chats': total_chats,
                'total_messages': total_messages,
                'total_documents': total_documents,
                'storage_path': str(self.chats_folder)
            }
        except Exception as e:
            logger.error(f"Error getting chat stats: {str(e)}")
            return {
                'total_chats': 0,
                'total_messages': 0,
                'total_documents': 0,
                'storage_path': str(self.chats_folder)
            }
