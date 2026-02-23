"""
FitGen AI v5.0 - Database Manager Module
Centralized MongoDB connection and operations
Single database for all collections
"""

import logging
from typing import Optional, Dict, List, Any
from datetime import datetime

try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False

from config import (
    MONGODB_CONNECTION_STRING,
    MONGODB_DATABASE,
    COLLECTIONS,
    LOGS_DIR
)
from utils import log_error, log_info, log_success, log_warning

logger = logging.getLogger(__name__)

# ============================================================================
# DATABASE MANAGER CLASS
# ============================================================================

class DatabaseManager:
    """
    Centralized MongoDB connection manager
    SINGLE DATABASE (fitgen_db) for all operations
    Handles: users, exercises, weekly_plans, session_logs, motivation_logs, etc.
    """
    
    def __init__(self, connection_string: str = MONGODB_CONNECTION_STRING,
                 db_name: str = MONGODB_DATABASE):
        """
        Initialize database manager
        
        Args:
            connection_string: MongoDB connection string (local or Atlas)
            db_name: Database name (default: fitgen_db)
        """
        self.connection_string = connection_string
        self.db_name = db_name
        self.client = None
        self.db = None
        self.in_memory_fallback = {}  # Fallback if no MongoDB
        
        self.connect()
        self._ensure_collections()
    
    def connect(self) -> bool:
        """
        Establish MongoDB connection
        Returns True if successful, False otherwise
        """
        if not MONGODB_AVAILABLE:
            log_warning("⚠️  MongoDB driver not available - using in-memory storage")
            return False
        
        try:
            self.client = MongoClient(
                self.connection_string,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000
            )
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client[self.db_name]
            log_success(f"Connected to MongoDB database: {self.db_name}")
            return True
        
        except ConnectionFailure:
            log_warning("⚠️  MongoDB Connection Failed - using in-memory storage")
            self.db = None
            return False
        except ServerSelectionTimeoutError:
            log_warning("⚠️  MongoDB Timeout - using in-memory storage")
            self.db = None
            return False
        except Exception as e:
            log_error(f"MongoDB Connection Error: {e}")
            self.db = None
            return False
    
    def _ensure_collections(self):
        """
        Ensure all required collections exist in SINGLE database
        Feature 28: Single MongoDB Database
        """
        if self.db is None:
            log_info("Using in-memory storage - collections created on demand")
            return
        
        try:
            existing_collections = self.db.list_collection_names()
            
            for collection_name in COLLECTIONS.values():
                if collection_name not in existing_collections:
                    self.db.create_collection(collection_name)
                    log_info(f"✅ Created collection: {collection_name}")
            
            # Create indexes
            self._create_indexes()
            
        except Exception as e:
            log_error(f"Failed to create collections: {e}")
    
    def _create_indexes(self):
        """
        Create database indexes for performance optimization
        Feature 29: Database Admin Tools
        """
        if self.db is None:
            return
        
        try:
            # Users collection
            self.db['users'].create_index([('user_id', 1)], unique=True)
            
            # Exercises collection
            self.db['exercises'].create_index([('title', 1)])
            self.db['exercises'].create_index([('body_part', 1)])
            self.db['exercises'].create_index([('equipment', 1)])
            self.db['exercises'].create_index([('level', 1)])
            
            # Weekly plans collection
            self.db['weekly_plans'].create_index([('user_id', 1), ('week_date', -1)])
            
            # Session logs collection
            self.db['session_logs'].create_index([('user_id', 1), ('date', -1)])
            
            # Motivation logs collection
            self.db['motivation_logs'].create_index([('user_id', 1), ('date', -1)])
            
            # Exercise history collection
            self.db['exercise_history'].create_index([('user_id', 1), ('exercise_id', 1)])
            
            # User preferences collection
            self.db['user_preferences'].create_index([('user_id', 1)])
            
            log_info("✅ Database indexes created successfully")
            
        except Exception as e:
            log_warning(f"Index creation warning: {e}")
    
    # ========================================================================
    # CRUD OPERATIONS - GENERIC
    # ========================================================================
    
    def insert_one(self, collection_name: str, document: Dict) -> bool:
        """
        Insert single document into collection
        
        Args:
            collection_name: Name of collection
            document: Document to insert
        
        Returns:
            True if successful, False otherwise
        """
        if self.db is None:
            # In-memory fallback
            if collection_name not in self.in_memory_fallback:
                self.in_memory_fallback[collection_name] = []
            self.in_memory_fallback[collection_name].append(document)
            return True
        
        try:
            collection = self.db[collection_name]
            collection.insert_one(document)
            return True
        except Exception as e:
            log_error(f"Insert failed in {collection_name}: {e}")
            return False
    
    def insert_many(self, collection_name: str, documents: List[Dict]) -> bool:
        """
        Insert multiple documents into collection
        
        Args:
            collection_name: Name of collection
            documents: List of documents to insert
        
        Returns:
            True if successful, False otherwise
        """
        if self.db is None:
            # In-memory fallback
            if collection_name not in self.in_memory_fallback:
                self.in_memory_fallback[collection_name] = []
            self.in_memory_fallback[collection_name].extend(documents)
            return True
        
        try:
            collection = self.db[collection_name]
            collection.insert_many(documents)
            return True
        except Exception as e:
            log_error(f"Batch insert failed in {collection_name}: {e}")
            return False
    
    def find_one(self, collection_name: str, query: Dict) -> Optional[Dict]:
        """
        Find single document in collection
        
        Args:
            collection_name: Name of collection
            query: Query filter
        
        Returns:
            Document if found, None otherwise
        """
        if self.db is None:
            # In-memory fallback
            collection = self.in_memory_fallback.get(collection_name, [])
            for doc in collection:
                if self._matches_query(doc, query):
                    return doc
            return None
        
        try:
            collection = self.db[collection_name]
            return collection.find_one(query)
        except Exception as e:
            log_error(f"Find one failed in {collection_name}: {e}")
            return None
    
    def find_many(self, collection_name: str, query: Dict = None, 
                  limit: int = None, sort_by: str = None) -> List[Dict]:
        """
        Find multiple documents in collection
        
        Args:
            collection_name: Name of collection
            query: Query filter (optional)
            limit: Maximum results (optional)
            sort_by: Sort field (optional)
        
        Returns:
            List of documents
        """
        if self.db is None:
            # In-memory fallback
            collection = self.in_memory_fallback.get(collection_name, [])
            results = collection
            if query:
                results = [d for d in results if self._matches_query(d, query)]
            if limit:
                results = results[:limit]
            return results
        
        try:
            collection = self.db[collection_name]
            cursor = collection.find(query or {})
            if sort_by:
                cursor = cursor.sort(sort_by, -1)
            if limit:
                cursor = cursor.limit(limit)
            return list(cursor)
        except Exception as e:
            log_error(f"Find many failed in {collection_name}: {e}")
            return []
    
    def update_one(self, collection_name: str, query: Dict, updates: Dict) -> bool:
        """
        Update single document in collection
        
        Args:
            collection_name: Name of collection
            query: Query filter
            updates: Update data
        
        Returns:
            True if successful, False otherwise
        """
        if self.db is None:
            # In-memory fallback
            collection = self.in_memory_fallback.get(collection_name, [])
            for doc in collection:
                if self._matches_query(doc, query):
                    doc.update(updates)
                    return True
            return False
        
        try:
            collection = self.db[collection_name]
            result = collection.update_one(query, {'$set': updates})
            return result.modified_count > 0
        except Exception as e:
            log_error(f"Update failed in {collection_name}: {e}")
            return False
    
    def delete_one(self, collection_name: str, query: Dict) -> bool:
        """
        Delete single document from collection
        
        Args:
            collection_name: Name of collection
            query: Query filter
        
        Returns:
            True if successful, False otherwise
        """
        if self.db is None:
            # In-memory fallback
            collection = self.in_memory_fallback.get(collection_name, [])
            for i, doc in enumerate(collection):
                if self._matches_query(doc, query):
                    collection.pop(i)
                    return True
            return False
        
        try:
            collection = self.db[collection_name]
            result = collection.delete_one(query)
            return result.deleted_count > 0
        except Exception as e:
            log_error(f"Delete failed in {collection_name}: {e}")
            return False
    
    def count(self, collection_name: str, query: Dict = None) -> int:
        """
        Count documents in collection
        
        Args:
            collection_name: Name of collection
            query: Query filter (optional)
        
        Returns:
            Document count
        """
        if self.db is None:
            # In-memory fallback
            collection = self.in_memory_fallback.get(collection_name, [])
            if query:
                return len([d for d in collection if self._matches_query(d, query)])
            return len(collection)
        
        try:
            collection = self.db[collection_name]
            return collection.count_documents(query or {})
        except Exception as e:
            log_error(f"Count failed in {collection_name}: {e}")
            return 0
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _matches_query(self, doc: Dict, query: Dict) -> bool:
        """Check if document matches query (simple matching for in-memory)"""
        for key, value in query.items():
            if key not in doc or doc[key] != value:
                return False
        return True
    
    def get_collection(self, collection_name: str):
        """
        Get collection object directly
        Returns MongoDB collection or in-memory list
        """
        if self.db is None:
            return self.in_memory_fallback.get(collection_name, [])
        return self.db[collection_name]
    
    def get_database(self):
        """Get database object directly"""
        return self.db
    
    def is_connected(self) -> bool:
        """Check if connected to MongoDB"""
        return self.db is not None
    
    def get_connection_status(self) -> Dict:
        """Get connection status information"""
        return {
            'connected': self.is_connected(),
            'database': self.db_name if self.is_connected() else 'In-Memory',
            'connection_string': self.connection_string[:50] + '...' if len(self.connection_string) > 50 else self.connection_string,
            'storage_type': 'MongoDB' if self.is_connected() else 'In-Memory'
        }
    
    # ========================================================================
    # ADMIN OPERATIONS
    # ========================================================================
    
    def list_collections(self) -> List[str]:
        """List all collections in database"""
        if self.db is None:
            return list(self.in_memory_fallback.keys())
        try:
            return self.db.list_collection_names()
        except Exception as e:
            log_error(f"Failed to list collections: {e}")
            return []
    
    def get_collection_stats(self) -> Dict:
        """Get statistics for all collections"""
        stats = {}
        for collection_name in self.list_collections():
            count = self.count(collection_name)
            stats[collection_name] = {
                'count': count,
                'collection': collection_name
            }
        return stats
    
    def delete_old_documents(self, collection_name: str, days: int = 90) -> int:
        """
        Delete documents older than N days (Feature 29)
        
        Args:
            collection_name: Name of collection
            days: Delete documents older than this many days
        
        Returns:
            Number of deleted documents
        """
        if self.db is None:
            log_warning("Cannot delete old documents in in-memory storage")
            return 0
        
        try:
            from datetime import datetime, timedelta
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            collection = self.db[collection_name]
            result = collection.delete_many({
                'date': {'$lt': cutoff_date}
            })
            return result.deleted_count
        except Exception as e:
            log_error(f"Failed to delete old documents: {e}")
            return 0
    
    def backup_database(self, backup_path: str) -> bool:
        """
        Backup database (Feature 29)
        
        Args:
            backup_path: Path to save backup
        
        Returns:
            True if successful, False otherwise
        """
        import json
        from pathlib import Path
        
        try:
            backup_data = {}
            for collection_name in self.list_collections():
                docs = self.find_many(collection_name)
                # Convert to JSON-serializable format
                backup_data[collection_name] = [
                    {k: (str(v) if not isinstance(v, (str, int, float, bool, list, dict)) else v) 
                     for k, v in doc.items()}
                    for doc in docs
                ]
            
            Path(backup_path).parent.mkdir(parents=True, exist_ok=True)
            with open(backup_path, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            log_success(f"Database backed up to {backup_path}")
            return True
        except Exception as e:
            log_error(f"Backup failed: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            log_info("Database connection closed")
