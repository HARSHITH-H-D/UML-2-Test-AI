# 🎯 STAGE 3: RISK-GUIDED A* PATH GENERATION

## 📋 Complete Documentation

Based on: UML_TestCase_Second_Review_Neon_Theme.pptx

---

## 🎨 Overview

Stage 3 implements intelligent test path generation using:
1. **GNN-based Risk Prediction** - Identifies high-risk components
2. **Risk-Guided A* Search** - Finds optimal execution paths
3. **Coverage Analysis** - Ensures comprehensive testing
4. **Redundancy Elimination** - Removes duplicate paths

---

## 🏗️ Architecture

```
Unified Graph (from Stage 2)
         ↓
┌──────────────────────────────────────┐
│  GNN Risk Predictor                  │
│  - Learns structural patterns        │
│  - Predicts node risk scores (0-1)   │
│  - Calculates edge risks             │
└──────────────────────────────────────┘
         ↓
    Risk Scores
         ↓
┌──────────────────────────────────────┐
│  Risk-Guided A* Algorithm            │
│  - Prioritizes high-risk nodes       │
│  - Uses heuristic search             │
│  - Finds optimal paths               │
│  - Balances risk vs cost             │
└──────────────────────────────────────┘
         ↓
   Candidate Paths
         ↓
┌──────────────────────────────────────┐
│  Path Analyzer                       │
│  - Coverage analysis                 │
│  - Redundancy detection              │
│  - Priority assignment               │
└──────────────────────────────────────┘
         ↓
  Final Test Paths
  (Ready for Stage 4: LLM)
```

---

## 🧠 1. GNN Risk Predictor

### Purpose
Predict risk scores for each UML node using Graph Neural Networks.

### Architecture
```python
RiskPredictionGNN:
  - Input: Node features (64 dim)
  - GCN Layer 1: 64 → 128
  - Batch Normalization
  - ReLU + Dropout (0.3)
  - GCN Layer 2: 128 → 128
  - Batch Normalization
  - ReLU + Dropout (0.3)
  - Risk Head: 128 → 64 → 1
  - Sigmoid activation (output: 0-1)
```

### Node Features
- **Type encoding** (one-hot): actor, usecase, class, activity
- **Degree features**: in_degree, out_degree (normalized)
- **Centrality**: betweenness centrality
- **Total dimensions**: 64

### Risk Levels
| Level | Range | Color | Description |
|-------|-------|-------|-------------|
| **CRITICAL** | > 0.8 | 🔴 Red | Requires immediate attention |
| **HIGH** | 0.6-0.8 | 🟠 Orange | High priority testing |
| **MEDIUM** | 0.4-0.6 | 🟡 Yellow | Standard testing |
| **LOW** | 0.2-0.4 | 🔵 Cyan | Lower priority |
| **MINIMAL** | ≤ 0.2 | 🟢 Green | Minimal risk |

### Usage
```python
from stage3_risk_guided_astar import RiskPredictor

# Initialize predictor
predictor = RiskPredictor()

# Predict risks for graph
risk_scores = predictor.predict_risks(graph)

# Get node risk
node_risk = risk_scores.get_node_risk('N0')  # 0.0 - 1.0

# Get risk level
risk_level = risk_scores.get_risk_level('N0')  # RiskLevel enum
```

---

## 🔍 2. Risk-Guided A* Algorithm

### Purpose
Find optimal test execution paths that prioritize high-risk components.

### Algorithm

```
FUNCTION RiskGuidedAStar(graph, start, goal, risk_scores):
    priority_queue = [(f_score(start), 0, [start])]
    
    WHILE priority_queue is not empty:
        f, g, path = pop(priority_queue)
        current = path[-1]
        
        IF current == goal:
            RETURN path
        
        FOR each neighbor of current:
            IF neighbor not visited:
                # Calculate scores
                edge_risk = risk_scores.get_edge_risk(current, neighbor)
                node_risk = risk_scores.get_node_risk(neighbor)
                
                # g_score: accumulated cost
                new_g = g + (1 - edge_risk)
                
                # h_score: heuristic to goal
                h = shortest_path_length(neighbor, goal)
                
                # f_score: total cost (prioritize high risk)
                new_f = α × (1 - node_risk) + β × (new_g + h)
                
                # Add to queue
                push(priority_queue, (new_f, new_g, path + [neighbor]))
    
    RETURN []
```

