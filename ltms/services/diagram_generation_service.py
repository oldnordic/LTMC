#!/usr/bin/env python3
"""
Diagram & Dependency Analysis Service for LTMC Documentation Generation.

This service generates real, code-driven diagrams including:
- Inheritance hierarchies with PlantUML
- Import dependency graphs with Graphviz
- Call graphs and usage patterns with Mermaid
- Architecture diagrams with comprehensive relationship mapping

Uses sh for external tool integration and rich for CLI visualization.
Supports embedding in Markdown/HTML for documentation generation.

Real implementations only - no stubs, mocks, or placeholders.
"""

import ast
import os
import tempfile
import subprocess
from typing import Dict, List, Optional, Set, Any, Union, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import logging
import json
import re

try:
    import sh
except ImportError:
    sh = None

try:
    from rich.console import Console
    from rich.tree import Tree
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.progress import Progress, SpinnerColumn, TextColumn
except ImportError:
    Console = None

# Import our existing services
from .cross_reference_service import (
    CrossReferenceEngine, 
    DocumentationSymbolTable,
    SymbolReference,
    CrossReference,
    InheritanceChain
)
from .advanced_documentation_service import (
    AdvancedDocumentationExtractor,
    ModuleDocumentation
)

logger = logging.getLogger(__name__)

class DiagramType(Enum):
    """Supported diagram types."""
    INHERITANCE = "inheritance"
    IMPORT_DEPENDENCY = "import_dependency" 
    CALL_GRAPH = "call_graph"
    ARCHITECTURE = "architecture"
    CLASS_DIAGRAM = "class_diagram"
    SEQUENCE = "sequence"

class DiagramFormat(Enum):
    """Supported output formats."""
    PNG = "png"
    SVG = "svg"
    PDF = "pdf"
    HTML = "html"
    ASCII = "ascii"

@dataclass
class DiagramGenerationOptions:
    """Configuration options for diagram generation."""
    diagram_type: DiagramType
    output_format: DiagramFormat = DiagramFormat.SVG
    output_path: Optional[str] = None
    include_private: bool = False
    include_external: bool = True
    max_depth: int = 5
    layout_engine: str = "dot"  # For Graphviz: dot, neato, fdp, sfdp, circo
    theme: str = "default"
    title: Optional[str] = None
    font_size: int = 12
    dpi: int = 300
    include_docstrings: bool = True
    group_by_module: bool = True
    show_relationships: bool = True
    custom_styles: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DiagramNode:
    """Represents a node in a diagram."""
    id: str
    label: str
    node_type: str  # class, function, module, etc.
    module_path: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    style: Dict[str, str] = field(default_factory=dict)

@dataclass
class DiagramEdge:
    """Represents an edge/relationship in a diagram."""
    source: str
    target: str
    relationship_type: str  # inherits, calls, imports, etc.
    label: Optional[str] = None
    style: Dict[str, str] = field(default_factory=dict)
    weight: float = 1.0

@dataclass
class GeneratedDiagram:
    """Container for generated diagram data."""
    diagram_type: DiagramType
    source_code: str  # PlantUML/Graphviz/Mermaid source
    output_format: DiagramFormat
    file_path: Optional[str] = None
    ascii_representation: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    generation_timestamp: str = ""
    nodes: List[DiagramNode] = field(default_factory=list)
    edges: List[DiagramEdge] = field(default_factory=list)

