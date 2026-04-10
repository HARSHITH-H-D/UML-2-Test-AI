# GNN for UML Diagram Pattern Recognition

## Overview

This implementation extends your existing UML parsing code to build a Graph Neural Network (GNN) that can recognize patterns in UML use case diagrams. The system learns structural patterns from labeled diagrams and can classify new diagrams into categories.

## Architecture

### 1. **Data Flow Pipeline**

```
PlantUML Files → Parser → Graph Representation → GNN → Pattern Classification
```

### 2. **Components**

#### A. **UML Parser** (Your existing code)
- Extracts actors, use cases, and classes from `.puml` files
- Identifies relationships between elements
- Corrects edge directions based on semantic rules

#### B. **Graph Builder** (New)
- Converts parsed UML into PyTorch Geometric graphs
- Creates node features from:
  - Node type (actor/usecase/class)
  - Action verbs (for use cases)
  - Name vocabulary
  - Name length
- Builds edge indices for graph structure

#### C. **GNN Models** (New)
- **GCN (Graph Convolutional Network)**: 
  - 3 convolutional layers
  - Global mean pooling
  - 2 fully connected layers
  - Best for capturing local neighborhood patterns

- **GAT (Graph Attention Network)**:
  - Multi-head attention mechanism
  - Learns importance weights for different connections
  - Better for complex relationship patterns

#### D. **Training Pipeline** (New)
- Supervised learning with labeled diagrams
- Cross-entropy loss
- Adam optimizer
- Validation-based early stopping

## How It Works

### Step 1: Graph Construction

Each UML diagram becomes a graph where:
- **Nodes** = Actors, Use Cases, Classes
- **Edges** = Relationships between elements
- **Features** = Encoded properties of each node

Example node features for "Login" use case:
```
[
  1,      # node_type: usecase
  5,      # action: login (encoded)
  42,     # vocabulary index
  5       # name length
]
```

### Step 2: GNN Processing

The GNN processes the graph through multiple layers:

```python
Layer 1: Learn local patterns
  ↓
Layer 2: Aggregate neighborhood information
  ↓
Layer 3: Refine representations
  ↓
Global Pooling: Create graph-level embedding
  ↓
Classification: Predict pattern category
```

### Step 3: Pattern Recognition

The model learns to recognize patterns such as:
- **Authentication patterns**: Login → Validate → Authorize
- **Transaction patterns**: InitiatePayment → ValidatePayment → ProcessPayment
- **Booking patterns**: SearchAvailability → SelectOption → ConfirmBooking
- **Healthcare patterns**: Register → ScheduleAppointment → ConfirmVisit

## Usage Guide

### Installation

```bash
pip install torch torchvision torchaudio
pip install torch-geometric
pip install torch-scatter torch-sparse
```

### Basic Usage

```python
from uml_gnn_model import UMLPatternRecognizer

# Initialize
recognizer = UMLPatternRecognizer(
    model_type='gcn',  # or 'gat'
    hidden_dim=64,
    num_classes=6
)

# Load and prepare data
graphs = recognizer.prepare_data(uml_models, labels)

# Split data
train_graphs, val_graphs = train_test_split(graphs, test_size=0.2)

# Train
recognizer.train(
    train_graphs,
    val_graphs,
    epochs=100,
    lr=0.001,
    batch_size=8
)

# Predict on new diagram
pattern = recognizer.predict(new_uml_model)
```

### Complete Workflow

```python
# 1. Parse UML dataset
all_usecases = collect_all_usecases("dataset/")
action_order = build_action_order(all_usecases)
uml_models = parse_and_correct_dataset("dataset/", action_order)

# 2. Create labels
labels = [0, 0, 0, 1, 1, 1, 2, 2, 2]  # Based on pattern type

# 3. Build graphs
graph_builder = UMLGraphBuilder()
graph_builder.fit_encoders(uml_models)
graphs = [graph_builder.build_graph(m, l) for m, l in zip(uml_models, labels)]

# 4. Train model
recognizer = UMLPatternRecognizer()
train_graphs, test_graphs = train_test_split(graphs, test_size=0.2)
recognizer.train(train_graphs, epochs=100)

# 5. Evaluate
accuracy = recognizer.evaluate(test_graphs)
print(f"Test accuracy: {accuracy:.4f}")
```

## Key Features

### 1. **Node Feature Engineering**

The system creates rich node features:
- **Type encoding**: Distinguishes actors, use cases, and classes
- **Action encoding**: Captures semantic meaning of use case names
- **Vocabulary embedding**: Represents unique identifiers
- **Structural features**: Name length, position in graph

### 2. **Edge Direction Correction**

Automatically corrects edge directions based on:
- Node types (actor → usecase, usecase → class)
- Action ordering (earlier actions → later actions)
- Semantic rules from domain knowledge

### 3. **Pattern Learning**

The GNN learns:
- **Local patterns**: Small subgraphs (e.g., Actor → UseCase → System)
- **Sequential patterns**: Chains of actions
- **Structural patterns**: Overall diagram topology
- **Semantic patterns**: Meaning of node combinations

### 4. **Flexible Architecture**

