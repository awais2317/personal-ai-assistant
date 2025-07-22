import logging
from typing import List, Dict, Any, Optional
import uuid
from pathlib import Path
from config.settings import settings

logger = logging.getLogger(__name__)

class VectorStore:
    """Handle vector database operations with fallback support"""
    
    def __init__(self):
        self.client = None
        self.collection = None
        self.use_chromadb = True
        
        # Try to initialize ChromaDB, fallback to simple store if it fails
        try:
            self.initialize_chromadb()
        except Exception as e:
            logger.warning(f"ChromaDB initialization failed: {str(e)}")
            logger.info("Falling back to Simple Vector Store")
            self.use_chromadb = False
            self.initialize_simple_store()
    
    def initialize_chromadb(self):
        """Initialize ChromaDB client and collection"""
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings
            
            # Create the database directory if it doesn't exist
            db_path = Path(settings.CHROMA_DB_PATH)
            db_path.mkdir(parents=True, exist_ok=True)
            
            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(
                path=str(db_path),
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection(
                    name=settings.COLLECTION_NAME
                )
                logger.info(f"Loaded existing ChromaDB collection: {settings.COLLECTION_NAME}")
            except:
                self.collection = self.client.create_collection(
                    name=settings.COLLECTION_NAME,
                    metadata={"description": "Personal AI Assistant document storage"}
                )
                logger.info(f"Created new ChromaDB collection: {settings.COLLECTION_NAME}")
                
        except Exception as e:
            logger.error(f"Error initializing ChromaDB: {str(e)}")
            raise
    
    def initialize_simple_store(self):
        """Initialize simple file-based vector store"""
        from core.simple_vector_store import SimpleVectorStore
        self.simple_store = SimpleVectorStore()
        logger.info("Simple Vector Store initialized")
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts using OpenAI"""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            
            response = client.embeddings.create(
                model=settings.EMBEDDING_MODEL,
                input=texts
            )
            
            embeddings = [item.embedding for item in response.data]
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            if self.use_chromadb:
                raise
            else:
                # Use simple store fallback
                return self.simple_store.get_embeddings(texts)
    
    def add_documents(self, 
                     texts: List[str], 
                     metadatas: List[Dict[str, Any]] = None,
                     document_id: str = None) -> List[str]:
        """Add documents to the vector store"""
        if self.use_chromadb:
            return self._add_documents_chromadb(texts, metadatas, document_id)
        else:
            return self.simple_store.add_documents(texts, metadatas, document_id)
    
    def _add_documents_chromadb(self, texts, metadatas, document_id):
        """Add documents using ChromaDB"""
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
                for metadata in metadatas:
                    metadata['document_id'] = document_id
                    metadata['chunk_index'] = metadatas.index(metadata)
            
            # Add to collection
            self.collection.add(
                ids=chunk_ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas
            )
            
            logger.info(f"Added {len(texts)} chunks to ChromaDB")
            return chunk_ids
            
        except Exception as e:
            logger.error(f"Error adding documents to ChromaDB: {str(e)}")
            raise
    
    def search_similar(self, 
                      query: str, 
                      n_results: int = 5,
                      document_id: str = None) -> Dict[str, Any]:
        """Search for similar documents"""
        if self.use_chromadb:
            return self._search_similar_chromadb(query, n_results, document_id)
        else:
            return self.simple_store.search_similar(query, n_results, document_id)
    
    def _search_similar_chromadb(self, query, n_results, document_id):
        """Search using ChromaDB"""
        try:
            # Generate query embedding
            query_embedding = self.get_embeddings([query])[0]
            
            # Prepare where clause for filtering
            where_clause = None
            if document_id:
                where_clause = {"document_id": document_id}
            
            # Search in collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_clause,
                include=['documents', 'metadatas', 'distances']
            )
            
            return {
                'documents': results['documents'][0] if results['documents'] else [],
                'metadatas': results['metadatas'][0] if results['metadatas'] else [],
                'distances': results['distances'][0] if results['distances'] else [],
                'query': query
            }
            
        except Exception as e:
            logger.error(f"Error searching ChromaDB: {str(e)}")
            raise
    
    def get_all_documents(self) -> Dict[str, Any]:
        """Get all documents in the collection"""
        if self.use_chromadb:
            return self._get_all_documents_chromadb()
        else:
            return self.simple_store.get_all_documents()
    
    def _get_all_documents_chromadb(self):
        """Get all documents from ChromaDB"""
        try:
            results = self.collection.get(include=['documents', 'metadatas'])
            
            # Group by document_id
            documents = {}
            for i, metadata in enumerate(results['metadatas']):
                doc_id = metadata.get('document_id', 'unknown')
                if doc_id not in documents:
                    documents[doc_id] = {
                        'chunks': [],
                        'metadata': metadata
                    }
                documents[doc_id]['chunks'].append(results['documents'][i])
            
            return documents
            
        except Exception as e:
            logger.error(f"Error getting all documents from ChromaDB: {str(e)}")
            return {}
    
    def delete_document(self, document_id: str) -> bool:
        """Delete all chunks for a specific document"""
        if self.use_chromadb:
            return self._delete_document_chromadb(document_id)
        else:
            return self.simple_store.delete_document(document_id)
    
    def _delete_document_chromadb(self, document_id):
        """Delete document from ChromaDB"""
        try:
            # Get all chunks for this document
            results = self.collection.get(
                where={"document_id": document_id},
                include=['ids']
            )
            
            if results['ids']:
                self.collection.delete(ids=results['ids'])
                logger.info(f"Deleted document from ChromaDB: {document_id}")
                return True
            else:
                logger.warning(f"No chunks found in ChromaDB for document: {document_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting document {document_id} from ChromaDB: {str(e)}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection"""
        if self.use_chromadb:
            return self._get_collection_stats_chromadb()
        else:
            return self.simple_store.get_collection_stats()
    
    def _get_collection_stats_chromadb(self):
        """Get stats from ChromaDB"""
        try:
            count = self.collection.count()
            
            # Get sample of metadata to understand document types
            results = self.collection.get(
                limit=min(100, count),
                include=['metadatas']
            )
            
            document_types = {}
            document_ids = set()
            
            for metadata in results['metadatas']:
                doc_type = metadata.get('type', 'unknown')
                doc_id = metadata.get('document_id')
                
                if doc_type not in document_types:
                    document_types[doc_type] = 0
                document_types[doc_type] += 1
                
                if doc_id:
                    document_ids.add(doc_id)
            
            return {
                'total_chunks': count,
                'unique_documents': len(document_ids),
                'document_types': document_types,
                'collection_name': settings.COLLECTION_NAME,
                'store_type': 'ChromaDB'
            }
            
        except Exception as e:
            logger.error(f"Error getting ChromaDB stats: {str(e)}")
            return {}
    
    def reset_collection(self) -> bool:
        """Reset the entire collection"""
        if self.use_chromadb:
            return self._reset_collection_chromadb()
        else:
            return self.simple_store.reset_collection()
    
    def _reset_collection_chromadb(self):
        """Reset ChromaDB collection"""
        try:
            self.client.delete_collection(settings.COLLECTION_NAME)
            self.collection = self.client.create_collection(
                name=settings.COLLECTION_NAME,
                metadata={"description": "Personal AI Assistant document storage"}
            )
            logger.info("ChromaDB collection reset successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting ChromaDB collection: {str(e)}")
            return False
