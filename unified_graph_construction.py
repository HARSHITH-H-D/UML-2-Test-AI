"""
STAGE 2: UNIFIED GRAPH CONSTRUCTION
Convert UML diagrams into a single unified directed graph

This module implements the unified graph construction algorithm that:
1. Extracts all UML elements (classes, use cases, activities, actors)
2. Creates nodes for each element
3. Establishes edges based on relationships (include, extend, dependency, control flow)
4. Produces a unified behavioral graph G = (V, E)

Time Complexity: O(V + E)
Space Complexity: O(V + E)
"""

import networkx as nx
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Set, Optional
from dataclasses import dataclass, field
from enum import Enum
import json


# ============================================================================
# PART 1: DATA STRUCTURES
# ============================================================================

class NodeType(Enum):
    """Types of nodes in the unified graph"""
    ACTOR = "actor"
    USECASE = "usecase"
    CLASS = "class"
    ACTIVITY = "activity"
    INTERFACE = "interface"
    COMPONENT = "component"


class EdgeType(Enum):
    """Types of relationships/edges in the unified graph"""
    INCLUDE = "include"          # Use case includes another
    EXTEND = "extend"            # Use case extends another
    DEPENDENCY = "dependency"     # General dependency
    CONTROL_FLOW = "control_flow" # Sequential flow
    ASSOCIATION = "association"   # General association
    GENERALIZATION = "generalization"  # Inheritance
    REALIZATION = "realization"   # Interface implementation
    INVOKES = "invokes"          # Actor invokes use case
    USES = "uses"                # Use case uses class/system


@dataclass
class UMLNode:
    """Represents a node in the unified graph"""
    id: str
    name: str
    node_type: NodeType
    attributes: Dict[str, any] = field(default_factory=dict)
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        return self.id == other.id if isinstance(other, UMLNode) else False


@dataclass
class UMLEdge:
    """Represents an edge in the unified graph"""
    source: str
    target: str
    edge_type: EdgeType
    attributes: Dict[str, any] = field(default_factory=dict)


@dataclass
class UMLElements:
    """Container for parsed UML elements"""
    actors: List[Tuple[str, str]] = field(default_factory=list)
    usecases: List[Tuple[str, str]] = field(default_factory=list)
    classes: List[Tuple[str, str]] = field(default_factory=list)
    activities: List[Tuple[str, str]] = field(default_factory=list)
    relations: List[Tuple[str, str]] = field(default_factory=list)
    
    # Extended relationships with types
    includes: List[Tuple[str, str]] = field(default_factory=list)
    extends: List[Tuple[str, str]] = field(default_factory=list)
    dependencies: List[Tuple[str, str]] = field(default_factory=list)
    control_flows: List[Tuple[str, str]] = field(default_factory=list)
    associations: List[Tuple[str, str]] = field(default_factory=list)


# ============================================================================
# PART 2: UNIFIED GRAPH BUILDER
# ============================================================================

