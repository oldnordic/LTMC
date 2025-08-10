"""
Blueprint Data Models for Phase 3 Component 1: Neo4j Blueprint Enhancement.

This module implements comprehensive blueprint data structures including:
- BlueprintNode: Base node for code structure elements  
- FunctionNode, ClassNode, ModuleNode, APIEndpointNode: Specialized nodes
- DocumentationFile: Documentation integration
- CodeStructure: Complete code structure representation
- BlueprintRelationship: Node relationships and dependencies

Performance Requirements:
- Node creation: <2ms per node
- Relationship creation: <1ms per relationship
- Structure analysis: <10ms per file

Security Integration:
- Project isolation via project_id
- Path validation for file operations
- Input sanitization for all node properties
"""

import re
import json
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional, Union, Set
from dataclasses import dataclass, field
from pathlib import Path


class BlueprintNodeType(Enum):
    """Types of blueprint nodes for code structure mapping."""
    
    FUNCTION = "function"
    CLASS = "class"
    MODULE = "module"
    API_ENDPOINT = "api_endpoint"
    IMPORT = "import"
    VARIABLE = "variable"
    DECORATOR = "decorator"


class RelationshipType(Enum):
    """Types of relationships between blueprint nodes."""
    
    BELONGS_TO = "BELONGS_TO"
    CALLS = "CALLS"
    IMPORTS = "IMPORTS"
    INHERITS = "INHERITS"
    DECORATES = "DECORATES"
    DEPENDS_ON = "DEPENDS_ON"
    HANDLED_BY = "HANDLED_BY"
    DEFINES = "DEFINES"
    USES = "USES"


class ConsistencyLevel(Enum):
    """Consistency levels for blueprint-code validation."""
    
    PERFECT = (1.0, "Perfect match between blueprint and code")
    HIGH = (0.8, "High consistency with minor differences")
    MEDIUM = (0.6, "Medium consistency with some differences")  
    LOW = (0.4, "Low consistency with major differences")
    NONE = (0.0, "No consistency, complete mismatch")
    
    def __init__(self, score: float, description: str):
        self.score = score
        self.description = description


