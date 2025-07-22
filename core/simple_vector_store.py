"""
Simple Vector Store Implementation
This is a fallback implementation that stores vectors in memory and files
when ChromaDB has compatibility issues.
"""

import json
import pickle
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
import uuid
import logging
from config.settings import settings

logger = logging.getLogger(__name__)

class SimpleVectorStore:
    """Simple file-based vector store as fallback"""
    
    def __init__(self):
        self.storage_path = Path(settings.CHROMA_DB_PATH).parent / "simple_store"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.documents_file = self.storage_path / "documents.json"
        self.embeddings_file = self.storage_path / "embeddings.pkl"
        
        # Load existing data
        self.documents = self._load_documents()
        self.embeddings = self._load_embeddings()
        
        logger.info("Using Simple Vector Store (file-based)")
    
    def _load_documents(self) -> Dict[str, Any]:
        """Load documents from file"""
        if self.documents_file.exists():
            try:
                with open(self.documents_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load documents: {e}")
        return {}
    
    def _save_documents(self):
        """Save documents to file"""
        try:
            with open(self.documents_file, 'w', encoding='utf-8') as f:
                json.dump(self.documents, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Could not save documents: {e}")
    
    def _load_embeddings(self) -> Dict[str, List[float]]:
        """Load embeddings from file"""
        if self.embeddings_file.exists():
            try:
                with open(self.embeddings_file, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                logger.warning(f"Could not load embeddings: {e}")
        return {}
    
    def _save_embeddings(self):
        """Save embeddings to file"""
        try:
            with open(self.embeddings_file, 'wb') as f:
                pickle.dump(self.embeddings, f)
        except Exception as e:
            logger.error(f"Could not save embeddings: {e}")
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts (simplified - uses random vectors for demo)"""
        try:
            # For demonstration purposes, we'll use random embeddings
            # In a real implementation, you would use OpenAI's API here
            logger.warning("Using random embeddings for demonstration")
            
            embeddings = []
            for text in texts:
                # Create a simple hash-based embedding for consistency
                import hashlib
                text_hash = hashlib.md5(text.encode()).hexdigest()
                # Convert hex to numbers and normalize
                embedding = [int(text_hash[i:i+2], 16) / 255.0 for i in range(0, 32, 2)]
                # Pad to 1536 dimensions (OpenAI embedding size)
                while len(embedding) < 1536:
                    embedding.extend(embedding[:min(16, 1536-len(embedding))])
                embedding = embedding[:1536]
                embeddings.append(embedding)
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            # Return zero embeddings as fallback
            return [[0.0] * 1536 for _ in texts]
    
    def add_documents(self, 
                     texts: List[str], 
                     metadatas: List[Dict[str, Any]] = None,
                     document_id: str = None) -> List[str]:
        """Add documents to the store"""
        try:
            if not texts:
                return []
            
            # Generate embeddings
            embeddings = self.get_embeddings(texts)
            
            # Generate unique IDs for each chunk
            chunk_ids = [str(uuid.uuid4()) for _ in texts]
            
            # Prepare metadata
            if metadatas is None:
                metadatas = [{}] * len(texts)
            
            # Add document_id to metadata if provided
            if document_id:
                for i, metadata in enumerate(metadatas):
                    metadata['document_id'] = document_id
                    metadata['chunk_index'] = i
            
            # Store documents and embeddings
            for i, (chunk_id, text, metadata, embedding) in enumerate(zip(chunk_ids, texts, metadatas, embeddings)):
                self.documents[chunk_id] = {
                    'text': text,
                    'metadata': metadata
                }
                self.embeddings[chunk_id] = embedding
            
            # Save to files
            self._save_documents()
            self._save_embeddings()
            
            logger.info(f"Added {len(texts)} chunks to simple vector store")
            return chunk_ids
            
        except Exception as e:
            logger.error(f"Error adding documents: {str(e)}")
            return []
    
    def search_similar(self, 
                      query: str, 
                      n_results: int = 5,
                      document_id: str = None) -> Dict[str, Any]:
        """Search for similar documents using simple text matching"""
        try:
            # Generate query embedding
            query_embeddings = self.get_embeddings([query])
            if not query_embeddings:
                return {'documents': [], 'metadatas': [], 'distances': [], 'query': query}
            
            query_embedding = query_embeddings[0]
            
            # Find similar documents
            results = []
            
            for chunk_id, doc_data in self.documents.items():
                metadata = doc_data['metadata']
                text = doc_data['text']
                
                # Filter by document_id if specified
                if document_id and metadata.get('document_id') != document_id:
                    continue
                
                # Calculate similarity (simplified - using text matching)
                query_lower = query.lower()
                text_lower = text.lower()
                
                # Simple scoring based on keyword matches
                score = 0.0
                query_words = query_lower.split()
                
                for word in query_words:
                    if word in text_lower:
                        score += 1.0
                
                # Normalize by query length
                if query_words:
                    score = score / len(query_words)
                
                # Also check for exact phrase matches
                if query_lower in text_lower:
                    score += 0.5
                
                if score > 0:
                    results.append({
                        'chunk_id': chunk_id,
                        'text': text,
                        'metadata': metadata,
                        'score': score,
                        'distance': 1.0 - score  # Convert score to distance
                    })
            
            # Sort by score (highest first)
            results.sort(key=lambda x: x['score'], reverse=True)
            
            # Limit results
            results = results[:n_results]
            
            return {
                'documents': [r['text'] for r in results],
                'metadatas': [r['metadata'] for r in results],
                'distances': [r['distance'] for r in results],
                'query': query
            }
            
        except Exception as e:
            logger.error(f"Error searching: {str(e)}")
            return {'documents': [], 'metadatas': [], 'distances': [], 'query': query}
    
    def get_all_documents(self) -> Dict[str, Any]:
        """Get all documents in the collection"""
        try:
            # Group by document_id
            documents = {}
            for chunk_id, doc_data in self.documents.items():
                metadata = doc_data['metadata']
                doc_id = metadata.get('document_id', 'unknown')
                
                if doc_id not in documents:
                    documents[doc_id] = {
                        'chunks': [],
                        'metadata': metadata
                    }
                documents[doc_id]['chunks'].append(doc_data['text'])
            
            return documents
            
        except Exception as e:
            logger.error(f"Error getting all documents: {str(e)}")
            return {}
    
    def delete_document(self, document_id: str) -> bool:
        """Delete all chunks for a specific document"""
        try:
            deleted_count = 0
            chunk_ids_to_delete = []
            
            # Find chunks to delete
            for chunk_id, doc_data in self.documents.items():
                if doc_data['metadata'].get('document_id') == document_id:
                    chunk_ids_to_delete.append(chunk_id)
            
            # Delete chunks
            for chunk_id in chunk_ids_to_delete:
                if chunk_id in self.documents:
                    del self.documents[chunk_id]
                    deleted_count += 1
                if chunk_id in self.embeddings:
                    del self.embeddings[chunk_id]
            
            if deleted_count > 0:
                # Save changes
                self._save_documents()
                self._save_embeddings()
                logger.info(f"Deleted {deleted_count} chunks for document: {document_id}")
                return True
            else:
                logger.warning(f"No chunks found for document: {document_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {str(e)}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection"""
        try:
            document_types = {}
            document_ids = set()
            
            for chunk_id, doc_data in self.documents.items():
                metadata = doc_data['metadata']
                doc_type = metadata.get('type', 'unknown')
                doc_id = metadata.get('document_id')
                
                if doc_type not in document_types:
                    document_types[doc_type] = 0
                document_types[doc_type] += 1
                
                if doc_id:
                    document_ids.add(doc_id)
            
            return {
                'total_chunks': len(self.documents),
                'unique_documents': len(document_ids),
                'document_types': document_types,
                'collection_name': settings.COLLECTION_NAME + "_simple"
            }
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {}
    
    def reset_collection(self) -> bool:
        """Reset the entire collection"""
        try:
            self.documents = {}
            self.embeddings = {}
            
            # Delete files
            if self.documents_file.exists():
                self.documents_file.unlink()
            if self.embeddings_file.exists():
                self.embeddings_file.unlink()
            
            logger.info("Simple vector store reset successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting collection: {str(e)}")
            return False
