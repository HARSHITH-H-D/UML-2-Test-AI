# STAGE 2: UNIFIED GRAPH CONSTRUCTION

## 🎯 Goal
Convert UML diagrams into a single unified directed graph for pattern recognition and analysis.

## 📋 Algorithm

### Unified Graph Construction
**Input:** Parsed UML elements  
**Output:** Unified Behavioral Graph G = (V, E)

```
1. Initialize directed graph G
2. For each class:
      add node in G
3. For each usecase:
      add node in G
4. For each activity:
      add node in G
5. For each relationship:
      include → add edge
      extend → add edge
      dependency → add edge
      control flow → add edge
6. Return graph G
```

**Graph Definition:**
- G = (V, E)
- V = UML elements (nodes)
- E = relationships (edges)

**Complexity:** O(V + E)
- Adding nodes: O(V)
- Adding edges: O(E)
- Total: O(V + E)

## 📦 Files Provided

### 1. **unified_graph_construction.py** - Core Implementation
Complete Python module implementing:

**Data Structures:**
- `NodeType`: Enum for node types (Actor, UseCase, Class, Activity)
- `EdgeType`: Enum for edge types (Include, Extend, Dependency, Control Flow, etc.)
- `UMLNode`: Node representation with attributes
- `UMLEdge`: Edge representation with type
- `UMLElements`: Container for parsed UML elements

**Main Class:**
- `UnifiedGraphBuilder`: Builds the unified graph
  - `build_unified_graph()`: Main algorithm implementation
  - `get_statistics()`: Graph analytics
  - `export_to_adjacency_list()`: Export as adjacency list
  - `export_to_json()`: Export as JSON
  - `visualize()`: Generate visualization

**Features:**
✅ O(V + E) complexity as specified  
✅ Directed graph structure  
✅ Multiple relationship types  
✅ Comprehensive statistics  
✅ Multiple export formats  
✅ Beautiful visualizations

### 2. **integration_pipeline.py** - Complete Pipeline
Integrates your existing parser with unified graph construction:

**Components:**
- Enhanced UML parser (from your notebook)
- Relationship type detection
- Unified graph construction
- PyTorch Geometric conversion

**Pipeline Flow:**
```
PlantUML Files → Parser → UMLElements → Unified Graph → PyG Data
```

**Features:**
✅ Batch processing of datasets  
✅ Single file processing  
✅ Automatic relationship classification  
✅ Edge direction correction  
✅ Statistics and analytics  
✅ Ready for GNN training

### 3. **stage2_unified_graph.ipynb** - Interactive Notebook
Step-by-step Jupyter notebook with:

**Contents:**
1. Algorithm explanation
2. Data structure definitions
3. Graph builder implementation
4. Example usage with sample data
5. Visualization
6. Statistics and analysis
7. Export demonstrations
8. Complexity verification

**Perfect for:**
- Learning the algorithm
- Testing with custom data
- Interactive exploration
- Google Colab execution

## 🚀 Quick Start

### Option 1: Using the Core Module

```python
from unified_graph_construction import UnifiedGraphBuilder, UMLElements

# Create UML elements
uml_elements = UMLElements(
    actors=[('A1', 'User')],
    usecases=[
        ('UC1', 'Login'),
        ('UC2', 'ValidateCredentials')
    ],
    classes=[('C1', 'AuthService')],
    includes=[('UC1', 'UC2')],
    dependencies=[('UC2', 'C1')],
    associations=[('A1', 'UC1')]
)

# Build unified graph
builder = UnifiedGraphBuilder()
graph = builder.build_unified_graph(uml_elements)

# Get statistics
stats = builder.get_statistics()
print(f"Nodes: {stats['total_nodes']}, Edges: {stats['total_edges']}")

# Visualize
builder.visualize(output_path='graph.png')
```

### Option 2: Using the Complete Pipeline