class PlantUMLGenerator:
    """Generates PlantUML diagrams for inheritance and class structures."""
    
    def __init__(self, options: DiagramGenerationOptions):
        self.options = options
        self.console = Console() if Console else None
    
    def generate_inheritance_diagram(self, symbol_table: DocumentationSymbolTable) -> str:
        """Generate PlantUML source for inheritance hierarchy."""
        plantuml_lines = ["@startuml"]
        
        if self.options.title:
            plantuml_lines.append(f"title {self.options.title}")
        
        # Add theme and styling
        plantuml_lines.extend([
            "!theme plain",
            "skinparam classAttributeIconSize 0",
            "skinparam classFontSize 12",
            "skinparam packageFontSize 14"
        ])
        
        # Process classes and inheritance chains
        processed_classes = set()
        
        for class_name, inheritance_chain in symbol_table.inheritance_chains.items():
            if class_name in processed_classes:
                continue
                
            # Add class definition
            class_symbol = symbol_table.symbols.get(class_name)
            if class_symbol and class_symbol.symbol_type == "class":
                class_simple_name = class_symbol.name
                
                # Add class with basic structure
                if inheritance_chain.is_abstract:
                    plantuml_lines.append(f"abstract class {class_simple_name}")
                else:
                    plantuml_lines.append(f"class {class_simple_name}")
                
                # Add inheritance relationships
                for base_class in inheritance_chain.base_classes:
                    base_symbol = symbol_table.symbols.get(f"{class_symbol.module_path}.{base_class}")
                    if base_symbol:
                        plantuml_lines.append(f"{base_class} <|-- {class_simple_name}")
                    else:
                        # External inheritance
                        if self.options.include_external:
                            plantuml_lines.append(f"class {base_class}")
                            plantuml_lines.append(f"{base_class} <|-- {class_simple_name}")
                
                # Add mixins as aggregation
                for mixin in inheritance_chain.mixins:
                    if self.options.include_external or mixin in symbol_table.symbols:
                        plantuml_lines.append(f"class {mixin}")
                        plantuml_lines.append(f"{class_simple_name} o-- {mixin} : uses")
                
                processed_classes.add(class_name)
        
        plantuml_lines.append("@enduml")
        return "\n".join(plantuml_lines)
    
    def generate_class_diagram(self, modules: List[ModuleDocumentation]) -> str:
        """Generate comprehensive class diagram with methods and attributes."""
        plantuml_lines = ["@startuml"]
        
        if self.options.title:
            plantuml_lines.append(f"title {self.options.title}")
            
        plantuml_lines.extend([
            "!theme plain",
            "skinparam classAttributeIconSize 0",
            "left to right direction"
        ])
        
        # Group by modules if requested
        if self.options.group_by_module:
            for module in modules:
                if module.classes:
                    plantuml_lines.append(f"package {module.name} {{")
                    
                    for class_doc in module.classes:
                        class_lines = [f"class {class_doc.name} {{"]
                        
                        # Add attributes
                        if hasattr(class_doc, 'attributes'):
                            for attr in class_doc.attributes:
                                visibility = "+" if attr.is_public else "-"
                                type_hint = f": {attr.type_hint}" if attr.type_hint else ""
                                class_lines.append(f"  {visibility}{attr.name}{type_hint}")
                        
                        # Add separator
                        if hasattr(class_doc, 'methods') and class_doc.methods:
                            class_lines.append("  --")
                        
                        # Add methods
                        if hasattr(class_doc, 'methods'):
                            for method in class_doc.methods:
                                if not self.options.include_private and method.name.startswith('_'):
                                    continue
                                    
                                visibility = "+" if not method.name.startswith('_') else "-"
                                params = ", ".join([p.name for p in method.parameters if p.name != 'self'])
                                return_type = f": {method.return_info.type_hint}" if method.return_info else ""
                                class_lines.append(f"  {visibility}{method.name}({params}){return_type}")
                        
                        class_lines.append("}")
                        plantuml_lines.extend(class_lines)
                    
                    plantuml_lines.append("}")
        
        plantuml_lines.append("@enduml")
        return "\n".join(plantuml_lines)