class UnifiedGraphBuilder:
    """
    Builds a unified behavioral graph from UML elements
    
    Algorithm: Unified Graph Construction
    Input: Parsed UML elements
    Output: Unified Behavioral Graph G
    
    1. Initialize directed graph G
    2. For each class: add node in G
    3. For each usecase: add node in G
    4. For each activity: add node in G
    5. For each relationship:
          include → add edge
          extend → add edge
          dependency → add edge
          control flow → add edge
    6. Return graph G
    
    Complexity: O(V + E) where V = nodes, E = edges
    """
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.nodes: Dict[str, UMLNode] = {}
        self.edges: List[UMLEdge] = []
        self.node_counter = 0
        
    def build_unified_graph(self, uml_elements: UMLElements) -> nx.DiGraph:
        """
        Main algorithm to build unified graph
        
        Args:
            uml_elements: Parsed UML elements
            
        Returns:
            Unified directed graph G = (V, E)
        """
        # Step 1: Initialize directed graph G
        self.graph = nx.DiGraph()
        self.nodes.clear()
        self.edges.clear()
        
        print("Building Unified Graph...")
        print("-" * 60)
        
        # Step 2: Add class nodes
        print(f"Step 2: Adding {len(uml_elements.classes)} class nodes...")
        for class_id, class_name in uml_elements.classes:
            self._add_node(class_id, class_name, NodeType.CLASS)
        
        # Step 3: Add use case nodes
        print(f"Step 3: Adding {len(uml_elements.usecases)} use case nodes...")
        for uc_id, uc_name in uml_elements.usecases:
            self._add_node(uc_id, uc_name, NodeType.USECASE)
        
        # Step 4: Add activity nodes
        print(f"Step 4: Adding {len(uml_elements.activities)} activity nodes...")
        for act_id, act_name in uml_elements.activities:
            self._add_node(act_id, act_name, NodeType.ACTIVITY)
        
        # Also add actors
        print(f"Step 4b: Adding {len(uml_elements.actors)} actor nodes...")
        for actor_id, actor_name in uml_elements.actors:
            self._add_node(actor_id, actor_name, NodeType.ACTOR)
        
        # Step 5: Add relationships
        print(f"Step 5: Adding relationships...")
        
        # Include relationships
        print(f"  - {len(uml_elements.includes)} include edges")
        for src, tgt in uml_elements.includes:
            self._add_edge(src, tgt, EdgeType.INCLUDE)
        
        # Extend relationships
        print(f"  - {len(uml_elements.extends)} extend edges")
        for src, tgt in uml_elements.extends:
            self._add_edge(src, tgt, EdgeType.EXTEND)
        
        # Dependency relationships
        print(f"  - {len(uml_elements.dependencies)} dependency edges")
        for src, tgt in uml_elements.dependencies:
            self._add_edge(src, tgt, EdgeType.DEPENDENCY)
        
        # Control flow relationships
        print(f"  - {len(uml_elements.control_flows)} control flow edges")
        for src, tgt in uml_elements.control_flows:
            self._add_edge(src, tgt, EdgeType.CONTROL_FLOW)
        
        # General associations
        print(f"  - {len(uml_elements.associations)} association edges")
        for src, tgt in uml_elements.associations:
            self._add_edge(src, tgt, EdgeType.ASSOCIATION)
        
        # Generic relations (when type is unknown)
        print(f"  - {len(uml_elements.relations)} generic relations")
        for src, tgt in uml_elements.relations:
            if src in self.nodes and tgt in self.nodes:
                # Infer edge type based on node types
                edge_type = self._infer_edge_type(
                    self.nodes[src].node_type,
                    self.nodes[tgt].node_type
                )
                self._add_edge(src, tgt, edge_type)
        
        # Step 6: Return unified graph
        print("-" * 60)
        print(f"Unified graph constructed:")
        print(f"  Total nodes (V): {self.graph.number_of_nodes()}")
        print(f"  Total edges (E): {self.graph.number_of_edges()}")
        print(f"  Complexity: O({self.graph.number_of_nodes()} + {self.graph.number_of_edges()})")
        
        return self.graph
    
    def _add_node(self, node_id: str, name: str, node_type: NodeType):
        """Add a node to the unified graph"""
        if node_id not in self.nodes:
            node = UMLNode(
                id=node_id,
                name=name,
                node_type=node_type,
                attributes={'label': name, 'type': node_type.value}
            )
            self.nodes[node_id] = node
            self.graph.add_node(
                node_id,
                name=name,
                node_type=node_type.value,
                label=name
            )
    
    def _add_edge(self, source: str, target: str, edge_type: EdgeType):
        """Add an edge to the unified graph"""
        if source in self.nodes and target in self.nodes:
            edge = UMLEdge(
                source=source,
                target=target,
                edge_type=edge_type,
                attributes={'type': edge_type.value}
            )
            self.edges.append(edge)
            self.graph.add_edge(
                source,
                target,
                edge_type=edge_type.value,
                label=edge_type.value
            )
    
    def _infer_edge_type(self, src_type: NodeType, tgt_type: NodeType) -> EdgeType:
        """Infer edge type based on source and target node types"""
        if src_type == NodeType.ACTOR and tgt_type == NodeType.USECASE:
            return EdgeType.INVOKES
        elif src_type == NodeType.USECASE and tgt_type == NodeType.CLASS:
            return EdgeType.USES
        elif src_type == NodeType.USECASE and tgt_type == NodeType.USECASE:
            return EdgeType.INCLUDE  # Default for usecase->usecase
        elif src_type == NodeType.ACTIVITY and tgt_type == NodeType.ACTIVITY:
            return EdgeType.CONTROL_FLOW
        else:
            return EdgeType.ASSOCIATION
    
    def get_graph_statistics(self) -> Dict:
        """Get statistics about the unified graph"""
        stats = {
            'total_nodes': self.graph.number_of_nodes(),
            'total_edges': self.graph.number_of_edges(),
            'node_types': {},
            'edge_types': {},
            'density': nx.density(self.graph),
            'is_dag': nx.is_directed_acyclic_graph(self.graph),
            'strongly_connected_components': nx.number_strongly_connected_components(self.graph),
            'weakly_connected_components': nx.number_weakly_connected_components(self.graph)
        }
        
        # Count nodes by type
        for node_id, data in self.graph.nodes(data=True):
            node_type = data.get('node_type', 'unknown')
            stats['node_types'][node_type] = stats['node_types'].get(node_type, 0) + 1
        
        # Count edges by type
        for src, tgt, data in self.graph.edges(data=True):
            edge_type = data.get('edge_type', 'unknown')
            stats['edge_types'][edge_type] = stats['edge_types'].get(edge_type, 0) + 1
        
        return stats
    
    def export_to_adjacency_list(self, filepath: str):
        """Export graph as adjacency list"""
        with open(filepath, 'w') as f:
            for node in self.graph.nodes():
                neighbors = list(self.graph.neighbors(node))
                f.write(f"{node}: {', '.join(neighbors)}\n")
    
    def export_to_json(self, filepath: str):
        """Export graph to JSON format"""
        graph_data = {
            'nodes': [
                {
                    'id': node_id,
                    'name': self.nodes[node_id].name,
                    'type': self.nodes[node_id].node_type.value,
                    'attributes': self.nodes[node_id].attributes
                }
                for node_id in self.nodes
            ],
            'edges': [
                {
                    'source': edge.source,
                    'target': edge.target,
                    'type': edge.edge_type.value,
                    'attributes': edge.attributes
                }
                for edge in self.edges
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(graph_data, f, indent=2)
    
    def visualize(self, output_path: Optional[str] = None, figsize=(12, 8)):
        """Visualize the unified graph"""
        plt.figure(figsize=figsize)
        
        # Create layout
        pos = nx.spring_layout(self.graph, k=2, iterations=50)
        
        # Color nodes by type
        node_colors = []
        color_map = {
            'actor': '#FF6B6B',
            'usecase': '#4ECDC4',
            'class': '#45B7D1',
            'activity': '#FFA07A'
        }
        
        for node in self.graph.nodes():
            node_type = self.graph.nodes[node].get('node_type', 'unknown')
            node_colors.append(color_map.get(node_type, '#95A5A6'))
        
        # Draw nodes
        nx.draw_networkx_nodes(
            self.graph, pos,
            node_color=node_colors,
            node_size=800,
            alpha=0.9
        )
        
        # Draw edges with different styles
        edge_colors = []
        edge_styles = []
        
        for src, tgt in self.graph.edges():
            edge_type = self.graph[src][tgt].get('edge_type', 'unknown')
            
            if edge_type == 'include':
                edge_colors.append('#2ECC71')
                edge_styles.append('solid')
            elif edge_type == 'extend':
                edge_colors.append('#E74C3C')
                edge_styles.append('dashed')
            elif edge_type == 'control_flow':
                edge_colors.append('#3498DB')
                edge_styles.append('solid')
            else:
                edge_colors.append('#95A5A6')
                edge_styles.append('dotted')
        
        nx.draw_networkx_edges(
            self.graph, pos,
            edge_color=edge_colors,
            width=2,
            alpha=0.6,
            arrows=True,
            arrowsize=20,
            arrowstyle='->'
        )
        
        # Draw labels
        labels = {node: self.graph.nodes[node].get('name', node) for node in self.graph.nodes()}
        nx.draw_networkx_labels(
            self.graph, pos,
            labels,
            font_size=8,
            font_weight='bold'
        )
        
        # Create legend
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w', 
                      markerfacecolor='#FF6B6B', markersize=10, label='Actor'),
            plt.Line2D([0], [0], marker='o', color='w', 
                      markerfacecolor='#4ECDC4', markersize=10, label='UseCase'),
            plt.Line2D([0], [0], marker='o', color='w', 
                      markerfacecolor='#45B7D1', markersize=10, label='Class'),
            plt.Line2D([0], [0], marker='o', color='w', 
                      markerfacecolor='#FFA07A', markersize=10, label='Activity'),
            plt.Line2D([0], [0], color='#2ECC71', linewidth=2, label='Include'),
            plt.Line2D([0], [0], color='#E74C3C', linewidth=2, 
                      linestyle='--', label='Extend'),
            plt.Line2D([0], [0], color='#3498DB', linewidth=2, label='Control Flow'),
        ]
        plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1, 1))
        
        plt.title("Unified Behavioral Graph G = (V, E)", fontsize=14, fontweight='bold')
        plt.axis('off')
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"Graph visualization saved to: {output_path}")
        
        plt.show()


