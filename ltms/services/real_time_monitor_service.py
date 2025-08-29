#!/usr/bin/env python3
"""
Real-Time Documentation Monitoring Service

Provides real-time file system monitoring with automatic documentation generation
when source code files change. Implements complete background monitoring with
state persistence and error recovery.
"""

import asyncio
import logging
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set, Callable, Any
import json
import os

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent, FileDeletedEvent

# Local imports
from ltms.config.json_config_loader import get_config
from ltms.tools.docs.documentation_actions import documentation_action

logger = logging.getLogger(__name__)


class RealTimeDocumentationMonitor(FileSystemEventHandler):
    """
    File system event handler for real-time documentation synchronization.
    
    Monitors source code files and automatically triggers documentation generation
    when changes are detected. Provides comprehensive event handling, state
    persistence, and error recovery.
    """
    
    def __init__(self, project_id: str, monitor_manager: 'DocumentationMonitorManager'):
        """
        Initialize the documentation monitor.
        
        Args:
            project_id: Unique identifier for the project
            monitor_manager: Reference to the manager instance
        """
        super().__init__()
        self.project_id = project_id
        self.monitor_manager = monitor_manager
        self.logger = logging.getLogger(f"{__name__}.RealTimeDocumentationMonitor.{project_id}")
        
        # Track processed events to avoid duplicates
        self._recent_events: Set[str] = set()
        self._event_lock = threading.Lock()
        
    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return
            
        self._handle_file_event(event.src_path, 'modified')
    
    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return
            
        self._handle_file_event(event.src_path, 'created')
    
    def on_deleted(self, event):
        """Handle file deletion events."""
        if event.is_directory:
            return
            
        self._handle_file_event(event.src_path, 'deleted')
    
    def _handle_file_event(self, file_path: str, event_type: str):
        """
        Process file system events and trigger documentation updates.
        
        Args:
            file_path: Path to the file that changed
            event_type: Type of event (modified, created, deleted)
        """
        try:
            file_path = os.path.abspath(file_path)
            
            # Check if this file should be monitored
            if not self._should_monitor_file(file_path):
                return
            
            # Avoid duplicate processing of rapid events
            event_key = f"{file_path}:{event_type}"
            with self._event_lock:
                if event_key in self._recent_events:
                    return
                self._recent_events.add(event_key)
                
                # Clean old events (keep only last 100)
                if len(self._recent_events) > 100:
                    self._recent_events.clear()
            
            self.logger.info(f"File {event_type}: {file_path}")
            
            # Log the event to database
            self._log_file_event(file_path, event_type)
            
            # Trigger documentation update
            if event_type in ['modified', 'created']:
                self._trigger_documentation_update(file_path)
                
        except Exception as e:
            self.logger.error(f"Error handling file event {event_type} for {file_path}: {e}")
    
    def _should_monitor_file(self, file_path: str) -> bool:
        """
        Check if a file should be monitored for documentation updates.
        
        Args:
            file_path: Path to check
            
        Returns:
            bool: True if file should be monitored
        """
        # Get monitored extensions and paths from manager
        monitored_extensions = self.monitor_manager.get_monitored_extensions(self.project_id)
        monitored_paths = self.monitor_manager.get_monitored_paths(self.project_id)
        
        file_path = Path(file_path)
        
        # Check extension
        if file_path.suffix not in monitored_extensions:
            return False
        
        # Check if file is within monitored paths
        for monitored_path in monitored_paths:
            try:
                if file_path.is_relative_to(Path(monitored_path)):
                    return True
            except ValueError:
                # is_relative_to can raise ValueError
                continue
        
        return False
    
    def _log_file_event(self, file_path: str, event_type: str):
        """
        Log file event to database for tracking and debugging.
        
        Args:
            file_path: Path to the file
            event_type: Type of event
        """
        try:
            config = get_config()
            db_path = config.get_db_path()
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Create events table if not exists
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS file_monitor_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        project_id TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        processed BOOLEAN DEFAULT FALSE,
                        error_message TEXT
                    )
                ''')
                
                # Insert event
                cursor.execute('''
                    INSERT INTO file_monitor_events 
                    (project_id, file_path, event_type, timestamp)
                    VALUES (?, ?, ?, ?)
                ''', (
                    self.project_id,
                    file_path,
                    event_type,
                    datetime.now(timezone.utc).isoformat()
                ))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to log file event: {e}")
    
    def _trigger_documentation_update(self, file_path: str):
        """
        Trigger documentation update for a changed file.
        
        Args:
            file_path: Path to the file that changed
        """
        try:
            # Read file content
            if not os.path.exists(file_path):
                self.logger.warning(f"File no longer exists: {file_path}")
                return
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Trigger API documentation generation
            result = documentation_action(
                action='generate_api_docs',
                project_id=self.project_id,
                source_files={file_path: content},
                output_format='markdown'
            )
            
            if result.get('success'):
                self.logger.info(f"Documentation updated for {file_path}")
                self._mark_event_processed(file_path)
            else:
                error_msg = result.get('error', 'Unknown error')
                self.logger.error(f"Documentation update failed for {file_path}: {error_msg}")
                self._mark_event_error(file_path, error_msg)
                
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Error triggering documentation update for {file_path}: {error_msg}")
            self._mark_event_error(file_path, error_msg)
    
    def _mark_event_processed(self, file_path: str):
        """Mark the latest event for a file as processed."""
        self._update_event_status(file_path, processed=True, error_message=None)
    
    def _mark_event_error(self, file_path: str, error_message: str):
        """Mark the latest event for a file as having an error."""
        self._update_event_status(file_path, processed=False, error_message=error_message)
    
    def _update_event_status(self, file_path: str, processed: bool, error_message: Optional[str]):
        """
        Update the status of the most recent event for a file.
        
        Args:
            file_path: Path to the file
            processed: Whether the event was processed successfully
            error_message: Error message if processing failed
        """
        try:
            config = get_config()
            db_path = config.get_db_path()
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Update the most recent event for this file and project
                cursor.execute('''
                    UPDATE file_monitor_events
                    SET processed = ?, error_message = ?
                    WHERE project_id = ? AND file_path = ?
                    AND id = (
                        SELECT MAX(id) FROM file_monitor_events 
                        WHERE project_id = ? AND file_path = ?
                    )
                ''', (
                    processed,
                    error_message,
                    self.project_id,
                    file_path,
                    self.project_id,
                    file_path
                ))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to update event status: {e}")


class DocumentationMonitorManager:
    """
    Manager for real-time documentation monitoring across multiple projects.
    
    Handles observer lifecycle, state persistence, and configuration management
    for file system monitoring and documentation synchronization.
    """
    
    def __init__(self):
        """Initialize the monitor manager."""
        self.observers: Dict[str, Observer] = {}
        self.monitors: Dict[str, RealTimeDocumentationMonitor] = {}
        self.monitoring_configs: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self.logger = logging.getLogger(f"{__name__}.DocumentationMonitorManager")
        
        # Initialize database schema
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database tables for monitoring state."""
        try:
            config = get_config()
            db_path = config.get_db_path()
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Create monitoring configurations table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS monitor_configs (
                        project_id TEXT PRIMARY KEY,
                        monitored_paths TEXT NOT NULL,
                        monitored_extensions TEXT NOT NULL,
                        sync_interval_ms INTEGER DEFAULT 100,
                        enabled BOOLEAN DEFAULT TRUE,
                        created_at TEXT NOT NULL,
                        last_updated TEXT NOT NULL
                    )
                ''')
                
                # Create monitoring status table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS monitor_status (
                        project_id TEXT PRIMARY KEY,
                        status TEXT NOT NULL,
                        started_at TEXT,
                        last_activity TEXT,
                        error_count INTEGER DEFAULT 0,
                        last_error TEXT
                    )
                ''')
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
    
    def start_monitoring(self, project_id: str, file_paths: List[str], 
                        monitored_extensions: Optional[List[str]] = None,
                        sync_interval_ms: int = 100) -> Dict[str, Any]:
        """
        Start real-time monitoring for a project.
        
        Args:
            project_id: Unique identifier for the project
            file_paths: List of paths to monitor
            monitored_extensions: List of file extensions to monitor
            sync_interval_ms: Sync interval in milliseconds (for compatibility)
            
        Returns:
            Dict with monitoring status and details
        """
        try:
            with self._lock:
                # Stop existing monitoring if active
                if project_id in self.observers:
                    self.stop_monitoring(project_id)
                
                # Set default extensions if not provided
                if monitored_extensions is None:
                    monitored_extensions = ['.py', '.md', '.txt', '.rst', '.json', '.yaml', '.yml']
                
                # Validate and filter existing paths
                valid_paths = []
                invalid_paths = []
                
                for path in file_paths:
                    if os.path.exists(path):
                        valid_paths.append(os.path.abspath(path))
                    else:
                        invalid_paths.append(path)
                
                if not valid_paths:
                    return {
                        'success': False,
                        'error': 'No valid paths to monitor',
                        'invalid_paths': invalid_paths
                    }
                
                # Store configuration
                config = {
                    'monitored_paths': valid_paths,
                    'monitored_extensions': monitored_extensions,
                    'sync_interval_ms': sync_interval_ms
                }
                self.monitoring_configs[project_id] = config
                self._save_monitoring_config(project_id, config)
                
                # Create monitor and observer
                monitor = RealTimeDocumentationMonitor(project_id, self)
                observer = Observer()
                
                # Add watches for all valid paths
                watch_count = 0
                for path in valid_paths:
                    try:
                        if os.path.isfile(path):
                            # Monitor parent directory for file changes
                            watch_path = os.path.dirname(path)
                        else:
                            # Monitor directory
                            watch_path = path
                        
                        observer.schedule(monitor, watch_path, recursive=True)
                        watch_count += 1
                        
                    except Exception as e:
                        self.logger.error(f"Failed to add watch for {path}: {e}")
                
                if watch_count == 0:
                    return {
                        'success': False,
                        'error': 'Failed to add any file watches',
                        'invalid_paths': file_paths
                    }
                
                # Start observer
                observer.start()
                
                # Store references
                self.observers[project_id] = observer
                self.monitors[project_id] = monitor
                
                # Update status
                self._update_monitoring_status(project_id, 'active', started_at=datetime.now(timezone.utc))
                
                self.logger.info(f"Started monitoring for project {project_id} with {watch_count} watches")
                
                return {
                    'success': True,
                    'project_id': project_id,
                    'monitoring_paths': valid_paths,
                    'invalid_paths': invalid_paths,
                    'monitored_extensions': monitored_extensions,
                    'watch_count': watch_count,
                    'sync_interval_ms': sync_interval_ms,
                    'monitor_started': datetime.now(timezone.utc).isoformat(),
                    'message': f'Real-time monitoring started for {len(valid_paths)} paths with {watch_count} active watches'
                }
                
        except Exception as e:
            error_msg = f"Failed to start monitoring: {str(e)}"
            self.logger.error(error_msg)
            self._update_monitoring_status(project_id, 'error', error_message=error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def stop_monitoring(self, project_id: str) -> Dict[str, Any]:
        """
        Stop monitoring for a project.
        
        Args:
            project_id: Project identifier
            
        Returns:
            Dict with stop status
        """
        try:
            with self._lock:
                if project_id not in self.observers:
                    return {
                        'success': False,
                        'error': f'No active monitoring for project {project_id}'
                    }
                
                # Stop observer
                observer = self.observers[project_id]
                observer.stop()
                observer.join(timeout=5.0)  # Wait up to 5 seconds
                
                # Clean up references
                del self.observers[project_id]
                del self.monitors[project_id]
                if project_id in self.monitoring_configs:
                    del self.monitoring_configs[project_id]
                
                # Update status
                self._update_monitoring_status(project_id, 'stopped')
                
                self.logger.info(f"Stopped monitoring for project {project_id}")
                
                return {
                    'success': True,
                    'project_id': project_id,
                    'message': 'Monitoring stopped successfully',
                    'stopped_at': datetime.now(timezone.utc).isoformat()
                }
                
        except Exception as e:
            error_msg = f"Failed to stop monitoring: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def get_monitoring_status(self, project_id: str) -> Dict[str, Any]:
        """
        Get monitoring status for a project.
        
        Args:
            project_id: Project identifier
            
        Returns:
            Dict with status information
        """
        try:
            with self._lock:
                is_active = project_id in self.observers
                
                # Get status from database
                config = get_config()
                db_path = config.get_db_path()
                
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Get monitoring status
                    cursor.execute('''
                        SELECT status, started_at, last_activity, error_count, last_error
                        FROM monitor_status
                        WHERE project_id = ?
                    ''', (project_id,))
                    
                    status_row = cursor.fetchone()
                    
                    # Get configuration
                    cursor.execute('''
                        SELECT monitored_paths, monitored_extensions, sync_interval_ms, enabled
                        FROM monitor_configs
                        WHERE project_id = ?
                    ''', (project_id,))
                    
                    config_row = cursor.fetchone()
                    
                    # Get recent events
                    cursor.execute('''
                        SELECT COUNT(*) as total_events,
                               SUM(CASE WHEN processed = 1 THEN 1 ELSE 0 END) as processed_events,
                               MAX(timestamp) as last_event
                        FROM file_monitor_events
                        WHERE project_id = ?
                    ''', (project_id,))
                    
                    events_row = cursor.fetchone()
                
                status_info = {
                    'project_id': project_id,
                    'is_active': is_active,
                    'status': status_row[0] if status_row else 'unknown',
                    'started_at': status_row[1] if status_row else None,
                    'last_activity': status_row[2] if status_row else None,
                    'error_count': status_row[3] if status_row else 0,
                    'last_error': status_row[4] if status_row else None
                }
                
                if config_row:
                    status_info.update({
                        'monitored_paths': json.loads(config_row[0]) if config_row[0] else [],
                        'monitored_extensions': json.loads(config_row[1]) if config_row[1] else [],
                        'sync_interval_ms': config_row[2],
                        'enabled': bool(config_row[3])
                    })
                
                if events_row:
                    status_info.update({
                        'total_events': events_row[0] or 0,
                        'processed_events': events_row[1] or 0,
                        'last_event': events_row[2]
                    })
                
                return {
                    'success': True,
                    **status_info
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to get monitoring status: {str(e)}"
            }
    
    def get_monitored_extensions(self, project_id: str) -> List[str]:
        """Get monitored file extensions for a project."""
        config = self.monitoring_configs.get(project_id, {})
        return config.get('monitored_extensions', ['.py', '.md', '.txt', '.rst'])
    
    def get_monitored_paths(self, project_id: str) -> List[str]:
        """Get monitored file paths for a project."""
        config = self.monitoring_configs.get(project_id, {})
        return config.get('monitored_paths', [])
    
    def _save_monitoring_config(self, project_id: str, config: Dict[str, Any]):
        """Save monitoring configuration to database."""
        try:
            db_config = get_config()
            db_path = db_config.get_db_path()
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO monitor_configs
                    (project_id, monitored_paths, monitored_extensions, sync_interval_ms, enabled, created_at, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    project_id,
                    json.dumps(config['monitored_paths']),
                    json.dumps(config['monitored_extensions']),
                    config['sync_interval_ms'],
                    True,
                    datetime.now(timezone.utc).isoformat(),
                    datetime.now(timezone.utc).isoformat()
                ))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to save monitoring config: {e}")
    
    def _update_monitoring_status(self, project_id: str, status: str, 
                                started_at: Optional[datetime] = None,
                                error_message: Optional[str] = None):
        """Update monitoring status in database."""
        try:
            config = get_config()
            db_path = config.get_db_path()
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Get current status
                cursor.execute('''
                    SELECT error_count FROM monitor_status WHERE project_id = ?
                ''', (project_id,))
                
                row = cursor.fetchone()
                error_count = (row[0] if row else 0)
                
                if error_message:
                    error_count += 1
                elif status == 'active':
                    error_count = 0  # Reset error count on successful start
                
                cursor.execute('''
                    INSERT OR REPLACE INTO monitor_status
                    (project_id, status, started_at, last_activity, error_count, last_error)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    project_id,
                    status,
                    started_at.isoformat() if started_at else None,
                    datetime.now(timezone.utc).isoformat(),
                    error_count,
                    error_message
                ))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to update monitoring status: {e}")
    
    def shutdown_all(self):
        """Shutdown all active monitoring."""
        with self._lock:
            for project_id in list(self.observers.keys()):
                self.stop_monitoring(project_id)