class GraphvizGenerator:
    """Generates Graphviz diagrams for dependency and call graphs."""
    
    def __init__(self, options: DiagramGenerationOptions):
        self.options = options
        self.console = Console() if Console else None
    
    def generate_import_dependency_graph(self, symbol_table: DocumentationSymbolTable) -> str:
        """Generate Graphviz DOT source for import dependencies."""
        dot_lines = [f"digraph import_dependencies {{"]
        
        # Graph attributes
        dot_lines.extend([
            f"  layout={self.options.layout_engine};",
            "  rankdir=LR;",
            "  node [shape=box, style=rounded];",
            f"  graph [fontsize={self.options.font_size}];"
        ])
        
        if self.options.title:
            dot_lines.append(f'  label="{self.options.title}";')
        
        # Track modules and their dependencies
        modules = {}
        dependencies = []
        
        # Extract import relationships
        for cross_ref in symbol_table.cross_references:
            if cross_ref.relationship_type == "imports":
                source_module = cross_ref.source_symbol.split('.')[0]
                target_module = cross_ref.target_symbol.split('.')[0]
                
                if source_module != target_module:
                    modules[source_module] = modules.get(source_module, set())
                    modules[target_module] = modules.get(target_module, set())
                    dependencies.append((source_module, target_module))
        
        # Add module nodes
        for module in modules:
            if module in symbol_table.modules:
                dot_lines.append(f'  "{module}" [label="{module}", fillcolor=lightblue, style=filled];')
            else:
                if self.options.include_external:
                    dot_lines.append(f'  "{module}" [label="{module}", fillcolor=lightgray, style=filled];')
        
        # Add dependency edges
        for source, target in set(dependencies):
            if self.options.include_external or (source in symbol_table.modules and target in symbol_table.modules):
                dot_lines.append(f'  "{source}" -> "{target}";')
        
        dot_lines.append("}")
        return "\n".join(dot_lines)
    
    def generate_call_graph(self, symbol_table: DocumentationSymbolTable) -> str:
        """Generate Graphviz DOT source for function call graph."""
        dot_lines = ["digraph call_graph {"]
        
        dot_lines.extend([
            f"  layout={self.options.layout_engine};",
            "  node [shape=ellipse];",
            f"  graph [fontsize={self.options.font_size}];"
        ])
        
        if self.options.title:
            dot_lines.append(f'  label="{self.options.title}";')
        
        # Add function nodes
        functions = {name: symbol for name, symbol in symbol_table.symbols.items() 
                    if symbol.symbol_type in ["function", "method", "async_function"]}
        
        for func_name, func_symbol in functions.items():
            simple_name = func_symbol.name
            if not self.options.include_private and simple_name.startswith('_'):
                continue
                
            # Color-code by type
            color = "lightgreen" if func_symbol.symbol_type == "function" else "lightcyan"
            if func_symbol.symbol_type == "async_function":
                color = "lightyellow"
                
            dot_lines.append(f'  "{simple_name}" [fillcolor={color}, style=filled];')
        
        # Add call relationships
        for caller, callees in symbol_table.call_graph.items():
            caller_simple = caller.split('.')[-1]
            if not self.options.include_private and caller_simple.startswith('_'):
                continue
                
            for callee in callees:
                callee_simple = callee.split('.')[-1]
                if not self.options.include_private and callee_simple.startswith('_'):
                    continue
                    
                dot_lines.append(f'  "{caller_simple}" -> "{callee_simple}";')
        
        dot_lines.append("}")
        return "\n".join(dot_lines)

