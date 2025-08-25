"""
LTMC Tech Stack Alignment System

Smart modularized tech stack validation and enforcement system
for preventing AI agent tech stack drift.

Components:
- validator: TechStackValidator for AST-based pattern validation
- registry: StackRegistry for configuration management
- monitor: EventLoopMonitor for conflict detection
- alignment_agent: Multi-agent coordination
- coordination_network: Network utilities

Performance SLA: <500ms operations
No mocks, stubs, or placeholders - production ready only.
"""

from .validator import TechStackValidator, ValidationResult, ValidationSeverity
from .registry import StackRegistry
from .monitor import EventLoopMonitor
from .alignment_agent import TechStackAlignmentAgent, CoordinationMode, MessageType
from .coordination_network import create_coordination_network, coordinate_network_validation

__all__ = [
    'TechStackValidator', 'ValidationResult', 'ValidationSeverity',
    'StackRegistry', 
    'EventLoopMonitor',
    'TechStackAlignmentAgent', 'CoordinationMode', 'MessageType',
    'create_coordination_network', 'coordinate_network_validation'
]