### Cost Function

```
f(n) = α × (1 - risk(n)) + β × (g(n) + h(n))
```

Where:
- **α**: Risk weight (default 0.7) - Higher value prioritizes risk
- **β**: Cost weight (default 0.3) - Higher value prioritizes shorter paths
- **g(n)**: Path cost from start to n
- **h(n)**: Heuristic from n to goal (shortest path estimate)
- **risk(n)**: GNN-predicted risk score for node n

**Note**: We use `(1 - risk)` so that high-risk nodes have lower f-scores and are explored first.

### Parameters
| Parameter | Default | Description |
|-----------|---------|-------------|
| `alpha` | 0.7 | Weight for risk (70% risk, 30% cost) |
| `beta` | 0.3 | Weight for path cost |
| `num_paths` | 10 | Number of paths to generate |
| `max_path_length` | 20 | Maximum nodes per path |

### Usage
```python
from stage3_risk_guided_astar import RiskGuidedAStar

# Initialize A* algorithm
astar = RiskGuidedAStar(
    graph=unified_graph,
    risk_scores=risk_scores,
    alpha=0.7,  # 70% risk weight
    beta=0.3    # 30% cost weight
)

# Find test paths
test_paths = astar.find_test_paths(
    start_nodes=None,  # Auto-detect actors
    num_paths=10,
    max_path_length=20,
    prioritize_risk=True
)
```

---

## 📊 3. Path Analysis

### TestPath Object

```python
@dataclass
class TestPath:
    nodes: List[str]           # Node IDs in path
    edges: List[Tuple[str, str]]  # Edges traversed
    risk_score: float          # Overall path risk (0-1)
    path_cost: float           # Total path cost
    coverage: float            # Coverage percentage (0-1)
    priority: int              # Priority rank (1 = highest)
```

### Coverage Metrics

```python
coverage_report = {
    'node_coverage': 0.85,     # 85% of nodes covered
    'edge_coverage': 0.78,     # 78% of edges covered
    'nodes_covered': 17,
    'edges_covered': 23,
    'total_nodes': 20,
    'total_edges': 30,
    'type_coverage': {
        'actor': {'coverage': 1.0, 'covered': 3, 'total': 3},
        'usecase': {'coverage': 0.8, 'covered': 8, 'total': 10},
        'class': {'coverage': 0.857, 'covered': 6, 'total': 7}
    },
    'num_paths': 10
}
```

### Redundancy Detection

Two paths are considered redundant if their **Jaccard similarity** exceeds a threshold:

```
similarity = |path1 ∩ path2| / |path1 ∪ path2|
```

**Default threshold**: 0.8 (80% overlap)

### Usage
```python
from stage3_risk_guided_astar import PathAnalyzer

analyzer = PathAnalyzer(graph)

# Get coverage report
coverage = analyzer.analyze_coverage(test_paths)

# Find redundant paths
redundant_pairs = analyzer.find_redundant_paths(test_paths, threshold=0.8)

# Remove redundancy
filtered_paths = analyzer.remove_redundant_paths(test_paths, threshold=0.8)
```

---

## 🚀 4. Complete Pipeline

### TestPathGenerator Class

All-in-one class that combines all components:

```python
from stage3_risk_guided_astar import TestPathGenerator

# Initialize
path_gen = TestPathGenerator(unified_graph)

# Generate test paths (complete pipeline)
test_paths = path_gen.generate_test_paths(
    num_paths=10,
    max_path_length=20,
    remove_redundant=True,
    redundancy_threshold=0.8
)

# Print summary
path_gen.print_path_summary()

# Get coverage report
coverage = path_gen.get_coverage_report()

# Visualize paths
path_gen.visualize_path(0, output_path='top_risk_path.png')
```

### Output Example

