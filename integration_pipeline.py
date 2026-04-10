"""
INTEGRATION: UML Parser + Unified Graph Construction + GNN

This script integrates:
1. Your original UML parser (from uml_to_testcase.ipynb)
2. Unified Graph Construction (Stage 2)
3. GNN Pattern Recognition

Complete pipeline: PlantUML → Unified Graph → GNN Training
"""

import os
import re
from collections import Counter
import networkx as nx
import torch
from torch_geometric.data import Data
from typing import List, Dict, Tuple

# Import unified graph construction
from unified_graph_construction import (
    UnifiedGraphBuilder,
    UMLElements,
    UMLParserAdapter,
    NodeType,
    EdgeType
)


# ============================================================================
# PART 1: YOUR ORIGINAL PARSER (Enhanced)
# ============================================================================

def parse_plantuml_raw(puml_path):
    """Parse PlantUML file and extract nodes and edges"""
    nodes = {}
    edges = []

    actor_pat   = re.compile(r'actor\s+"?(.+?)"?(\s+as\s+(\w+))?', re.I)
    usecase_pat = re.compile(r'usecase\s+"?(.+?)"?(\s+as\s+(\w+))?', re.I)
    class_pat   = re.compile(r'class\s+"?(.+?)"?(\s+as\s+(\w+))?', re.I)
    activity_pat = re.compile(r'activity\s+"?(.+?)"?(\s+as\s+(\w+))?', re.I)
    
    # Enhanced edge patterns to detect relationship types
    include_pat = re.compile(r'(.+?)\s*\.\.\s*>\s*(.+?)\s*:\s*<<include>>', re.I)
    extend_pat = re.compile(r'(.+?)\s*\.\.\s*>\s*(.+?)\s*:\s*<<extend>>', re.I)
    edge_pat = re.compile(r'(.+?)\s*[-.]+[<>]*\s*(.+)')

    with open(puml_path, "r") as f:
        for line in f:
            line = line.strip()

            if not line or line.startswith("@") or line.startswith("'"):
                continue

            # Check for include relationship
            m = include_pat.match(line)
            if m:
                src = m.group(1).strip().strip('"')
                tgt = m.group(2).strip().strip('"')
                edges.append((src, tgt, 'include'))
                nodes.setdefault(src, "usecase")
                nodes.setdefault(tgt, "usecase")
                continue
            
            # Check for extend relationship
            m = extend_pat.match(line)
            if m:
                src = m.group(1).strip().strip('"')
                tgt = m.group(2).strip().strip('"')
                edges.append((src, tgt, 'extend'))
                nodes.setdefault(src, "usecase")
                nodes.setdefault(tgt, "usecase")
                continue

            # Check for actor
            m = actor_pat.match(line)
            if m:
                nodes[m.group(3) or m.group(1)] = "actor"
                continue

            # Check for usecase
            m = usecase_pat.match(line)
            if m:
                nodes[m.group(3) or m.group(1)] = "usecase"
                continue

            # Check for class
            m = class_pat.match(line)
            if m:
                nodes[m.group(3) or m.group(1)] = "class"
                continue
            
            # Check for activity
            m = activity_pat.match(line)
            if m:
                nodes[m.group(3) or m.group(1)] = "activity"
                continue

            # Generic edge
            m = edge_pat.match(line)
            if m:
                src = m.group(1).strip().strip('"')
                tgt = m.group(2).strip().strip('"')
                edges.append((src, tgt, 'generic'))
                nodes.setdefault(src, "usecase")
                nodes.setdefault(tgt, "usecase")

    return nodes, edges


def split_camelcase(text):
    """
    Split CamelCase or PascalCase into separate words.
    
    Examples:
        "AuditBudgets" → ["Audit", "Budgets"]
        "CheckTransactions" → ["Check", "Transactions"]
    """
    # Insert space before uppercase letters (except at start)
    spaced = re.sub(r'(?<!^)(?=[A-Z])', ' ', text)
    return spaced.split()