class MermaidGenerator:
    """Generates Mermaid diagrams for sequence and flowcharts."""
    
    def __init__(self, options: DiagramGenerationOptions):
        self.options = options
        self.console = Console() if Console else None
    
    def generate_architecture_diagram(self, symbol_table: DocumentationSymbolTable) -> str:
        """Generate Mermaid architecture flowchart."""
        mermaid_lines = ["graph TD"]
        
        # Add modules as subgraphs
        for module_name in symbol_table.modules:
            module_id = module_name.replace('.', '_')
            mermaid_lines.append(f"  subgraph {module_id}[{module_name}]")
            
            # Add classes and functions in this module
            module_symbols = [s for s in symbol_table.symbols.values() 
                            if s.module_path == module_name]
            
            for symbol in module_symbols:
                if symbol.symbol_type == "class":
                    mermaid_lines.append(f"    {symbol.name}[{symbol.name}]")
                elif symbol.symbol_type in ["function", "async_function"]:
                    if not symbol.name.startswith('_') or self.options.include_private:
                        mermaid_lines.append(f"    {symbol.name}({symbol.name})")
            
            mermaid_lines.append("  end")
        
        # Add relationships
        for cross_ref in symbol_table.cross_references:
            if cross_ref.relationship_type == "calls":
                source_name = cross_ref.source_symbol.split('.')[-1]
                target_name = cross_ref.target_symbol.split('.')[-1]
                mermaid_lines.append(f"  {source_name} --> {target_name}")
        
        return "\n".join(mermaid_lines)
    
    def generate_sequence_diagram(self, symbol_table: DocumentationSymbolTable, 
                                 focus_function: str) -> str:
        """Generate Mermaid sequence diagram for specific function calls."""
        mermaid_lines = ["sequenceDiagram"]
        
        if self.options.title:
            mermaid_lines.append(f"  title: {self.options.title}")
        
        # Find call chain starting from focus function
        call_chain = self._build_call_chain(symbol_table, focus_function)
        
        participants = set()
        for caller, callee in call_chain:
            participants.add(caller)
            participants.add(callee)
        
        # Add participants
        for participant in sorted(participants):
            mermaid_lines.append(f"  participant {participant}")
        
        # Add sequence
        for caller, callee in call_chain:
            mermaid_lines.append(f"  {caller}->>+{callee}: call")
            mermaid_lines.append(f"  {callee}-->>-{caller}: return")
        
        return "\n".join(mermaid_lines)
    
    def _build_call_chain(self, symbol_table: DocumentationSymbolTable, 
                         start_function: str, max_depth: int = None) -> List[Tuple[str, str]]:
        """Build call chain from a starting function."""
        if max_depth is None:
            max_depth = self.options.max_depth
            
        call_chain = []
        visited = set()
        
        def traverse(func_name, depth):
            if depth >= max_depth or func_name in visited:
                return
                
            visited.add(func_name)
            
            if func_name in symbol_table.call_graph:
                for callee in symbol_table.call_graph[func_name]:
                    call_chain.append((func_name.split('.')[-1], callee.split('.')[-1]))
                    traverse(callee, depth + 1)
        
        traverse(start_function, 0)
        return call_chain