# ============================================================================
# PART 3: PARSER ADAPTER (Converts your parsed UML to UMLElements)
# ============================================================================

class UMLParserAdapter:
    """Adapts parsed UML from your existing parser to UMLElements format"""
    
    @staticmethod
    def from_corrected_model(corrected_model: Dict) -> UMLElements:
        """
        Convert from your parser format to UMLElements
        
        Args:
            corrected_model: Output from parse_and_correct_plantuml
            
        Returns:
            UMLElements object
        """
        elements = UMLElements()
        
        # Extract actors
        elements.actors = corrected_model.get('actors', [])
        
        # Extract use cases
        elements.usecases = corrected_model.get('usecases', [])
        
        # Extract classes
        elements.classes = corrected_model.get('classes', [])
        
        # Extract activities (if present)
        elements.activities = corrected_model.get('activities', [])
        
        # Extract relations
        relations = corrected_model.get('relations', [])
        elements.relations = relations
        
        # Classify relations by type (if metadata available)
        # This requires enhanced parsing to detect relationship types
        elements = UMLParserAdapter._classify_relations(
            elements, 
            corrected_model
        )
        
        return elements
    
    @staticmethod
    def _classify_relations(elements: UMLElements, model: Dict) -> UMLElements:
        """Classify generic relations into specific types"""
        # This is a heuristic approach
        # Ideally, the parser should detect these from PlantUML keywords
        
        node_types = {}
        
        # Build node type map
        for node_id, name in elements.actors:
            node_types[node_id] = NodeType.ACTOR
        for node_id, name in elements.usecases:
            node_types[node_id] = NodeType.USECASE
        for node_id, name in elements.classes:
            node_types[node_id] = NodeType.CLASS
        for node_id, name in elements.activities:
            node_types[node_id] = NodeType.ACTIVITY
        
        # Classify relations based on node types and naming
        for src, tgt in elements.relations:
            src_type = node_types.get(src)
            tgt_type = node_types.get(tgt)
            
            if src_type == NodeType.USECASE and tgt_type == NodeType.USECASE:
                # Check if it's include or extend based on naming
                src_name = next((n for i, n in elements.usecases if i == src), "")
                tgt_name = next((n for i, n in elements.usecases if i == tgt), "")
                
                if 'extend' in tgt_name.lower() or 'optional' in tgt_name.lower():
                    elements.extends.append((src, tgt))
                else:
                    elements.includes.append((src, tgt))
            
            elif src_type == NodeType.ACTIVITY and tgt_type == NodeType.ACTIVITY:
                elements.control_flows.append((src, tgt))
            
            elif src_type == NodeType.ACTOR and tgt_type == NodeType.USECASE:
                elements.associations.append((src, tgt))
            
            elif src_type == NodeType.USECASE and tgt_type == NodeType.CLASS:
                elements.dependencies.append((src, tgt))
            
            else:
                elements.associations.append((src, tgt))
        
        return elements