```
======================================================================
STAGE 3: RISK-GUIDED TEST PATH GENERATION
======================================================================

[1/4] Predicting risk scores with GNN...
  ✓ Global risk score: 0.652
  ✓ Analyzed 25 nodes

[2/4] Initializing Risk-Guided A* algorithm...

[3/4] Generating 10 test paths...
  ✓ Generated 20 candidate paths

[4/4] Removing redundant paths (threshold=0.8)...
  ✓ Removed 8 redundant paths
  ✓ Kept 12 unique paths

======================================================================
GENERATION COMPLETE: 10 test paths ready
======================================================================

TEST PATH SUMMARY
======================================================================

Path 1:
  Length: 7 nodes
  Risk: 0.823 (high)
  Cost: 2.341
  Coverage: 35.0%
  Nodes: User → Login → ValidateCredentials → CheckPermissions → ...

Path 2:
  Length: 6 nodes
  Risk: 0.789 (high)
  Cost: 2.156
  Coverage: 30.0%
  Nodes: Admin → ManageUsers → DeleteUser → NotifySystem → ...
```

---

## 📈 5. Performance Metrics

### System Parameters (from PPT)

| Parameter | Description | Stage 3 Implementation |
|-----------|-------------|------------------------|
| Number of UML nodes | Graph size | `graph.number_of_nodes()` |
| Number of UML relationships | Graph edges | `graph.number_of_edges()` |
| Node risk score | GNN output | `risk_scores.get_node_risk(node)` |
| Path cost | A* algorithm | `test_path.path_cost` |
| Heuristic function value | Shortest path estimate | `nx.shortest_path_length()` |
| Coverage percentage | Node/edge coverage | `coverage_report['node_coverage']` |
| Test case complexity level | Path length | `len(test_path.nodes)` |
| Confidence score | Risk score | `test_path.risk_score` |
| Redundancy threshold | Similarity threshold | `0.8` (default) |
| Priority weight factor | Risk vs cost balance | `alpha=0.7, beta=0.3` |

### Complexity Analysis

| Operation | Complexity | Description |
|-----------|-----------|-------------|
| GNN Forward Pass | O(V + E) | Graph convolution |
| Risk Prediction | O(V) | For all nodes |
| A* Search (single path) | O(E × log(V)) | Priority queue operations |
| Path Generation | O(k × E × log(V)) | k = num_paths |
| Redundancy Detection | O(p²) | p = num_paths |
| **Total** | **O(V + E + k × E × log(V) + p²)** | Full pipeline |

For typical UML graphs:
- V = 20-50 nodes
- E = 30-100 edges
- k = 10-20 paths
- **Runtime**: < 5 seconds

---

## 💾 6. Export Format (for Stage 4)

### JSON Structure

```json
{
  "metadata": {
    "num_paths": 10,
    "total_nodes": 25,
    "total_edges": 35
  },
  "paths": [
    {
      "priority": 1,
      "risk_score": 0.823,
      "path_cost": 2.341,
      "coverage": 0.35,
      "length": 7,
      "nodes": [
        {"id": "N0", "name": "User", "type": "actor"},
        {"id": "N1", "name": "Login", "type": "usecase"},
        {"id": "N2", "name": "ValidateCredentials", "type": "usecase"}
      ],
      "edges": [
        {"source": "N0", "target": "N1", "source_name": "User", "target_name": "Login"},
        {"source": "N1", "target": "N2", "source_name": "Login", "target_name": "ValidateCredentials"}
      ]
    }
  ]
}
```

### Usage

```python
from stage3_risk_guided_astar import export_paths_for_llm

# Export for LLM
export_data = export_paths_for_llm(
    test_paths,
    graph,
    output_path='paths_for_llm.json'
)
```

---

## 🎯 7. Use Cases

### Use Case 1: Critical Path Testing
```python
# Generate paths prioritizing risk
test_paths = path_gen.generate_test_paths(
    num_paths=5,
    max_path_length=15,
    remove_redundant=True
)

# Filter critical paths (risk > 0.8)
critical_paths = [p for p in test_paths if p.risk_score > 0.8]
```

### Use Case 2: Full Coverage Testing
```python
# Generate many short paths for coverage
test_paths = path_gen.generate_test_paths(
    num_paths=50,
    max_path_length=8,
    remove_redundant=True
)

coverage = path_gen.get_coverage_report()
print(f"Coverage: {coverage['node_coverage']*100:.1f}%")
```

### Use Case 3: Balanced Risk-Cost
```python
# Adjust alpha/beta for balanced approach
astar = RiskGuidedAStar(graph, risk_scores, alpha=0.5, beta=0.5)
test_paths = astar.find_test_paths(num_paths=10)
```