def extract_action(name):
    """
    Extract the primary action verb from a use case name.
    
    Handles multiple formats:
    - CamelCase: "AuditBudgets" → "audit"
    - snake_case: "audit_budgets" → "audit"
    - Space-separated: "Audit Budgets" → "audit"
    
    Args:
        name: Use case name in any format
        
    Returns:
        action: Primary action verb (lowercase) or None
    """
    # Step 1: Handle CamelCase
    words = split_camelcase(name)
    
    # Step 2: Handle other separators (underscores, hyphens)
    text = ' '.join(words)
    text = re.sub(r'[_\-]', ' ', text)
    
    # Step 3: Extract alphabetic tokens
    tokens = re.findall(r"[a-zA-Z]+", text)
    
    if not tokens:
        return None
    
    # Step 4: Get first token (the action)
    action = tokens[0].lower()
    
    # Step 5: Filter out non-action words
    if len(action) < 3:  # Allow 3+ letter actions like "add", "get"
        return None
    if action.endswith(("service", "system", "manager")):
        return None
    if action in ("user", "customer", "patient", "admin", "manager", "team", "actor"):
        return None
    
    return action


def build_action_order(all_usecase_names):
    """Build frequency-based action ordering"""
    freq = Counter()
    for name in all_usecase_names:
        action = extract_action(name)
        if action:
            freq[action] += 1
    return [a for a, _ in freq.most_common()]


def rank(name, action_order):
    """Rank action by frequency"""
    name = name.lower()
    for i, action in enumerate(action_order):
        if action in name:
            return i
    return len(action_order)


def correct_edges(nodes, edges, action_order):
    """Correct edge directions based on node types and action ordering"""
    corrected = []

    for edge_info in edges:
        if len(edge_info) == 3:
            src, tgt, edge_type = edge_info
        else:
            src, tgt = edge_info
            edge_type = 'generic'
        
        s, t = nodes.get(src), nodes.get(tgt)

        # Keep explicit edge types
        if edge_type in ['include', 'extend']:
            corrected.append((src, tgt, edge_type))
            continue

        if s == "actor" and t == "usecase":
            corrected.append((src, tgt, 'invokes'))

        elif s == "usecase" and t == "actor":
            corrected.append((tgt, src, 'invokes'))

        elif s == "usecase" and t == "usecase":
            if rank(src, action_order) <= rank(tgt, action_order):
                corrected.append((src, tgt, 'control_flow'))
            else:
                corrected.append((tgt, src, 'control_flow'))

        elif s == "usecase" and t == "class":
            corrected.append((src, tgt, 'dependency'))

        elif s == "class" and t == "usecase":
            corrected.append((tgt, src, 'dependency'))
        
        elif s == "activity" and t == "activity":
            corrected.append((src, tgt, 'control_flow'))
        
        else:
            corrected.append((src, tgt, 'association'))

    return corrected


def parse_and_correct_plantuml(puml_path, action_order):
    """Parse and correct a single PlantUML file"""
    nodes, raw_edges = parse_plantuml_raw(puml_path)
    edges = correct_edges(nodes, raw_edges, action_order)

    uml = {
        "actors": [],
        "usecases": [],
        "classes": [],
        "activities": [],
        "relations": [],
        "includes": [],
        "extends": [],
        "dependencies": [],
        "control_flows": [],
        "associations": []
    }

    type_map = {
        "actor": "actors",
        "usecase": "usecases",
        "class": "classes",
        "activity": "activities"
    }

    id_map = {}
    counter = 0

    def get_id(name):
        nonlocal counter
        if name not in id_map:
            id_map[name] = f"N{counter}"
            counter += 1
        return id_map[name]

    # Add nodes
    for name, t in nodes.items():
        if t in type_map:
            uml[type_map[t]].append((get_id(name), name))

    # Add edges by type
    for src, tgt, edge_type in edges:
        src_id = get_id(src)
        tgt_id = get_id(tgt)
        
        if edge_type == 'include':
            uml["includes"].append((src_id, tgt_id))
        elif edge_type == 'extend':
            uml["extends"].append((src_id, tgt_id))
        elif edge_type == 'dependency':
            uml["dependencies"].append((src_id, tgt_id))
        elif edge_type == 'control_flow':
            uml["control_flows"].append((src_id, tgt_id))
        elif edge_type == 'association' or edge_type == 'invokes':
            uml["associations"].append((src_id, tgt_id))
        else:
            uml["relations"].append((src_id, tgt_id))

    return uml