```python
from integration_pipeline import UMLToUnifiedGraph

# Process entire dataset
pipeline = UMLToUnifiedGraph()
graphs = pipeline.process_dataset("/path/to/uml_dataset")

# Get statistics
stats = pipeline.get_statistics()

# Process single file
graph, builder = pipeline.process_single_file("diagram.puml")
```

### Option 3: Using the Notebook

1. Open `stage2_unified_graph.ipynb` in Jupyter or Colab
2. Run cells sequentially
3. Modify example data as needed
4. Visualize and analyze results

## 📊 Graph Structure

### Node Types
- **Actor**: External entities (users, systems)
- **UseCase**: System functionality
- **Class**: System components
- **Activity**: Process steps

### Edge Types
- **Include**: UseCase includes another (mandatory)
- **Extend**: UseCase extends another (optional)
- **Dependency**: Component depends on another
- **Control Flow**: Sequential execution
- **Association**: General relationship
- **Invokes**: Actor initiates UseCase
- **Uses**: UseCase utilizes Class

## 🎨 Visualization

The unified graph is visualized with:
- Color-coded nodes by type
- Different edge colors by relationship type
- Spring layout for clarity
- Comprehensive legend
- High-resolution output

**Color Scheme:**
- 🔴 **Actors**: Red
- 🔵 **UseCases**: Cyan
- 🟢 **Classes**: Blue
- 🟠 **Activities**: Orange

## 📈 Statistics and Analysis

The builder provides comprehensive statistics:

```python
stats = builder.get_statistics()

# Available metrics:
stats['total_nodes']           # Total number of nodes
stats['total_edges']           # Total number of edges
stats['node_types']            # Distribution by node type
stats['edge_types']            # Distribution by edge type
stats['density']               # Graph density
stats['is_dag']                # Is it a DAG?
stats['strongly_connected_components']
stats['weakly_connected_components']
```

## 💾 Export Formats

### 1. Adjacency List
```
User → Login
Login → ValidateCredentials
ValidateCredentials → AuthService
```

### 2. JSON
```json
{
  "nodes": [
    {"id": "A1", "name": "User", "type": "actor"},
    {"id": "UC1", "name": "Login", "type": "usecase"}
  ],
  "edges": [
    {"source": "A1", "target": "UC1", "type": "invokes"}
  ]
}
```

### 3. NetworkX DiGraph
Native Python object for further analysis

### 4. PyTorch Geometric Data
Ready for GNN training

## 🔗 Integration with GNN

The unified graph can be directly converted for GNN training:

```python
from integration_pipeline import unified_graph_to_pyg

# Convert to PyTorch Geometric
pyg_data = unified_graph_to_pyg(unified_graph)

# Use in GNN model
from torch_geometric.data import DataLoader
loader = DataLoader([pyg_data], batch_size=1)
```

## 🧪 Example Use Cases

### 1. Pattern Analysis
```python
# Identify common patterns
for node in graph.nodes():
    in_degree = graph.in_degree(node)
    out_degree = graph.out_degree(node)
    if in_degree > 3 and out_degree > 3:
        print(f"Hub node: {graph.nodes[node]['name']}")
```

### 2. Path Finding
```python
import networkx as nx

# Find path from Actor to Class
if nx.has_path(graph, 'A1', 'C1'):
    path = nx.shortest_path(graph, 'A1', 'C1')
    print(f"Path: {' → '.join(path)}")
```

### 3. Subgraph Extraction
```python
# Extract UseCase subgraph
usecase_nodes = [n for n in graph.nodes() 
                 if graph.nodes[n]['node_type'] == 'usecase']
usecase_subgraph = graph.subgraph(usecase_nodes)
```

## 📝 Complete Workflow Example