---

## 🔧 8. Customization

### Custom Risk Predictor

```python
from stage3_risk_guided_astar import RiskPredictionGNN, RiskPredictor

# Train your own GNN
model = RiskPredictionGNN(input_dim=64, hidden_dim=256, dropout=0.2)
# ... train model ...

# Use custom predictor
predictor = RiskPredictor(model=model)
path_gen = TestPathGenerator(graph, risk_predictor=predictor)
```

### Custom Heuristic

```python
class CustomAStar(RiskGuidedAStar):
    def _heuristic(self, current, goal):
        # Custom heuristic based on node types
        if self.graph.nodes[current]['type'] == 'actor':
            return 0.5  # Lower cost for actors
        return 1.0
```

### Custom Path Filtering

```python
# Filter paths by specific criteria
def filter_paths(paths):
    return [
        p for p in paths
        if p.risk_score > 0.6  # High risk only
        and len(p.nodes) >= 5   # Minimum length
        and len(p.nodes) <= 15  # Maximum length
    ]

filtered = filter_paths(test_paths)
```

---

## 📚 9. API Reference

### Main Classes

#### `RiskPredictor`
```python
class RiskPredictor:
    def predict_risks(graph: nx.DiGraph) -> RiskScores
```

#### `RiskGuidedAStar`
```python
class RiskGuidedAStar:
    def __init__(graph, risk_scores, alpha=0.7, beta=0.3)
    def find_test_paths(start_nodes=None, num_paths=10, 
                       max_path_length=20) -> List[TestPath]
```

#### `PathAnalyzer`
```python
class PathAnalyzer:
    def analyze_coverage(paths: List[TestPath]) -> Dict
    def find_redundant_paths(paths, threshold=0.8) -> List[Tuple[int, int]]
    def remove_redundant_paths(paths, threshold=0.8) -> List[TestPath]
```

#### `TestPathGenerator`
```python
class TestPathGenerator:
    def __init__(graph, risk_predictor=None)
    def generate_test_paths(num_paths=10, max_path_length=20,
                           remove_redundant=True) -> List[TestPath]
    def get_coverage_report() -> Dict
    def print_path_summary()
    def visualize_path(path_index, output_path)
```

---

## 🎓 10. Examples

### Example 1: Basic Usage
```python
from stage3_risk_guided_astar import TestPathGenerator

# Simple usage
path_gen = TestPathGenerator(unified_graph)
test_paths = path_gen.generate_test_paths(num_paths=10)
path_gen.print_path_summary()
```

### Example 2: High-Risk Focus
```python
# Focus on high-risk components
astar = RiskGuidedAStar(graph, risk_scores, alpha=0.9, beta=0.1)
high_risk_paths = astar.find_test_paths(num_paths=5)
```

### Example 3: Batch Processing
```python
# Process multiple diagrams
all_paths = []
for graph in unified_graphs:
    path_gen = TestPathGenerator(graph)
    paths = path_gen.generate_test_paths(num_paths=5)
    all_paths.extend(paths)
```

---

## ✅ Summary

### What Stage 3 Provides:

1. ✅ **GNN-based risk prediction** for all UML nodes
2. ✅ **Risk-Guided A* algorithm** for optimal path finding
3. ✅ **Multiple test paths** with priority ranking
4. ✅ **Coverage analysis** by node type and overall
5. ✅ **Redundancy elimination** for efficient testing
6. ✅ **Visualization** of test paths with risk coloring
7. ✅ **JSON export** ready for Stage 4 (LLM)
8. ✅ **Comprehensive metrics** from your PPT requirements

### Key Innovation:

Unlike traditional test generation that treats all paths equally, Stage 3 uses **machine learning (GNN)** to predict risk and **intelligent search (A*)** to prioritize critical paths, resulting in more efficient and effective test coverage.

---

## 📞 Next Steps

### Ready for Stage 4: LLM Test Case Generation

The exported JSON contains:
- Test path structure (nodes, edges)
- Risk scores and priorities
- Node/edge metadata

Stage 4 will use this data to generate natural language test cases with:
- Preconditions
- Test steps
- Expected results
- Test data

🎉 **Stage 3 Complete!** 🎉