# ============================================================================
# PART 2: INTEGRATION WITH UNIFIED GRAPH
# ============================================================================

class UMLToUnifiedGraph:
    """
    Complete pipeline: PlantUML → Parsed UML → Unified Graph
    """
    
    def __init__(self):
        self.action_order = []
        self.parsed_models = []
        self.unified_graphs = []
        
    def process_dataset(self, dataset_path: str) -> List[nx.DiGraph]:
        """
        Process entire UML dataset and build unified graphs
        
        Args:
            dataset_path: Path to directory containing .puml files
            
        Returns:
            List of unified graphs
        """
        print("="*70)
        print("COMPLETE PIPELINE: PLANTUML → UNIFIED GRAPH")
        print("="*70)
        
        # Step 1: Collect use cases for action ordering
        print("\n[Step 1] Collecting use cases...")
        all_usecases = []
        
        for root, _, files in os.walk(dataset_path):
            for file in files:
                if file.endswith(".puml"):
                    nodes, _ = parse_plantuml_raw(os.path.join(root, file))
                    for name, t in nodes.items():
                        if t == "usecase":
                            all_usecases.append(name)
        
        print(f"Found {len(all_usecases)} use cases")
        
        # Step 2: Build action order
        print("\n[Step 2] Building action order...")
        self.action_order = build_action_order(all_usecases)
        print(f"Learned {len(self.action_order)} unique actions")
        
        # Step 3: Parse all UML files
        print("\n[Step 3] Parsing UML files...")
        for root, _, files in os.walk(dataset_path):
            for file in files:
                if file.endswith(".puml"):
                    puml_path = os.path.join(root, file)
                    parsed = parse_and_correct_plantuml(puml_path, self.action_order)
                    self.parsed_models.append(parsed)
        
        print(f"Parsed {len(self.parsed_models)} UML models")
        
        # Step 4: Build unified graphs
        print("\n[Step 4] Building unified graphs...")
        for i, model in enumerate(self.parsed_models):
            # Convert to UMLElements
            elements = UMLElements(
                actors=model['actors'],
                usecases=model['usecases'],
                classes=model['classes'],
                activities=model['activities'],
                includes=model['includes'],
                extends=model['extends'],
                dependencies=model['dependencies'],
                control_flows=model['control_flows'],
                associations=model['associations']
            )
            
            # Build unified graph
            builder = UnifiedGraphBuilder()
            graph = builder.build_unified_graph(elements)
            self.unified_graphs.append(graph)
            
            if (i + 1) % 5 == 0:
                print(f"  Processed {i + 1}/{len(self.parsed_models)} models")
        
        print(f"\n✓ Created {len(self.unified_graphs)} unified graphs")
        
        return self.unified_graphs
    
    def process_single_file(self, puml_path: str) -> nx.DiGraph:
        """
        Process a single PlantUML file
        
        Args:
            puml_path: Path to .puml file
            
        Returns:
            Unified graph
        """
        # Parse
        if not self.action_order:
            # Build action order from this file
            nodes, _ = parse_plantuml_raw(puml_path)
            usecases = [name for name, t in nodes.items() if t == "usecase"]
            self.action_order = build_action_order(usecases)
        
        parsed = parse_and_correct_plantuml(puml_path, self.action_order)
        
        # Convert to UMLElements
        elements = UMLElements(
            actors=parsed['actors'],
            usecases=parsed['usecases'],
            classes=parsed['classes'],
            activities=parsed['activities'],
            includes=parsed['includes'],
            extends=parsed['extends'],
            dependencies=parsed['dependencies'],
            control_flows=parsed['control_flows'],
            associations=parsed['associations']
        )
        
        # Build unified graph
        builder = UnifiedGraphBuilder()
        graph = builder.build_unified_graph(elements)
        
        return graph, builder
    
    def get_statistics(self):
        """Get statistics for all graphs"""
        if not self.unified_graphs:
            return None
        
        total_nodes = sum(g.number_of_nodes() for g in self.unified_graphs)
        total_edges = sum(g.number_of_edges() for g in self.unified_graphs)
        
        stats = {
            'total_graphs': len(self.unified_graphs),
            'total_nodes': total_nodes,
            'total_edges': total_edges,
            'avg_nodes_per_graph': total_nodes / len(self.unified_graphs),
            'avg_edges_per_graph': total_edges / len(self.unified_graphs),
            'min_nodes': min(g.number_of_nodes() for g in self.unified_graphs),
            'max_nodes': max(g.number_of_nodes() for g in self.unified_graphs),
            'min_edges': min(g.number_of_edges() for g in self.unified_graphs),
            'max_edges': max(g.number_of_edges() for g in self.unified_graphs)
        }
        
        return stats