class DiagramGenerationService:
    """Main service for generating and managing diagrams."""
    
    def __init__(self):
        self.console = Console() if Console else None
        self.cross_ref_engine = CrossReferenceEngine()
        self.doc_extractor = AdvancedDocumentationExtractor()
        
        # Check tool availability
        self.available_tools = self._check_tool_availability()
        
    def _check_tool_availability(self) -> Dict[str, bool]:
        """Check availability of external diagram generation tools."""
        tools = {}
        
        # Check PlantUML (requires Java)
        try:
            if sh:
                java_result = sh.java("-version", _ok_code=[0, 1])
                tools['java'] = True
            else:
                subprocess.run(["java", "-version"], capture_output=True, check=True)
                tools['java'] = True
        except (subprocess.CalledProcessError, FileNotFoundError, AttributeError):
            tools['java'] = False
        
        # Check Graphviz
        try:
            if sh:
                sh.dot("-V")
                tools['graphviz'] = True
            else:
                subprocess.run(["dot", "-V"], capture_output=True, check=True)
                tools['graphviz'] = True
        except (subprocess.CalledProcessError, FileNotFoundError, AttributeError):
            tools['graphviz'] = False
        
        # Check Mermaid CLI
        try:
            if sh:
                sh.mmdc("--version")
                tools['mermaid'] = True
            else:
                subprocess.run(["mmdc", "--version"], capture_output=True, check=True)
                tools['mermaid'] = True
        except (subprocess.CalledProcessError, FileNotFoundError, AttributeError):
            tools['mermaid'] = False
        
        return tools
    
    def generate_diagram(self, modules: List[ModuleDocumentation], 
                        options: DiagramGenerationOptions) -> GeneratedDiagram:
        """Generate a diagram based on the specified options."""
        if self.console:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                task = progress.add_task(f"Generating {options.diagram_type.value} diagram...", total=None)
                return self._generate_diagram_internal(modules, options)
        else:
            return self._generate_diagram_internal(modules, options)
    
    def _generate_diagram_internal(self, modules: List[ModuleDocumentation], 
                                  options: DiagramGenerationOptions) -> GeneratedDiagram:
        """Internal diagram generation logic."""
        # Build symbol table
        symbol_table = self.cross_ref_engine.analyze_codebase(modules)
        
        # Generate appropriate diagram source
        if options.diagram_type == DiagramType.INHERITANCE:
            generator = PlantUMLGenerator(options)
            source_code = generator.generate_inheritance_diagram(symbol_table)
            tool_needed = 'java'
        elif options.diagram_type == DiagramType.CLASS_DIAGRAM:
            generator = PlantUMLGenerator(options)
            source_code = generator.generate_class_diagram(modules)
            tool_needed = 'java'
        elif options.diagram_type == DiagramType.IMPORT_DEPENDENCY:
            generator = GraphvizGenerator(options)
            source_code = generator.generate_import_dependency_graph(symbol_table)
            tool_needed = 'graphviz'
        elif options.diagram_type == DiagramType.CALL_GRAPH:
            generator = GraphvizGenerator(options)
            source_code = generator.generate_call_graph(symbol_table)
            tool_needed = 'graphviz'
        elif options.diagram_type == DiagramType.ARCHITECTURE:
            generator = MermaidGenerator(options)
            source_code = generator.generate_architecture_diagram(symbol_table)
            tool_needed = 'mermaid'
        elif options.diagram_type == DiagramType.SEQUENCE:
            generator = MermaidGenerator(options)
            # For sequence diagrams, need to specify focus function
            focus_func = options.custom_styles.get('focus_function', 'main')
            source_code = generator.generate_sequence_diagram(symbol_table, focus_func)
            tool_needed = 'mermaid'
        else:
            raise ValueError(f"Unsupported diagram type: {options.diagram_type}")
        
        # Create diagram object
        diagram = GeneratedDiagram(
            diagram_type=options.diagram_type,
            source_code=source_code,
            output_format=options.output_format,
            generation_timestamp=str(pd.Timestamp.now() if 'pd' in globals() else "unknown"),
            metadata={
                'tool_needed': tool_needed,
                'tool_available': self.available_tools.get(tool_needed, False),
                'symbol_count': len(symbol_table.symbols),
                'cross_reference_count': len(symbol_table.cross_references)
            }
        )
        
        # Generate output file if tool is available and output path specified
        if options.output_path and self.available_tools.get(tool_needed, False):
            try:
                self._render_diagram_to_file(diagram, options)
            except Exception as e:
                logger.warning(f"Failed to render diagram to file: {e}")
                diagram.metadata['render_error'] = str(e)
        
        # Generate ASCII representation for CLI display
        if options.output_format == DiagramFormat.ASCII or not options.output_path:
            diagram.ascii_representation = self._generate_ascii_representation(symbol_table, options)
        
        return diagram
    
    def _render_diagram_to_file(self, diagram: GeneratedDiagram, 
                               options: DiagramGenerationOptions) -> None:
        """Render diagram source to output file using external tools."""
        tool_needed = diagram.metadata['tool_needed']
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as source_file:
            source_file.write(diagram.source_code)
            source_path = source_file.name
        
        try:
            if tool_needed == 'java':  # PlantUML
                self._render_plantuml(source_path, options.output_path, options.output_format)
            elif tool_needed == 'graphviz':
                self._render_graphviz(source_path, options.output_path, options.output_format, options.layout_engine)
            elif tool_needed == 'mermaid':
                self._render_mermaid(source_path, options.output_path, options.output_format)
            
            diagram.file_path = options.output_path
            
        finally:
            os.unlink(source_path)
    
    def _render_plantuml(self, source_path: str, output_path: str, 
                        output_format: DiagramFormat) -> None:
        """Render PlantUML diagram using Java."""
        plantuml_jar = self._find_plantuml_jar()
        if not plantuml_jar:
            raise RuntimeError("PlantUML JAR not found")
        
        format_flag = f"-t{output_format.value}"
        if sh:
            sh.java("-jar", plantuml_jar, format_flag, f"-o{os.path.dirname(output_path)}", source_path)
        else:
            subprocess.run([
                "java", "-jar", plantuml_jar, format_flag, 
                f"-o{os.path.dirname(output_path)}", source_path
            ], check=True)
    
    def _render_graphviz(self, source_path: str, output_path: str, 
                        output_format: DiagramFormat, layout_engine: str) -> None:
        """Render Graphviz diagram."""
        output_arg = f"-T{output_format.value}"
        output_file_arg = f"-o{output_path}"
        
        if sh:
            getattr(sh, layout_engine)(output_arg, output_file_arg, source_path)
        else:
            subprocess.run([layout_engine, output_arg, output_file_arg, source_path], check=True)
    
    def _render_mermaid(self, source_path: str, output_path: str, 
                       output_format: DiagramFormat) -> None:
        """Render Mermaid diagram using mermaid CLI."""
        format_flag = f"--outputFormat={output_format.value}"
        
        if sh:
            sh.mmdc("-i", source_path, "-o", output_path, format_flag)
        else:
            subprocess.run(["mmdc", "-i", source_path, "-o", output_path, format_flag], check=True)
    
    def _find_plantuml_jar(self) -> Optional[str]:
        """Find PlantUML JAR file in common locations."""
        common_paths = [
            "/usr/share/plantuml/plantuml.jar",
            "/usr/local/share/plantuml/plantuml.jar",
            "~/plantuml.jar",
            "./plantuml.jar"
        ]
        
        for path in common_paths:
            expanded_path = os.path.expanduser(path)
            if os.path.exists(expanded_path):
                return expanded_path
        
        return None
    
    def _generate_ascii_representation(self, symbol_table: DocumentationSymbolTable, 
                                     options: DiagramGenerationOptions) -> str:
        """Generate ASCII representation for CLI display using rich."""
        if not self.console:
            return "ASCII representation requires rich library"
        
        if options.diagram_type == DiagramType.INHERITANCE:
            return self._ascii_inheritance_tree(symbol_table)
        elif options.diagram_type in [DiagramType.IMPORT_DEPENDENCY, DiagramType.CALL_GRAPH]:
            return self._ascii_dependency_list(symbol_table, options.diagram_type)
        else:
            return self._ascii_symbol_summary(symbol_table)
    
    def _ascii_inheritance_tree(self, symbol_table: DocumentationSymbolTable) -> str:
        """Generate ASCII inheritance tree using rich Tree."""
        tree = Tree("Inheritance Hierarchy")
        
        # Build inheritance tree
        root_classes = []
        child_classes = {}
        
        for class_name, inheritance_chain in symbol_table.inheritance_chains.items():
            if not inheritance_chain.base_classes:
                root_classes.append(class_name)
            else:
                for base_class in inheritance_chain.base_classes:
                    if base_class not in child_classes:
                        child_classes[base_class] = []
                    child_classes[base_class].append(class_name)
        
        def add_class_to_tree(parent_node, class_name):
            simple_name = class_name.split('.')[-1]
            class_node = parent_node.add(simple_name)
            
            if class_name in child_classes:
                for child in child_classes[class_name]:
                    add_class_to_tree(class_node, child)
        
        for root_class in root_classes:
            add_class_to_tree(tree, root_class)
        
        # Capture tree output
        console = Console(file=StringIO(), width=80)
        console.print(tree)
        return console.file.getvalue()
    
    def _ascii_dependency_list(self, symbol_table: DocumentationSymbolTable, 
                             diagram_type: DiagramType) -> str:
        """Generate ASCII dependency list."""
        console = Console(file=StringIO(), width=80)
        
        if diagram_type == DiagramType.IMPORT_DEPENDENCY:
            table = Table(title="Import Dependencies")
            table.add_column("Module", style="cyan")
            table.add_column("Imports", style="green")
            
            # Group imports by module
            module_imports = {}
            for cross_ref in symbol_table.cross_references:
                if cross_ref.relationship_type == "imports":
                    source_module = cross_ref.source_symbol.split('.')[0]
                    target_module = cross_ref.target_symbol.split('.')[0]
                    
                    if source_module not in module_imports:
                        module_imports[source_module] = set()
                    module_imports[source_module].add(target_module)
            
            for module, imports in sorted(module_imports.items()):
                table.add_row(module, ", ".join(sorted(imports)))
            
        else:  # CALL_GRAPH
            table = Table(title="Function Call Graph")
            table.add_column("Function", style="cyan")
            table.add_column("Calls", style="green")
            
            for caller, callees in sorted(symbol_table.call_graph.items()):
                caller_simple = caller.split('.')[-1]
                callees_simple = [c.split('.')[-1] for c in callees]
                table.add_row(caller_simple, ", ".join(sorted(callees_simple)))
        
        console.print(table)
        return console.file.getvalue()
    
    def _ascii_symbol_summary(self, symbol_table: DocumentationSymbolTable) -> str:
        """Generate ASCII summary of symbols."""
        console = Console(file=StringIO(), width=80)
        
        # Count symbols by type
        symbol_counts = {}
        for symbol in symbol_table.symbols.values():
            symbol_type = symbol.symbol_type
            symbol_counts[symbol_type] = symbol_counts.get(symbol_type, 0) + 1
        
        table = Table(title="Symbol Summary")
        table.add_column("Type", style="cyan")
        table.add_column("Count", style="green")
        
        for symbol_type, count in sorted(symbol_counts.items()):
            table.add_row(symbol_type, str(count))
        
        console.print(table)
        return console.file.getvalue()
    
    def display_diagram_in_cli(self, diagram: GeneratedDiagram) -> None:
        """Display diagram in CLI using rich."""
        if not self.console:
            print("CLI display requires rich library")
            return
        
        # Display diagram info
        panel = Panel(
            f"Diagram Type: {diagram.diagram_type.value}\n"
            f"Format: {diagram.output_format.value}\n"
            f"Generated: {diagram.generation_timestamp}\n"
            f"Tool Available: {diagram.metadata.get('tool_available', 'Unknown')}",
            title="Diagram Information",
            style="blue"
        )
        self.console.print(panel)
        
        # Display ASCII representation
        if diagram.ascii_representation:
            self.console.print("\n[bold]ASCII Representation:[/bold]")
            self.console.print(diagram.ascii_representation)
        
        # Display source code
        if len(diagram.source_code) < 2000:  # Only show if not too long
            self.console.print(f"\n[bold]{diagram.diagram_type.value.title()} Source:[/bold]")
            self.console.print(Panel(diagram.source_code, style="green"))
    
    def get_available_tools_status(self) -> Dict[str, Any]:
        """Get status of available diagram generation tools."""
        return {
            'tools': self.available_tools,
            'recommendations': self._get_tool_recommendations(),
            'installation_instructions': self._get_installation_instructions()
        }
    
    def _get_tool_recommendations(self) -> Dict[str, str]:
        """Get tool recommendations based on availability."""
        recommendations = {}
        
        if not self.available_tools.get('java', False):
            recommendations['plantuml'] = "Install Java to enable PlantUML diagrams (inheritance, class diagrams)"
        
        if not self.available_tools.get('graphviz', False):
            recommendations['graphviz'] = "Install Graphviz to enable dependency and call graph diagrams"
        
        if not self.available_tools.get('mermaid', False):
            recommendations['mermaid'] = "Install Mermaid CLI to enable architecture and sequence diagrams"
        
        return recommendations
    
    def _get_installation_instructions(self) -> Dict[str, str]:
        """Get installation instructions for missing tools."""
        instructions = {}
        
        if not self.available_tools.get('java', False):
            instructions['java'] = "sudo apt-get install default-jre (Ubuntu/Debian) or brew install openjdk (macOS)"
        
        if not self.available_tools.get('graphviz', False):
            instructions['graphviz'] = "sudo apt-get install graphviz (Ubuntu/Debian) or brew install graphviz (macOS)"
        
        if not self.available_tools.get('mermaid', False):
            instructions['mermaid'] = "npm install -g @mermaid-js/mermaid-cli"
        
        return instructions

# StringIO import for ASCII generation
from io import StringIO

if __name__ == "__main__":
    # Example usage and testing
    service = DiagramGenerationService()
    
    # Show tool availability
    status = service.get_available_tools_status()
    print("Tool Availability:")
    for tool, available in status['tools'].items():
        print(f"  {tool}: {'✅' if available else '❌'}")
    
    if status['recommendations']:
        print("\nRecommendations:")
        for tool, rec in status['recommendations'].items():
            print(f"  {rec}")