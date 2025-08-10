"""
Database Service - Unified Interface
===================================

Unified interface combining basic and advanced database operations.
Preserves API compatibility while using modular architecture.
"""

import logging
from config.settings import LTMCSettings
from .basic_database_service import BasicDatabaseService  
from .advanced_database_service import AdvancedDatabaseService


class DatabaseService:
    """
    Unified database service interface.
    
    Combines basic and advanced database operations while maintaining
    compatibility with existing tool implementations.
    """
    
    def __init__(self, settings: LTMCSettings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        
        # Initialize component services
        self.basic_service = BasicDatabaseService(settings)
        self.advanced_service = AdvancedDatabaseService(settings)
        
    async def initialize(self) -> None:
        """Initialize both component services."""
        await self.basic_service.initialize()
        await self.advanced_service.initialize()
    
    # Basic operations (delegate to basic_service)
    async def store_resource(self, file_name: str, resource_type: str, content: str):
        return await self.basic_service.store_resource(file_name, resource_type, content)
    
    async def get_resources_by_type(self, resource_type=None):
        return await self.basic_service.get_resources_by_type(resource_type)
    
    async def log_chat_message(self, conversation_id: str, role: str, content: str, 
                             agent_name=None, metadata=None, source_tool=None):
        return await self.basic_service.log_chat_message(
            conversation_id, role, content, agent_name, metadata, source_tool)
    
    async def get_chat_history(self, conversation_id: str, limit: int = 50):
        return await self.basic_service.get_chat_history(conversation_id, limit)
    
    # Advanced operations (delegate to advanced_service)
    async def add_todo(self, title: str, description: str, priority: str = "medium"):
        return await self.advanced_service.add_todo(title, description, priority)
    
    async def list_todos(self, status=None, priority=None, limit: int = 10, offset: int = 0):
        return await self.advanced_service.list_todos(status, priority, limit, offset)
    
    async def complete_todo(self, todo_id: int):
        return await self.advanced_service.complete_todo(todo_id)
    
    async def log_code_pattern(self, input_prompt: str, generated_code: str, result: str,
                             execution_time_ms=None, error_message=None, tags=None):
        return await self.advanced_service.log_code_pattern(
            input_prompt, generated_code, result, execution_time_ms, error_message, tags)
    
    async def get_code_patterns(self, query_tags=None, result_filter=None, limit: int = 10):
        return await self.advanced_service.get_code_patterns(query_tags, result_filter, limit)