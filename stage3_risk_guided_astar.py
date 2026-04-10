"""
STAGE 3: RISK-GUIDED A* PATH GENERATION FOR TEST CASE GENERATION

This module implements:
1. GNN-based Risk Prediction
2. Risk-Guided A* Path Search
3. Test Path Generation
4. Coverage Analysis

Based on the project architecture from UML_TestCase_Second_Review_Neon_Theme.pptx
"""

import networkx as nx
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GCNConv, GATConv, global_mean_pool
from torch_geometric.data import Data
from typing import List, Tuple, Dict, Set, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import heapq
import matplotlib.pyplot as plt
from enum import Enum


# ============================================================================
# PART 1: DATA STRUCTURES
# ============================================================================

class RiskLevel(Enum):
    """Risk levels for nodes"""
    CRITICAL = "critical"    # Risk > 0.8
    HIGH = "high"           # Risk > 0.6
    MEDIUM = "medium"       # Risk > 0.4
    LOW = "low"             # Risk > 0.2
    MINIMAL = "minimal"     # Risk <= 0.2


@dataclass
class TestPath:
    """Represents a test execution path"""
    nodes: List[str]
    edges: List[Tuple[str, str]]
    risk_score: float
    path_cost: float
    coverage: float
    priority: int
    
    def __str__(self):
        return f"Path({len(self.nodes)} nodes, risk={self.risk_score:.3f}, cost={self.path_cost:.3f})"
    
    def __repr__(self):
        return self.__str__()


@dataclass
class RiskScores:
    """Container for node risk scores"""
    node_risks: Dict[str, float] = field(default_factory=dict)
    edge_risks: Dict[Tuple[str, str], float] = field(default_factory=dict)
    global_risk: float = 0.0
    
    def get_node_risk(self, node: str) -> float:
        """Get risk score for a node"""
        return self.node_risks.get(node, 0.5)  # Default medium risk
    
    def get_edge_risk(self, edge: Tuple[str, str]) -> float:
        """Get risk score for an edge"""
        return self.edge_risks.get(edge, 0.5)
    
    def get_risk_level(self, node: str) -> RiskLevel:
        """Get risk level category for a node"""
        risk = self.get_node_risk(node)
        if risk > 0.8:
            return RiskLevel.CRITICAL
        elif risk > 0.6:
            return RiskLevel.HIGH
        elif risk > 0.4:
            return RiskLevel.MEDIUM
        elif risk > 0.2:
            return RiskLevel.LOW
        else:
            return RiskLevel.MINIMAL


# ============================================================================
# PART 2: GNN-BASED RISK PREDICTOR
# ============================================================================

class RiskPredictionGNN(nn.Module):
    """
    Graph Neural Network for predicting risk scores of UML nodes.
    
    Architecture:
    - 2 GCN layers for graph convolution
    - Batch normalization
    - Dropout for regularization
    - Node-level risk prediction
    """
    
    def __init__(self, 
                 input_dim: int = 64,
                 hidden_dim: int = 128,
                 output_dim: int = 1,
                 dropout: float = 0.3):
        super(RiskPredictionGNN, self).__init__()
        
        # Graph convolutional layers
        self.conv1 = GCNConv(input_dim, hidden_dim)
        self.conv2 = GCNConv(hidden_dim, hidden_dim)
        
        # Batch normalization
        self.bn1 = nn.BatchNorm1d(hidden_dim)
        self.bn2 = nn.BatchNorm1d(hidden_dim)
        
        # Dropout
        self.dropout = nn.Dropout(dropout)
        
        # Risk prediction head
        self.risk_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, output_dim),
            nn.Sigmoid()  # Risk score between 0 and 1
        )
    
    def forward(self, x, edge_index):
        """
        Forward pass
        
        Args:
            x: Node features [num_nodes, input_dim]
            edge_index: Edge connections [2, num_edges]
            
        Returns:
            risk_scores: Risk scores for each node [num_nodes, 1]
        """
        # First GCN layer
        x = self.conv1(x, edge_index)
        x = self.bn1(x)
        x = F.relu(x)
        x = self.dropout(x)
        
        # Second GCN layer
        x = self.conv2(x, edge_index)
        x = self.bn2(x)
        x = F.relu(x)
        x = self.dropout(x)
        
        # Risk prediction
        risk_scores = self.risk_head(x)
        
        return risk_scores


