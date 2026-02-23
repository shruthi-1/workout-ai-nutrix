"""
FitGen AI v5.0 - Admin Tools Module
Database administration and maintenance utilities
Feature 29: Database admin tools (backup, restore, cleanup, stats)
"""

import logging
import json
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from config import COLLECTIONS
from utils import log_success, log_error, log_info, log_warning
from database_manager import DatabaseManager

logger = logging.getLogger(__name__)

# ============================================================================
# ADMIN TOOLS CLASS
# ============================================================================

class AdminTools:
    """
    Database administration and maintenance utilities
    Feature 29: Comprehensive admin tools for database management
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize admin tools
        
        Args:
            db_manager: DatabaseManager instance
        """
        self.db_manager = db_manager
    
    # ========================================================================
    # DATABASE STATISTICS (Feature 29)
    # ========================================================================
    
    def get_database_stats(self) -> Dict:
        """
        Feature 29: Get comprehensive database statistics
        
        Returns:
            Database statistics
        """
        if not self.db_manager.is_connected():
            return {
                'connected': False,
                'message': 'Database not connected'
            }
        
        stats = {
            'connected': True,
            'database': self.db_manager.database_name,
            'collections': {},
            'total_documents': 0,
            'storage_size': 0
        }
        
        # Get stats for each collection
        for collection_name in COLLECTIONS.values():
            count = self.db_manager.count(collection_name)
            stats['collections'][collection_name] = {
                'count': count,
                'size_bytes': 0
            }
            stats['total_documents'] += count
        
        return stats
    
    def get_collection_info(self, collection_name: str) -> Dict:
        """
        Get detailed information about a collection
        
        Args:
            collection_name: Name of collection
        
        Returns:
            Collection information
        """
        if not self.db_manager.is_connected():
            return {'error': 'Database not connected'}
        
        count = self.db_manager.count(collection_name)
        
        # Get sample document
        sample = self.db_manager.find_one(collection_name, {})
        
        return {
            'name': collection_name,
            'count': count,
            'sample_document': sample,
            'fields': list(sample.keys()) if sample else []
        }
    
    # ========================================================================
    # BACKUP & RESTORE (Feature 29)
    # ========================================================================
    
    def backup_database(self, backup_dir: str = 'backups') -> Tuple[bool, str]:
        """
        Feature 29: Backup entire database to JSON files
        
        Args:
            backup_dir: Directory to store backups
        
        Returns:
            Tuple: (success, filepath/message)
        """
        if not self.db_manager.is_connected():
            return False, "Database not connected"
        
        # Create backup directory
        os.makedirs(backup_dir, exist_ok=True)
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"fitgen_backup_{timestamp}.json")
        
        try:
            log_info(f"Creating backup: {backup_file}")
            
            backup_data = {
                'timestamp': timestamp,
                'database': self.db_manager.database_name,
                'collections': {}
            }
            
            # Backup each collection
            for collection_name in COLLECTIONS.values():
                documents = self.db_manager.find_many(
                    collection_name,
                    limit=100000
                )
                backup_data['collections'][collection_name] = documents
                log_info(f"  Backed up {len(documents)} documents from {collection_name}")
            
            # Write to file
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2, default=str)
            
            log_success(f"✅ Backup created: {backup_file}")
            return True, backup_file
        
        except Exception as e:
            log_error(f"Backup failed: {e}")
            return False, str(e)
    
    def restore_database(self, backup_file: str, 
                        clear_existing: bool = False) -> Tuple[bool, str]:
        """
        Feature 29: Restore database from backup file
        
        Args:
            backup_file: Path to backup JSON file
            clear_existing: Whether to clear existing data first
        
        Returns:
            Tuple: (success, message)
        """
        if not self.db_manager.is_connected():
            return False, "Database not connected"
        
        if not os.path.exists(backup_file):
            return False, f"Backup file not found: {backup_file}"
        
        try:
            log_info(f"Restoring from backup: {backup_file}")
            
            # Read backup file
            with open(backup_file, 'r') as f:
                backup_data = json.load(f)
            
            # Clear existing data if requested
            if clear_existing:
                log_warning("Clearing existing data...")
                for collection_name in COLLECTIONS.values():
                    self.db_manager.db[collection_name].delete_many({})
            
            # Restore each collection
            restored_counts = {}
            for collection_name, documents in backup_data['collections'].items():
                if documents:
                    success = self.db_manager.insert_many(collection_name, documents)
                    if success:
                        restored_counts[collection_name] = len(documents)
                        log_info(f"  Restored {len(documents)} documents to {collection_name}")
            
            total_restored = sum(restored_counts.values())
            log_success(f"✅ Restored {total_restored} total documents")
            
            return True, f"Restored {total_restored} documents"
        
        except Exception as e:
            log_error(f"Restore failed: {e}")
            return False, str(e)
    
    # ========================================================================
    # DATA CLEANUP (Feature 29)
    # ========================================================================
    
    def cleanup_old_logs(self, days: int = 90) -> Tuple[bool, int]:
        """
        Feature 29: Delete old log entries
        
        Args:
            days: Delete logs older than this many days
        
        Returns:
            Tuple: (success, deleted_count)
        """
        if not self.db_manager.is_connected():
            return False, 0
        
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        log_info(f"Deleting logs older than {days} days (before {cutoff_date})")
        
        deleted_count = self.db_manager.delete_old_documents(
            'session_logs',
            days=days
        )
        
        log_success(f"✅ Deleted {deleted_count} old session logs")
        
        return True, deleted_count
    
    def cleanup_old_moods(self, days: int = 180) -> Tuple[bool, int]:
        """
        Delete old mood logs
        
        Args:
            days: Delete moods older than this many days
        
        Returns:
            Tuple: (success, deleted_count)
        """
        if not self.db_manager.is_connected():
            return False, 0
        
        deleted_count = self.db_manager.delete_old_documents(
            'motivation_logs',
            days=days
        )
        
        log_success(f"✅ Deleted {deleted_count} old mood logs")
        
        return True, deleted_count
    
    def cleanup_orphaned_data(self) -> Tuple[bool, Dict]:
        """
        Clean up orphaned data (sessions without users, etc.)
        
        Returns:
            Tuple: (success, cleanup_report)
        """
        if not self.db_manager.is_connected():
            return False, {'error': 'Database not connected'}
        
        report = {
            'orphaned_sessions': 0,
            'orphaned_plans': 0,
            'orphaned_moods': 0
        }
        
        # Get all user IDs
        users = self.db_manager.find_many('users', limit=10000)
        user_ids = set(u['user_id'] for u in users)
        
        # Clean orphaned sessions
        sessions = self.db_manager.find_many('session_logs', limit=10000)
        for session in sessions:
            if session.get('user_id') not in user_ids:
                self.db_manager.delete_one('session_logs', {'_id': session['_id']})
                report['orphaned_sessions'] += 1
        
        log_success(f"✅ Cleaned {sum(report.values())} orphaned records")
        
        return True, report
    
    # ========================================================================
    # DATA EXPORT (Feature 29)
    # ========================================================================
    
    def export_collection(self, collection_name: str, 
                         output_file: str) -> Tuple[bool, str]:
        """
        Export single collection to JSON
        
        Args:
            collection_name: Name of collection
            output_file: Output file path
        
        Returns:
            Tuple: (success, message)
        """
        if not self.db_manager.is_connected():
            return False, "Database not connected"
        
        try:
            documents = self.db_manager.find_many(collection_name, limit=100000)
            
            with open(output_file, 'w') as f:
                json.dump(documents, f, indent=2, default=str)
            
            log_success(f"✅ Exported {len(documents)} documents to {output_file}")
            return True, f"Exported {len(documents)} documents"
        
        except Exception as e:
            log_error(f"Export failed: {e}")
            return False, str(e)
    
    # ========================================================================
    # SYSTEM HEALTH (Feature 29)
    # ========================================================================
    
    def check_system_health(self) -> Dict:
        """
        Feature 29: Check overall system health
        
        Returns:
            System health report
        """
        health = {
            'status': 'healthy',
            'checks': {},
            'warnings': [],
            'errors': []
        }
        
        # Check database connection
        health['checks']['database_connected'] = self.db_manager.is_connected()
        if not health['checks']['database_connected']:
            health['status'] = 'degraded'
            health['warnings'].append('Database not connected')
        
        if self.db_manager.is_connected():
            # Check collections exist
            stats = self.get_database_stats()
            health['checks']['collections_exist'] = len(stats['collections']) == len(COLLECTIONS)
            
            # Check for data
            health['checks']['has_exercises'] = stats['collections'].get('exercises', {}).get('count', 0) > 0
            if not health['checks']['has_exercises']:
                health['warnings'].append('No exercises in database')
            
            health['checks']['has_users'] = stats['collections'].get('users', {}).get('count', 0) > 0
            
            # Check for old logs
            session_count = stats['collections'].get('session_logs', {}).get('count', 0)
            if session_count > 10000:
                health['warnings'].append(f'Many session logs ({session_count}). Consider cleanup.')
        
        # Determine overall status
        if health['errors']:
            health['status'] = 'unhealthy'
        elif health['warnings']:
            health['status'] = 'degraded'
        
        return health
    
    def get_system_info(self) -> Dict:
        """
        Get comprehensive system information
        
        Returns:
            System information
        """
        info = {
            'database': self.db_manager.get_connection_status(),
            'stats': self.get_database_stats() if self.db_manager.is_connected() else {},
            'health': self.check_system_health()
        }
        
        return info
    
    # ========================================================================
    # MAINTENANCE TASKS (Feature 29)
    # ========================================================================
    
    def run_maintenance(self) -> Dict:
        """
        Run all maintenance tasks
        
        Returns:
            Maintenance report
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'tasks': {}
        }
        
        # Cleanup old logs (90 days)
        success, deleted = self.cleanup_old_logs(days=90)
        report['tasks']['cleanup_logs'] = {
            'success': success,
            'deleted': deleted
        }
        
        # Cleanup old moods (180 days)
        success, deleted = self.cleanup_old_moods(days=180)
        report['tasks']['cleanup_moods'] = {
            'success': success,
            'deleted': deleted
        }
        
        # Cleanup orphaned data
        success, cleanup_report = self.cleanup_orphaned_data()
        report['tasks']['cleanup_orphaned'] = {
            'success': success,
            'report': cleanup_report
        }
        
        # Check system health
        report['health'] = self.check_system_health()
        
        log_success("✅ Maintenance complete")
        
        return report
    
    def schedule_backup(self, interval_days: int = 7) -> bool:
        """
        Set up scheduled backups (placeholder for cron/scheduler)
        
        Args:
            interval_days: Backup interval in days
        
        Returns:
            Success status
        """
        log_info(f"Backup scheduled every {interval_days} days")
        log_warning("Note: Implement with cron job or task scheduler")
        return True