# Global manager instance
_monitor_manager: Optional[DocumentationMonitorManager] = None


def get_monitor_manager() -> DocumentationMonitorManager:
    """Get or create the global monitor manager instance."""
    global _monitor_manager
    if _monitor_manager is None:
        _monitor_manager = DocumentationMonitorManager()
    return _monitor_manager


def start_real_time_monitoring(project_id: str, file_paths: List[str], **kwargs) -> Dict[str, Any]:
    """
    Start real-time documentation monitoring for a project.
    
    Args:
        project_id: Unique identifier for the project
        file_paths: List of file/directory paths to monitor
        **kwargs: Additional configuration options
        
    Returns:
        Dict with monitoring status and details
    """
    manager = get_monitor_manager()
    return manager.start_monitoring(project_id, file_paths, **kwargs)


def stop_real_time_monitoring(project_id: str) -> Dict[str, Any]:
    """
    Stop real-time documentation monitoring for a project.
    
    Args:
        project_id: Project identifier
        
    Returns:
        Dict with stop status
    """
    manager = get_monitor_manager()
    return manager.stop_monitoring(project_id)


def get_real_time_monitoring_status(project_id: str) -> Dict[str, Any]:
    """
    Get real-time monitoring status for a project.
    
    Args:
        project_id: Project identifier
        
    Returns:
        Dict with status information
    """
    manager = get_monitor_manager()
    return manager.get_monitoring_status(project_id)


# Cleanup on module shutdown
import atexit

def _cleanup_monitoring():
    """Cleanup function called on module shutdown."""
    global _monitor_manager
    if _monitor_manager is not None:
        _monitor_manager.shutdown_all()

atexit.register(_cleanup_monitoring)