class RiskPredictor:
    """
    Wrapper class for risk prediction from UML graphs.
    """
    
    def __init__(self, model: Optional[RiskPredictionGNN] = None):
        self.model = model or RiskPredictionGNN()
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.to(self.device)
    
    def predict_risks(self, graph: nx.DiGraph) -> RiskScores:
        """
        Predict risk scores for all nodes in the graph.
        
        Args:
            graph: NetworkX directed graph
            
        Returns:
            RiskScores object with node and edge risks
        """
        # Convert NetworkX to PyTorch Geometric format
        pyg_data = self._networkx_to_pyg(graph)
        
        # Predict risks
        self.model.eval()
        with torch.no_grad():
            x = pyg_data.x.to(self.device)
            edge_index = pyg_data.edge_index.to(self.device)
            
            risk_scores = self.model(x, edge_index)
            risk_scores = risk_scores.cpu().numpy().flatten()
        
        # Build RiskScores object
        risks = RiskScores()
        
        node_list = list(graph.nodes())
        for i, node in enumerate(node_list):
            risks.node_risks[node] = float(risk_scores[i])
        
        # Calculate edge risks (average of source and target)
        for src, tgt in graph.edges():
            src_risk = risks.get_node_risk(src)
            tgt_risk = risks.get_node_risk(tgt)
            risks.edge_risks[(src, tgt)] = (src_risk + tgt_risk) / 2.0
        
        # Calculate global risk
        risks.global_risk = float(np.mean(risk_scores))
        
        return risks
    
    def _networkx_to_pyg(self, graph: nx.DiGraph) -> Data:
        """Convert NetworkX graph to PyTorch Geometric Data"""
        # Create node mapping
        node_list = list(graph.nodes())
        node_to_idx = {node: i for i, node in enumerate(node_list)}
        
        # Create edge index
        edge_list = []
        for src, tgt in graph.edges():
            edge_list.append([node_to_idx[src], node_to_idx[tgt]])
        
        if edge_list:
            edge_index = torch.tensor(edge_list, dtype=torch.long).t().contiguous()
        else:
            edge_index = torch.empty((2, 0), dtype=torch.long)
        
        # Create node features (simple one-hot encoding based on node type)
        num_nodes = len(node_list)
        x = self._create_node_features(graph, node_list)
        
        return Data(x=x, edge_index=edge_index)
    
    def _create_node_features(self, graph: nx.DiGraph, node_list: List[str]) -> torch.Tensor:
        """Create node features from graph"""
        num_nodes = len(node_list)
        feature_dim = 64  # Match model input_dim
        
        features = []
        for node in node_list:
            node_data = graph.nodes[node]
            node_type = node_data.get('type', 'usecase')
            
            # Create feature vector
            feat = np.zeros(feature_dim)
            
            # Type encoding (first 4 dimensions)
            if node_type == 'actor':
                feat[0] = 1.0
            elif node_type == 'usecase':
                feat[1] = 1.0
            elif node_type == 'class':
                feat[2] = 1.0
            elif node_type == 'activity':
                feat[3] = 1.0
            
            # Degree features
            in_degree = graph.in_degree(node)
            out_degree = graph.out_degree(node)
            feat[4] = in_degree / max(1, num_nodes)
            feat[5] = out_degree / max(1, num_nodes)
            
            # Centrality (if available)
            try:
                betweenness = nx.betweenness_centrality(graph, endpoints=True)[node]
                feat[6] = betweenness
            except:
                feat[6] = 0.0
            
            features.append(feat)
        
        return torch.tensor(features, dtype=torch.float32)