@dataclass
class BlueprintNode:
    """Base blueprint node for code structure elements."""
    
    node_id: str
    name: str
    node_type: BlueprintNodeType
    project_id: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    docstring: Optional[str] = None
    complexity_score: float = 0.5
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate node after initialization."""
        if not self.node_id or not self.name:
            raise ValueError("node_id and name are required")
        
        if not re.match(r'^[a-zA-Z0-9_-]+$', self.node_id):
            raise ValueError("node_id must contain only alphanumeric characters, underscores, and hyphens")
        
        if self.complexity_score < 0.0 or self.complexity_score > 1.0:
            raise ValueError("complexity_score must be between 0.0 and 1.0")
        
        if self.file_path and not Path(self.file_path).is_absolute():
            # Convert to absolute path if relative
            self.file_path = str(Path(self.file_path).resolve())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary for serialization."""
        return {
            "node_id": self.node_id,
            "name": self.name,
            "node_type": self.node_type.value,
            "project_id": self.project_id,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "docstring": self.docstring,
            "complexity_score": self.complexity_score,
            "properties": self.properties,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BlueprintNode':
        """Create BlueprintNode from dictionary."""
        return cls(
            node_id=data["node_id"],
            name=data["name"],
            node_type=BlueprintNodeType(data["node_type"]),
            project_id=data["project_id"],
            file_path=data.get("file_path"),
            line_number=data.get("line_number"),
            docstring=data.get("docstring"),
            complexity_score=data.get("complexity_score", 0.5),
            properties=data.get("properties", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"])
        )


@dataclass
class FunctionNode(BlueprintNode):
    """Specialized node for function definitions."""
    
    is_async: bool = False
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    return_type: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    is_method: bool = False
    visibility: str = "public"  # public, private, protected
    
    def __post_init__(self):
        super().__post_init__()
        self.node_type = BlueprintNodeType.FUNCTION
        
        # Validate parameters structure
        for param in self.parameters:
            if not isinstance(param, dict) or "name" not in param:
                raise ValueError("Parameters must be dictionaries with 'name' field")
    
    def get_signature(self) -> str:
        """Get function signature string."""
        params = ", ".join([
            f"{p['name']}: {p.get('type', 'Any')}" if 'type' in p else p['name']
            for p in self.parameters
        ])
        
        async_prefix = "async " if self.is_async else ""
        return_type = f" -> {self.return_type}" if self.return_type else ""
        
        return f"{async_prefix}def {self.name}({params}){return_type}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert function node to dictionary."""
        data = super().to_dict()
        data.update({
            "is_async": self.is_async,
            "parameters": self.parameters,
            "return_type": self.return_type,
            "decorators": self.decorators,
            "is_method": self.is_method,
            "visibility": self.visibility
        })
        return data


@dataclass
class ClassNode(BlueprintNode):
    """Specialized node for class definitions."""
    
    base_classes: List[str] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    attributes: List[Dict[str, Any]] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
    is_abstract: bool = False
    
    def __post_init__(self):
        super().__post_init__()
        self.node_type = BlueprintNodeType.CLASS
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert class node to dictionary."""
        data = super().to_dict()
        data.update({
            "base_classes": self.base_classes,
            "methods": self.methods,
            "attributes": self.attributes,
            "decorators": self.decorators,
            "is_abstract": self.is_abstract
        })
        return data


@dataclass
class ModuleNode(BlueprintNode):
    """Specialized node for module definitions."""
    
    imports: List[Dict[str, Any]] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    variables: List[Dict[str, Any]] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        super().__post_init__()
        self.node_type = BlueprintNodeType.MODULE
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert module node to dictionary."""
        data = super().to_dict()
        data.update({
            "imports": self.imports,
            "functions": self.functions,
            "classes": self.classes,
            "variables": self.variables,
            "exports": self.exports
        })
        return data


@dataclass
class APIEndpointNode(BlueprintNode):
    """Specialized node for API endpoint definitions."""
    
    http_method: str = "GET"
    path: str = "/"
    handler_function: Optional[str] = None
    request_schema: Optional[Dict[str, Any]] = None
    response_schema: Optional[Dict[str, Any]] = None
    middleware: List[str] = field(default_factory=list)
    authentication_required: bool = False
    
    def __post_init__(self):
        super().__post_init__()
        self.node_type = BlueprintNodeType.API_ENDPOINT
        
        # Validate HTTP method
        valid_methods = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}
        if self.http_method.upper() not in valid_methods:
            raise ValueError(f"Invalid HTTP method: {self.http_method}")
        self.http_method = self.http_method.upper()
    
    def get_endpoint_signature(self) -> str:
        """Get endpoint signature string."""
        return f"{self.http_method} {self.path}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert API endpoint node to dictionary."""
        data = super().to_dict()
        data.update({
            "http_method": self.http_method,
            "path": self.path,
            "handler_function": self.handler_function,
            "request_schema": self.request_schema,
            "response_schema": self.response_schema,
            "middleware": self.middleware,
            "authentication_required": self.authentication_required
        })
        return data


@dataclass
class BlueprintRelationship:
    """Relationship between blueprint nodes."""
    
    relationship_id: str
    source_node_id: str
    target_node_id: str
    relationship_type: RelationshipType
    properties: Dict[str, Any] = field(default_factory=dict)
    strength: float = 1.0  # Relationship strength (0.0 to 1.0)
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate relationship after initialization."""
        if not self.relationship_id or not self.source_node_id or not self.target_node_id:
            raise ValueError("relationship_id, source_node_id, and target_node_id are required")
        
        if self.source_node_id == self.target_node_id:
            raise ValueError("Node cannot have relationship with itself")
        
        if self.strength < 0.0 or self.strength > 1.0:
            raise ValueError("strength must be between 0.0 and 1.0")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert relationship to dictionary."""
        return {
            "relationship_id": self.relationship_id,
            "source_node_id": self.source_node_id,
            "target_node_id": self.target_node_id,
            "relationship_type": self.relationship_type.value,
            "properties": self.properties,
            "strength": self.strength,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BlueprintRelationship':
        """Create BlueprintRelationship from dictionary."""
        return cls(
            relationship_id=data["relationship_id"],
            source_node_id=data["source_node_id"],
            target_node_id=data["target_node_id"],
            relationship_type=RelationshipType(data["relationship_type"]),
            properties=data.get("properties", {}),
            strength=data.get("strength", 1.0),
            created_at=datetime.fromisoformat(data["created_at"])
        )


@dataclass
class DocumentationFile:
    """Documentation file representation for blueprint documentation."""
    
    file_id: str
    file_path: str
    title: str
    format: str = "markdown"  # markdown, rst, html
    content: str = ""
    blueprint_nodes: List[str] = field(default_factory=list)  # Node IDs covered
    generated_at: datetime = field(default_factory=datetime.now)
    template_used: Optional[str] = None
    
    def __post_init__(self):
        """Validate documentation file."""
        if not self.file_id or not self.file_path or not self.title:
            raise ValueError("file_id, file_path, and title are required")
        
        valid_formats = {"markdown", "rst", "html", "txt"}
        if self.format not in valid_formats:
            raise ValueError(f"Invalid format: {self.format}. Must be one of {valid_formats}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert documentation file to dictionary."""
        return {
            "file_id": self.file_id,
            "file_path": self.file_path,
            "title": self.title,
            "format": self.format,
            "content": self.content,
            "blueprint_nodes": self.blueprint_nodes,
            "generated_at": self.generated_at.isoformat(),
            "template_used": self.template_used
        }


@dataclass
class CodeStructure:
    """Complete code structure representation for a file or module."""
    
    structure_id: str
    file_path: str
    project_id: str
    nodes: List[BlueprintNode] = field(default_factory=list)
    relationships: List[BlueprintRelationship] = field(default_factory=list)
    analysis_timestamp: datetime = field(default_factory=datetime.now)
    consistency_score: float = 1.0
    inconsistencies: List[Dict[str, Any]] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate code structure."""
        if not self.structure_id or not self.file_path or not self.project_id:
            raise ValueError("structure_id, file_path, and project_id are required")
        
        if self.consistency_score < 0.0 or self.consistency_score > 1.0:
            raise ValueError("consistency_score must be between 0.0 and 1.0")
    
    def add_node(self, node: BlueprintNode):
        """Add a node to the structure."""
        if node.project_id != self.project_id:
            raise ValueError("Node project_id must match structure project_id")
        self.nodes.append(node)
    
    def add_relationship(self, relationship: BlueprintRelationship):
        """Add a relationship to the structure."""
        # Verify that both nodes exist in the structure
        node_ids = {node.node_id for node in self.nodes}
        if relationship.source_node_id not in node_ids:
            raise ValueError(f"Source node {relationship.source_node_id} not found in structure")
        if relationship.target_node_id not in node_ids:
            raise ValueError(f"Target node {relationship.target_node_id} not found in structure")
        
        self.relationships.append(relationship)
    
    def get_nodes_by_type(self, node_type: BlueprintNodeType) -> List[BlueprintNode]:
        """Get all nodes of a specific type."""
        return [node for node in self.nodes if node.node_type == node_type]
    
    def get_node_relationships(self, node_id: str, direction: str = "both") -> List[BlueprintRelationship]:
        """Get relationships for a specific node."""
        relationships = []
        
        for rel in self.relationships:
            if direction == "outgoing" and rel.source_node_id == node_id:
                relationships.append(rel)
            elif direction == "incoming" and rel.target_node_id == node_id:
                relationships.append(rel)
            elif direction == "both" and (rel.source_node_id == node_id or rel.target_node_id == node_id):
                relationships.append(rel)
        
        return relationships
    
    def calculate_complexity_metrics(self) -> Dict[str, Any]:
        """Calculate complexity metrics for the code structure."""
        function_count = len(self.get_nodes_by_type(BlueprintNodeType.FUNCTION))
        class_count = len(self.get_nodes_by_type(BlueprintNodeType.CLASS))
        
        # Average complexity score
        avg_complexity = 0.0
        if self.nodes:
            avg_complexity = sum(node.complexity_score for node in self.nodes) / len(self.nodes)
        
        # Relationship density
        max_relationships = len(self.nodes) * (len(self.nodes) - 1)
        relationship_density = len(self.relationships) / max_relationships if max_relationships > 0 else 0.0
        
        return {
            "total_nodes": len(self.nodes),
            "function_count": function_count,
            "class_count": class_count,
            "relationship_count": len(self.relationships),
            "average_complexity": avg_complexity,
            "relationship_density": relationship_density,
            "consistency_score": self.consistency_score
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert code structure to dictionary."""
        return {
            "structure_id": self.structure_id,
            "file_path": self.file_path,
            "project_id": self.project_id,
            "nodes": [node.to_dict() for node in self.nodes],
            "relationships": [rel.to_dict() for rel in self.relationships],
            "analysis_timestamp": self.analysis_timestamp.isoformat(),
            "consistency_score": self.consistency_score,
            "inconsistencies": self.inconsistencies,
            "metrics": self.calculate_complexity_metrics()
        }


class BlueprintNodeFactory:
    """Factory for creating specialized blueprint nodes."""
    
    @staticmethod
    def create_function_node(
        node_id: str,
        name: str,
        project_id: str,
        is_async: bool = False,
        parameters: Optional[List[Dict[str, Any]]] = None,
        return_type: Optional[str] = None,
        **kwargs
    ) -> FunctionNode:
        """Create a function node."""
        return FunctionNode(
            node_id=node_id,
            name=name,
            project_id=project_id,
            is_async=is_async,
            parameters=parameters or [],
            return_type=return_type,
            **kwargs
        )
    
    @staticmethod
    def create_class_node(
        node_id: str,
        name: str,
        project_id: str,
        base_classes: Optional[List[str]] = None,
        methods: Optional[List[str]] = None,
        **kwargs
    ) -> ClassNode:
        """Create a class node."""
        return ClassNode(
            node_id=node_id,
            name=name,
            project_id=project_id,
            base_classes=base_classes or [],
            methods=methods or [],
            **kwargs
        )
    
    @staticmethod
    def create_module_node(
        node_id: str,
        name: str,
        project_id: str,
        file_path: str,
        **kwargs
    ) -> ModuleNode:
        """Create a module node."""
        return ModuleNode(
            node_id=node_id,
            name=name,
            project_id=project_id,
            file_path=file_path,
            **kwargs
        )
    
    @staticmethod
    def create_api_endpoint_node(
        node_id: str,
        name: str,
        project_id: str,
        http_method: str,
        path: str,
        **kwargs
    ) -> APIEndpointNode:
        """Create an API endpoint node."""
        return APIEndpointNode(
            node_id=node_id,
            name=name,
            project_id=project_id,
            http_method=http_method,
            path=path,
            **kwargs
        )


# Convenience functions for validation
def validate_node_data(node_data: Dict[str, Any]) -> bool:
    """Validate node data structure."""
    required_fields = {"node_id", "name", "node_type", "project_id"}
    return all(field in node_data for field in required_fields)


def validate_relationship_data(rel_data: Dict[str, Any]) -> bool:
    """Validate relationship data structure."""
    required_fields = {"relationship_id", "source_node_id", "target_node_id", "relationship_type"}
    return all(field in rel_data for field in required_fields)