# ============================================================================
# PART 3: CONVERT UNIFIED GRAPH TO PYTORCH GEOMETRIC
# ============================================================================

def unified_graph_to_pyg(unified_graph: nx.DiGraph) -> Data:
    """
    Convert NetworkX unified graph to PyTorch Geometric Data
    
    Args:
        unified_graph: Unified behavioral graph
        
    Returns:
        PyTorch Geometric Data object
    """
    # Create node mapping
    node_list = list(unified_graph.nodes())
    node_to_idx = {node: idx for idx, node in enumerate(node_list)}
    
    # Create node features
    node_features = []
    node_type_map = {'actor': 0, 'usecase': 1, 'class': 2, 'activity': 3}
    
    for node in node_list:
        node_data = unified_graph.nodes[node]
        node_type = node_data.get('node_type', 'usecase')
        node_type_enc = node_type_map.get(node_type, 1)
        
        # Feature: [node_type, degree, name_length]
        degree = unified_graph.degree(node)
        name_length = len(node_data.get('name', ''))
        
        feature = [node_type_enc, degree, name_length]
        node_features.append(feature)
    
    # Create edge index
    edges = []
    for src, tgt in unified_graph.edges():
        edges.append([node_to_idx[src], node_to_idx[tgt]])
    
    # Convert to tensors
    x = torch.tensor(node_features, dtype=torch.float)
    edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous() if edges else torch.zeros((2, 0), dtype=torch.long)
    
    return Data(x=x, edge_index=edge_index, num_nodes=len(node_list))


# ============================================================================
# PART 4: EXAMPLE USAGE
# ============================================================================

def main():
    """Example: Complete pipeline from PlantUML to Unified Graph"""
    
    # Option 1: Process entire dataset
    print("Option 1: Process dataset\n")
    
    # Uncomment when you have a dataset
    # pipeline = UMLToUnifiedGraph()
    # graphs = pipeline.process_dataset("/path/to/uml_dataset")
    # stats = pipeline.get_statistics()
    # print("\nDataset Statistics:")
    # for key, value in stats.items():
    #     print(f"  {key}: {value}")
    
    # Option 2: Process single file
    print("\nOption 2: Process single file\n")
    
    # Create a sample UML file for demonstration
    sample_puml = """@startuml
actor User
usecase Login
usecase ValidateCredentials
class AuthService

User --> Login
Login ..> ValidateCredentials : <<include>>
ValidateCredentials --> AuthService
@enduml"""
    
    # Save sample
    with open('/tmp/sample.puml', 'w') as f:
        f.write(sample_puml)
    
    # Process
    pipeline = UMLToUnifiedGraph()
    graph, builder = pipeline.process_single_file('/tmp/sample.puml')
    
    # Show statistics
    stats = builder.get_graph_statistics()
    print("\nGraph Statistics:")
    print(f"  Nodes: {stats['total_nodes']}")
    print(f"  Edges: {stats['total_edges']}")
    print(f"  Is DAG: {stats['is_dag']}")
    
    # Visualize
    builder.visualize(output_path='/tmp/unified_graph_sample.png')
    
    # Convert to PyG
    pyg_data = unified_graph_to_pyg(graph)
    print(f"\nPyTorch Geometric Data:")
    print(f"  Features shape: {pyg_data.x.shape}")
    print(f"  Edge index shape: {pyg_data.edge_index.shape}")
    print(f"  Number of nodes: {pyg_data.num_nodes}")
    
    print("\n✓ Pipeline complete!")


if __name__ == "__main__":
    main()