# ============================================================================
# PART 3: RISK-GUIDED A* ALGORITHM
# ============================================================================

class RiskGuidedAStar:
    """
    Risk-Guided A* Search Algorithm for generating test paths.
    
    Features:
    - Prioritizes high-risk nodes
    - Uses heuristic-based search
    - Finds optimal execution paths
    - Considers both risk and path cost
    """
    
    def __init__(self, 
                 graph: nx.DiGraph,
                 risk_scores: RiskScores,
                 alpha: float = 0.7,
                 beta: float = 0.3):
        """
        Initialize Risk-Guided A* algorithm.
        
        Args:
            graph: UML unified graph
            risk_scores: Risk scores from GNN
            alpha: Weight for risk score (0-1)
            beta: Weight for path cost (0-1)
        """
        self.graph = graph
        self.risk_scores = risk_scores
        self.alpha = alpha  # Risk weight
        self.beta = beta    # Cost weight
        
        assert abs(alpha + beta - 1.0) < 0.01, "alpha + beta must equal 1.0"
    
    def find_test_paths(self,
                       start_nodes: Optional[List[str]] = None,
                       num_paths: int = 10,
                       max_path_length: int = 20,
                       prioritize_risk: bool = True) -> List[TestPath]:
        """
        Find optimal test paths using Risk-Guided A*.
        
        Args:
            start_nodes: Starting nodes (actors), auto-detect if None
            num_paths: Number of paths to generate
            max_path_length: Maximum path length
            prioritize_risk: Whether to prioritize high-risk paths
            
        Returns:
            List of TestPath objects
        """
        # Auto-detect start nodes (actors)
        if start_nodes is None:
            start_nodes = self._find_start_nodes()
        
        all_paths = []
        
        for start in start_nodes:
            # Find all reachable end nodes
            end_nodes = self._find_end_nodes(start)
            
            for end in end_nodes[:5]:  # Limit end nodes per start
                # Run A* search
                paths = self._astar_search(
                    start, end,
                    max_paths=max(num_paths // len(start_nodes), 1),
                    max_length=max_path_length
                )
                all_paths.extend(paths)
        
        # Sort by risk score (descending) or path cost (ascending)
        if prioritize_risk:
            all_paths.sort(key=lambda p: (-p.risk_score, p.path_cost))
        else:
            all_paths.sort(key=lambda p: (p.path_cost, -p.risk_score))
        
        # Assign priorities
        for i, path in enumerate(all_paths[:num_paths]):
            path.priority = i + 1
        
        return all_paths[:num_paths]
    
    def _find_start_nodes(self) -> List[str]:
        """Find all actor nodes (entry points)"""
        actors = []
        for node, data in self.graph.nodes(data=True):
            if data.get('type') == 'actor':
                actors.append(node)
        
        if not actors:
            # If no actors, use nodes with in_degree = 0
            actors = [n for n in self.graph.nodes() if self.graph.in_degree(n) == 0]
        
        return actors if actors else [list(self.graph.nodes())[0]]
    
    def _find_end_nodes(self, start: str) -> List[str]:
        """Find all reachable end nodes from start"""
        try:
            reachable = nx.descendants(self.graph, start)
            # Prefer nodes with out_degree = 0 (end points)
            end_nodes = [n for n in reachable if self.graph.out_degree(n) == 0]
            
            if not end_nodes:
                # If no terminal nodes, use all reachable
                end_nodes = list(reachable)
            
            return end_nodes
        except:
            return []
    
    def _astar_search(self,
                     start: str,
                     goal: str,
                     max_paths: int = 5,
                     max_length: int = 20) -> List[TestPath]:
        """
        A* search from start to goal.
        
        Returns multiple paths with different characteristics.
        """
        paths_found = []
        
        # Priority queue: (f_score, g_score, path_nodes, path_edges, visited)
        initial_risk = self.risk_scores.get_node_risk(start)
        h_score = self._heuristic(start, goal)
        f_score = self.alpha * (1 - initial_risk) + self.beta * h_score
        
        pq = [(f_score, 0, [start], [], {start})]
        
        while pq and len(paths_found) < max_paths:
            f, g, path_nodes, path_edges, visited = heapq.heappop(pq)
            
            current = path_nodes[-1]
            
            # Check if reached goal
            if current == goal:
                # Calculate path metrics
                path_risk = self._calculate_path_risk(path_nodes)
                path_cost = g
                coverage = len(visited) / len(self.graph.nodes())
                
                test_path = TestPath(
                    nodes=path_nodes.copy(),
                    edges=path_edges.copy(),
                    risk_score=path_risk,
                    path_cost=path_cost,
                    coverage=coverage,
                    priority=0  # Will be assigned later
                )
                
                paths_found.append(test_path)
                continue
            
            # Check max length
            if len(path_nodes) >= max_length:
                continue
            
            # Explore neighbors
            for neighbor in self.graph.successors(current):
                if neighbor in visited:
                    continue
                
                # Calculate costs
                edge = (current, neighbor)
                edge_risk = self.risk_scores.get_edge_risk(edge)
                node_risk = self.risk_scores.get_node_risk(neighbor)
                
                # g_score: accumulated cost (lower is better)
                new_g = g + (1 - edge_risk)  # Lower risk = higher cost in A*
                
                # h_score: heuristic to goal
                h = self._heuristic(neighbor, goal)
                
                # f_score: total cost (prioritize high risk)
                new_f = self.alpha * (1 - node_risk) + self.beta * (new_g + h)
                
                # Add to queue
                new_path_nodes = path_nodes + [neighbor]
                new_path_edges = path_edges + [edge]
                new_visited = visited | {neighbor}
                
                heapq.heappush(pq, (
                    new_f, new_g,
                    new_path_nodes, new_path_edges, new_visited
                ))
        
        return paths_found
    
    def _heuristic(self, current: str, goal: str) -> float:
        """
        Heuristic function for A*.
        
        Uses shortest path distance if available.
        """
        try:
            # Try to find shortest path length
            path_length = nx.shortest_path_length(self.graph, current, goal)
            return path_length
        except:
            # If no path exists, return large value
            return float('inf')
    
    def _calculate_path_risk(self, nodes: List[str]) -> float:
        """Calculate total risk score for a path"""
        if not nodes:
            return 0.0
        
        risks = [self.risk_scores.get_node_risk(n) for n in nodes]
        
        # Use weighted average (higher weight for later nodes)
        weights = np.linspace(1, 2, len(risks))
        weighted_risk = np.average(risks, weights=weights)
        
        return float(weighted_risk)


# ============================================================================
# PART 4: PATH ANALYSIS AND COVERAGE
# ============================================================================

class PathAnalyzer:
    """
    Analyzes test paths for coverage, redundancy, and quality.
    """
    
    def __init__(self, graph: nx.DiGraph):
        self.graph = graph
        self.all_nodes = set(graph.nodes())
        self.all_edges = set(graph.edges())
    
    def analyze_coverage(self, paths: List[TestPath]) -> Dict:
        """
        Analyze coverage metrics for a set of paths.
        
        Returns:
            Dict with coverage statistics
        """
        # Collect all covered nodes and edges
        covered_nodes = set()
        covered_edges = set()
        
        for path in paths:
            covered_nodes.update(path.nodes)
            covered_edges.update(path.edges)
        
        # Calculate coverage percentages
        node_coverage = len(covered_nodes) / len(self.all_nodes) if self.all_nodes else 0
        edge_coverage = len(covered_edges) / len(self.all_edges) if self.all_edges else 0
        
        # Analyze by node type
        type_coverage = self._analyze_type_coverage(covered_nodes)
        
        return {
            'node_coverage': node_coverage,
            'edge_coverage': edge_coverage,
            'nodes_covered': len(covered_nodes),
            'edges_covered': len(covered_edges),
            'total_nodes': len(self.all_nodes),
            'total_edges': len(self.all_edges),
            'type_coverage': type_coverage,
            'num_paths': len(paths)
        }
    
    def _analyze_type_coverage(self, covered_nodes: Set[str]) -> Dict:
        """Analyze coverage by node type"""
        type_counts = defaultdict(lambda: {'total': 0, 'covered': 0})
        
        for node in self.all_nodes:
            node_type = self.graph.nodes[node].get('type', 'unknown')
            type_counts[node_type]['total'] += 1
            
            if node in covered_nodes:
                type_counts[node_type]['covered'] += 1
        
        type_coverage = {}
        for node_type, counts in type_counts.items():
            coverage = counts['covered'] / counts['total'] if counts['total'] > 0 else 0
            type_coverage[node_type] = {
                'coverage': coverage,
                'covered': counts['covered'],
                'total': counts['total']
            }
        
        return type_coverage
    
    def find_redundant_paths(self, paths: List[TestPath], threshold: float = 0.8) -> List[Tuple[int, int]]:
        """
        Find redundant paths (high overlap).
        
        Returns:
            List of (path_i, path_j) tuples that are redundant
        """
        redundant = []
        
        for i in range(len(paths)):
            for j in range(i + 1, len(paths)):
                similarity = self._path_similarity(paths[i], paths[j])
                
                if similarity >= threshold:
                    redundant.append((i, j))
        
        return redundant
    
    def _path_similarity(self, path1: TestPath, path2: TestPath) -> float:
        """Calculate Jaccard similarity between two paths"""
        set1 = set(path1.nodes)
        set2 = set(path2.nodes)
        
        if not set1 and not set2:
            return 1.0
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def remove_redundant_paths(self, paths: List[TestPath], threshold: float = 0.8) -> List[TestPath]:
        """Remove redundant paths, keeping higher priority ones"""
        redundant_pairs = self.find_redundant_paths(paths, threshold)
        
        # Build set of indices to remove (keep lower index = higher priority)
        to_remove = set()
        for i, j in redundant_pairs:
            # Remove path with lower risk score
            if paths[i].risk_score >= paths[j].risk_score:
                to_remove.add(j)
            else:
                to_remove.add(i)
        
        # Keep non-redundant paths
        filtered = [p for i, p in enumerate(paths) if i not in to_remove]
        
        return filtered


# ============================================================================
# PART 5: COMPLETE STAGE 3 PIPELINE
# ============================================================================

class TestPathGenerator:
    """
    Complete Stage 3 pipeline: Risk prediction + Path generation.
    """
    
    def __init__(self, 
                 graph: nx.DiGraph,
                 risk_predictor: Optional[RiskPredictor] = None):
        """
        Initialize test path generator.
        
        Args:
            graph: Unified UML graph from Stage 2
            risk_predictor: Optional pre-trained risk predictor
        """
        self.graph = graph
        self.risk_predictor = risk_predictor or RiskPredictor()
        self.risk_scores = None
        self.paths = []
    
    def generate_test_paths(self,
                          num_paths: int = 10,
                          max_path_length: int = 20,
                          remove_redundant: bool = True,
                          redundancy_threshold: float = 0.8) -> List[TestPath]:
        """
        Complete pipeline to generate test paths.
        
        Args:
            num_paths: Number of paths to generate
            max_path_length: Maximum path length
            remove_redundant: Whether to remove redundant paths
            redundancy_threshold: Similarity threshold for redundancy
            
        Returns:
            List of TestPath objects
        """
        print("="*70)
        print("STAGE 3: RISK-GUIDED TEST PATH GENERATION")
        print("="*70)
        
        # Step 1: Predict risk scores
        print("\n[1/4] Predicting risk scores with GNN...")
        self.risk_scores = self.risk_predictor.predict_risks(self.graph)
        print(f"  ✓ Global risk score: {self.risk_scores.global_risk:.3f}")
        print(f"  ✓ Analyzed {len(self.risk_scores.node_risks)} nodes")
        
        # Step 2: Initialize A* algorithm
        print("\n[2/4] Initializing Risk-Guided A* algorithm...")
        astar = RiskGuidedAStar(
            self.graph,
            self.risk_scores,
            alpha=0.7,  # 70% weight on risk
            beta=0.3    # 30% weight on cost
        )
        
        # Step 3: Generate paths
        print(f"\n[3/4] Generating {num_paths} test paths...")
        self.paths = astar.find_test_paths(
            num_paths=num_paths * 2 if remove_redundant else num_paths,
            max_path_length=max_path_length,
            prioritize_risk=True
        )
        print(f"  ✓ Generated {len(self.paths)} candidate paths")
        
        # Step 4: Remove redundant paths
        if remove_redundant and len(self.paths) > 1:
            print(f"\n[4/4] Removing redundant paths (threshold={redundancy_threshold})...")
            analyzer = PathAnalyzer(self.graph)
            original_count = len(self.paths)
            self.paths = analyzer.remove_redundant_paths(self.paths, redundancy_threshold)
            removed = original_count - len(self.paths)
            print(f"  ✓ Removed {removed} redundant paths")
            print(f"  ✓ Kept {len(self.paths)} unique paths")
        
        # Limit to requested number
        self.paths = self.paths[:num_paths]
        
        # Re-assign priorities
        for i, path in enumerate(self.paths):
            path.priority = i + 1
        
        print(f"\n{'='*70}")
        print(f"GENERATION COMPLETE: {len(self.paths)} test paths ready")
        print(f"{'='*70}")
        
        return self.paths
    
    def get_coverage_report(self) -> Dict:
        """Get coverage analysis for generated paths"""
        if not self.paths:
            return {}
        
        analyzer = PathAnalyzer(self.graph)
        return analyzer.analyze_coverage(self.paths)
    
    def print_path_summary(self):
        """Print summary of generated paths"""
        if not self.paths:
            print("No paths generated yet.")
            return
        
        print("\n" + "="*70)
        print("TEST PATH SUMMARY")
        print("="*70)
        
        for path in self.paths:
            risk_level = self.risk_scores.get_risk_level(path.nodes[0])
            print(f"\nPath {path.priority}:")
            print(f"  Length: {len(path.nodes)} nodes")
            print(f"  Risk: {path.risk_score:.3f} ({risk_level.value})")
            print(f"  Cost: {path.path_cost:.3f}")
            print(f"  Coverage: {path.coverage*100:.1f}%")
            print(f"  Nodes: {' → '.join(path.nodes[:5])}" + 
                  (" → ..." if len(path.nodes) > 5 else ""))
        
        # Coverage report
        coverage = self.get_coverage_report()
        print("\n" + "="*70)
        print("COVERAGE ANALYSIS")
        print("="*70)
        print(f"Node Coverage: {coverage['node_coverage']*100:.1f}% ({coverage['nodes_covered']}/{coverage['total_nodes']})")
        print(f"Edge Coverage: {coverage['edge_coverage']*100:.1f}% ({coverage['edges_covered']}/{coverage['total_edges']})")
        
        print("\nCoverage by Type:")
        for node_type, stats in coverage.get('type_coverage', {}).items():
            print(f"  {node_type}: {stats['coverage']*100:.1f}% ({stats['covered']}/{stats['total']})")
    
    def visualize_path(self, path_index: int = 0, output_path: str = 'test_path.png'):
        """Visualize a specific test path"""
        if path_index >= len(self.paths):
            print(f"Path index {path_index} out of range.")
            return
        
        path = self.paths[path_index]
        
        # Create subgraph with path
        path_graph = self.graph.subgraph(path.nodes).copy()
        
        plt.figure(figsize=(14, 10))
        
        # Layout
        pos = nx.spring_layout(path_graph, k=2, iterations=50)
        
        # Node colors by risk
        node_colors = []
        for node in path_graph.nodes():
            risk = self.risk_scores.get_node_risk(node)
            if risk > 0.8:
                node_colors.append('#FF0000')  # Critical - Red
            elif risk > 0.6:
                node_colors.append('#FF6B00')  # High - Orange
            elif risk > 0.4:
                node_colors.append('#FFB700')  # Medium - Yellow
            elif risk > 0.2:
                node_colors.append('#4ECDC4')  # Low - Cyan
            else:
                node_colors.append('#95E1D3')  # Minimal - Light green
        
        # Draw nodes
        nx.draw_networkx_nodes(
            path_graph, pos,
            node_color=node_colors,
            node_size=1500,
            alpha=0.9,
            edgecolors='black',
            linewidths=2
        )
        
        # Draw edges in path
        nx.draw_networkx_edges(
            path_graph, pos,
            edgelist=path.edges,
            edge_color='#2C3E50',
            width=3,
            arrows=True,
            arrowsize=25,
            arrowstyle='->',
            connectionstyle='arc3,rad=0.1'
        )
        
        # Draw labels
        labels = {node: f"{data['name'][:15]}\n(R:{self.risk_scores.get_node_risk(node):.2f})" 
                 for node, data in path_graph.nodes(data=True)}
        nx.draw_networkx_labels(
            path_graph, pos,
            labels=labels,
            font_size=8,
            font_weight='bold'
        )
        
        # Title
        plt.title(
            f"Test Path {path.priority}: Risk={path.risk_score:.3f}, "
            f"Cost={path.path_cost:.3f}, Coverage={path.coverage*100:.1f}%",
            fontsize=14,
            fontweight='bold'
        )
        
        # Legend
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#FF0000', 
                      markersize=10, label='Critical (R>0.8)'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#FF6B00', 
                      markersize=10, label='High (R>0.6)'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#FFB700', 
                      markersize=10, label='Medium (R>0.4)'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#4ECDC4', 
                      markersize=10, label='Low (R>0.2)'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#95E1D3', 
                      markersize=10, label='Minimal (R≤0.2)')
        ]
        plt.legend(handles=legend_elements, loc='best', fontsize=9)
        
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.show()
        
        print(f"Path visualization saved to: {output_path}")