```python
from integration_pipeline import UMLToUnifiedGraph
from torch_geometric.data import DataLoader

# Step 1: Parse and build graphs
pipeline = UMLToUnifiedGraph()
graphs = pipeline.process_dataset("/path/to/dataset")

# Step 2: Convert to PyG format
pyg_graphs = [unified_graph_to_pyg(g) for g in graphs]

# Step 3: Create data loader
loader = DataLoader(pyg_graphs, batch_size=8, shuffle=True)

# Step 4: Use in GNN training
for batch in loader:
    # Train your GNN model
    pass
```

## 🔍 Complexity Analysis

### Time Complexity: O(V + E)

**Node Addition:** O(V)
```python
# For each node type
for node_id, name in elements.actors:      # O(|actors|)
    add_node(node_id, name, NodeType.ACTOR)
for node_id, name in elements.usecases:    # O(|usecases|)
    add_node(node_id, name, NodeType.USECASE)
# ... etc
# Total: O(V) where V = sum of all node types
```

**Edge Addition:** O(E)
```python
# For each edge type
for src, tgt in elements.includes:         # O(|includes|)
    add_edge(src, tgt, EdgeType.INCLUDE)
# ... etc
# Total: O(E) where E = sum of all edge types
```

**Total: O(V + E)**

### Space Complexity: O(V + E)

**Node Storage:** O(V)
```python
self.graph.nodes()  # Stores V nodes
self.nodes = {}     # Additional node metadata
```

**Edge Storage:** O(E)
```python
self.graph.edges()  # Stores E edges
```

**Total: O(V + E)**

## 🎓 Algorithm Properties

### Correctness
✅ All nodes from UML elements are added  
✅ All relationships are preserved as edges  
✅ Edge directions follow semantic rules  
✅ Node and edge types are maintained  

### Efficiency
✅ Linear time complexity O(V + E)  
✅ Linear space complexity O(V + E)  
✅ Optimal for graph construction  
✅ No redundant operations  

### Completeness
✅ Handles all UML element types  
✅ Supports all relationship types  
✅ Preserves all structural information  
✅ Enables downstream analysis  

## 🔧 Advanced Features

### 1. Custom Node Attributes
```python
builder._add_node(
    'UC1', 
    'Login',
    NodeType.USECASE,
    attributes={'priority': 'high', 'complexity': 5}
)
```

### 2. Custom Edge Attributes
```python
builder._add_edge(
    'UC1', 
    'UC2',
    EdgeType.INCLUDE,
    attributes={'optional': False, 'weight': 1.0}
)
```

### 3. Graph Analysis
```python
# Centrality measures
centrality = nx.betweenness_centrality(graph)

# Community detection
communities = nx.community.greedy_modularity_communities(graph)

# Cycles detection
cycles = list(nx.simple_cycles(graph))
```

## 🐛 Troubleshooting

### Issue: Nodes not appearing
**Solution:** Check that node IDs are unique and relationships reference existing nodes

### Issue: Edges pointing wrong direction
**Solution:** Verify edge type inference logic in `_infer_edge_type()`

### Issue: Graph not visualizing
**Solution:** Install matplotlib: `pip install matplotlib networkx`

## 📚 References

### Graph Theory
- Cormen et al., "Introduction to Algorithms" - Graph Algorithms Chapter
- NetworkX Documentation: https://networkx.org/

### UML
- UML 2.5 Specification
- PlantUML Documentation: https://plantuml.com/

### Related Work
- Graph Neural Networks: Kipf & Welling (2017)
- UML Pattern Recognition: Various research papers

## 🎉 Summary

This implementation provides:

✅ **Complete Stage 2 Algorithm** - Exactly as specified  
✅ **O(V + E) Complexity** - Optimal performance  
✅ **Multiple Use Cases** - Pattern recognition, analysis, GNN training  
✅ **Production Ready** - Clean, documented, tested  
✅ **Easy Integration** - Works with your existing parser  
✅ **Extensible** - Add custom node/edge types easily  

Ready to build unified graphs from your UML diagrams! 🚀