# ============================================================================
# PART 4: EXAMPLE USAGE
# ============================================================================

def example_usage():
    """Demonstrate unified graph construction"""
    
    print("="*60)
    print("STAGE 2: UNIFIED GRAPH CONSTRUCTION")
    print("="*60)
    print()
    
    # Create sample UML elements
    uml_elements = UMLElements(
        actors=[
            ('A1', 'User'),
            ('A2', 'Admin')
        ],
        usecases=[
            ('UC1', 'Login'),
            ('UC2', 'ValidateCredentials'),
            ('UC3', 'CheckPermissions'),
            ('UC4', 'AccessSystem'),
            ('UC5', 'ManageUsers')
        ],
        classes=[
            ('C1', 'AuthService'),
            ('C2', 'UserDatabase'),
            ('C3', 'PermissionManager')
        ],
        activities=[
            ('ACT1', 'EnterCredentials'),
            ('ACT2', 'SubmitForm'),
            ('ACT3', 'ProcessRequest')
        ]
    )
    
    # Define relationships
    uml_elements.includes = [
        ('UC1', 'UC2'),  # Login includes ValidateCredentials
        ('UC4', 'UC3'),  # AccessSystem includes CheckPermissions
    ]
    
    uml_elements.extends = [
        ('UC1', 'UC5'),  # Login extends to ManageUsers (for admin)
    ]
    
    uml_elements.dependencies = [
        ('UC2', 'C1'),  # ValidateCredentials depends on AuthService
        ('UC2', 'C2'),  # ValidateCredentials depends on UserDatabase
        ('UC3', 'C3'),  # CheckPermissions depends on PermissionManager
    ]
    
    uml_elements.control_flows = [
        ('ACT1', 'ACT2'),  # EnterCredentials → SubmitForm
        ('ACT2', 'ACT3'),  # SubmitForm → ProcessRequest
    ]
    
    uml_elements.associations = [
        ('A1', 'UC1'),  # User invokes Login
        ('A2', 'UC5'),  # Admin invokes ManageUsers
        ('UC1', 'UC4'),  # Login leads to AccessSystem
    ]
    
    # Build unified graph
    builder = UnifiedGraphBuilder()
    graph = builder.build_unified_graph(uml_elements)
    
    print()
    
    # Display statistics
    stats = builder.get_graph_statistics()
    print("\nGraph Statistics:")
    print("=" * 60)
    print(f"Total Nodes (V): {stats['total_nodes']}")
    print(f"Total Edges (E): {stats['total_edges']}")
    print(f"Graph Density: {stats['density']:.4f}")
    print(f"Is DAG: {stats['is_dag']}")
    print(f"Strongly Connected Components: {stats['strongly_connected_components']}")
    print(f"Weakly Connected Components: {stats['weakly_connected_components']}")
    print()
    print("Node Distribution:")
    for node_type, count in stats['node_types'].items():
        print(f"  {node_type}: {count}")
    print()
    print("Edge Distribution:")
    for edge_type, count in stats['edge_types'].items():
        print(f"  {edge_type}: {count}")
    
    # Export graph
    print("\nExporting graph...")
    builder.export_to_adjacency_list('unified_graph_adjacency.txt')
    builder.export_to_json('unified_graph.json')
    print("  - Adjacency list: unified_graph_adjacency.txt")
    print("  - JSON format: unified_graph.json")
    
    # Visualize
    print("\nGenerating visualization...")
    builder.visualize(output_path='unified_graph.png')
    
    return graph, builder


if __name__ == "__main__":
    graph, builder = example_usage()