# ============================================================================
# PART 6: EXPORT TO STAGE 4 (LLM Test Case Generation)
# ============================================================================

def export_paths_for_llm(paths: List[TestPath], 
                        graph: nx.DiGraph,
                        output_path: str = 'paths_for_llm.json') -> Dict:
    """
    Export paths in format ready for LLM test case generation (Stage 4).
    
    Args:
        paths: List of TestPath objects
        graph: Original UML graph
        output_path: Path to save JSON
        
    Returns:
        Dictionary with path data
    """
    import json
    
    export_data = {
        'metadata': {
            'num_paths': len(paths),
            'total_nodes': graph.number_of_nodes(),
            'total_edges': graph.number_of_edges()
        },
        'paths': []
    }
    
    for path in paths:
        path_data = {
            'priority': path.priority,
            'risk_score': float(path.risk_score),
            'path_cost': float(path.path_cost),
            'coverage': float(path.coverage),
            'length': len(path.nodes),
            'nodes': [],
            'edges': []
        }
        
        # Add node details
        for node in path.nodes:
            node_info = {
                'id': node,
                'name': graph.nodes[node].get('name', node),
                'type': graph.nodes[node].get('type', 'unknown')
            }
            path_data['nodes'].append(node_info)
        
        # Add edge details
        for src, tgt in path.edges:
            edge_info = {
                'source': src,
                'target': tgt,
                'source_name': graph.nodes[src].get('name', src),
                'target_name': graph.nodes[tgt].get('name', tgt)
            }
            path_data['edges'].append(edge_info)
        
        export_data['paths'].append(path_data)
    
    # Save to JSON
    with open(output_path, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print(f"\n✓ Exported {len(paths)} paths to {output_path}")
    print(f"  Ready for Stage 4: LLM Test Case Generation")
    
    return export_data


if __name__ == "__main__":
    print("Stage 3: Risk-Guided A* Path Generation")
    print("This module is imported by the main pipeline.")