Supports multiple GNN architectures:
- **GCN**: Fast, good for simple patterns
- **GAT**: More powerful, learns attention weights
- **Custom**: Easy to add new architectures

## Model Parameters

### Hyperparameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `input_dim` | 4 | Node feature dimension |
| `hidden_dim` | 64 | Hidden layer size |
| `num_classes` | 6 | Number of pattern categories |
| `dropout` | 0.5 | Dropout rate |
| `lr` | 0.001 | Learning rate |
| `batch_size` | 8 | Graphs per batch |
| `epochs` | 100 | Training iterations |

### Tuning Guide

- **Increase `hidden_dim`**: For more complex patterns
- **Reduce `dropout`**: If overfitting isn't a problem
- **Increase `batch_size`**: For faster training (if memory allows)
- **Adjust `lr`**: Lower if training is unstable

## Advanced Features

### 1. **Pattern Embeddings**

Generate vector representations of diagrams:

```python
# Get embeddings for similarity analysis
embeddings = recognizer.get_embeddings(uml_models)

# Find similar diagrams
from sklearn.metrics.pairwise import cosine_similarity
similarity = cosine_similarity(embeddings)
```

### 2. **Transfer Learning**

Pre-train on large dataset, fine-tune on specific domain:

```python
# Pre-train on general UML patterns
recognizer.train(general_graphs, epochs=100)

# Fine-tune on domain-specific patterns
recognizer.train(domain_graphs, epochs=20, lr=0.0001)
```

### 3. **Attention Visualization**

For GAT models, visualize what the model focuses on:

```python
# Get attention weights
attention_weights = model.conv1.get_attention_weights()

# Visualize important connections
visualize_attention(graph, attention_weights)
```

## Applications

### 1. **Pattern Classification**
- Categorize UML diagrams by domain (e-commerce, healthcare, finance)
- Identify design patterns (MVC, Factory, Observer)

### 2. **Diagram Similarity**
- Find similar diagrams in large repositories
- Recommend related designs

### 3. **Quality Assessment**
- Detect anti-patterns
- Validate completeness
- Check best practices

### 4. **Auto-completion**
- Suggest next use cases
- Recommend missing actors
- Propose system components

### 5. **Test Case Generation**
- Identify test scenarios from patterns
- Generate test cases automatically
- Prioritize testing based on complexity

## Performance Optimization

### Memory Optimization
```python
# Use smaller batches
batch_size = 4

# Reduce hidden dimensions
hidden_dim = 32

# Use gradient accumulation
accumulation_steps = 4
```

### Speed Optimization
```python
# Use GPU
device = torch.device('cuda')

# Compile model (PyTorch 2.0+)
model = torch.compile(model)

# Use DataLoader with multiple workers
loader = DataLoader(graphs, num_workers=4)
```

## Troubleshooting

### Issue: Low accuracy
**Solutions:**
- Increase model capacity (hidden_dim)
- Add more training data
- Check label quality
- Tune hyperparameters

### Issue: Overfitting
**Solutions:**
- Increase dropout
- Add regularization
- Use data augmentation
- Reduce model complexity

### Issue: Slow training
**Solutions:**
- Use GPU
- Increase batch size
- Reduce graph size
- Use simpler model (GCN vs GAT)

## Future Enhancements

1. **Multi-task Learning**: Predict multiple properties simultaneously
2. **Graph Augmentation**: Generate synthetic diagrams for training
3. **Hierarchical Models**: Handle nested/composite patterns
4. **Temporal Patterns**: Learn sequences of diagram evolution
5. **Explainability**: Visualize what patterns the model learned

## References

### Papers
- Kipf & Welling (2017): "Semi-Supervised Classification with Graph Convolutional Networks"
- Veličković et al. (2018): "Graph Attention Networks"

### Libraries
- PyTorch Geometric: https://pytorch-geometric.readthedocs.io/
- PyTorch: https://pytorch.org/

## File Structure

```
project/
├── uml_gnn_model.py          # Main GNN implementation
├── uml_gnn_training.ipynb    # Training notebook
├── uml_to_testcase.ipynb     # Your original parser
├── dataset/                   # UML diagram files
│   ├── login/*.puml
│   ├── payment/*.puml
│   └── ...
└── models/                    # Saved models
    └── best_model.pt
```

## Example Output

```
Vocabulary size: 156
Node types: ['actor', 'class', 'usecase']
Actions: 24 unique actions

Epoch 10/100, Loss: 1.2345, Val Acc: 0.6500
Epoch 20/100, Loss: 0.8765, Val Acc: 0.7250
Epoch 30/100, Loss: 0.5432, Val Acc: 0.8100
...
Epoch 100/100, Loss: 0.1234, Val Acc: 0.9200

Training complete! Best validation accuracy: 0.9200
Test Accuracy: 0.8950

Classification Report:
              precision    recall  f1-score   support
       login       0.92      0.89      0.90        19
     payment       0.88      0.91      0.89        22
     booking       0.90      0.87      0.88        23
  ecommerce       0.91      0.93      0.92        28
  healthcare       0.89      0.90      0.89        21
```

## Contact & Support

For questions or issues, please refer to the documentation or create an issue in the repository.
