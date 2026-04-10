"""
Example: Complete workflow for training GNN on UML diagrams
This script demonstrates the end-to-end process
"""

import os
import sys
from sklearn.model_selection import train_test_split

# Import the GNN model components
from uml_gnn_model import (
    # Parsing functions
    parse_plantuml_raw,
    extract_action,
    build_action_order,
    collect_all_usecases,
    parse_and_correct_dataset,
    # GNN components
    UMLGraphBuilder,
    UMLPatternRecognizer,
    GCN_UML_Classifier,
    GAT_UML_Classifier
)


def main():
    """Example workflow for UML pattern recognition"""
    
    print("="*70)
    print("UML DIAGRAM PATTERN RECOGNITION WITH GNN")
    print("="*70)
    
    # ========================================================================
    # STEP 1: CONFIGURE PATHS
    # ========================================================================
    print("\n[STEP 1] Configuration")
    print("-" * 70)
    
    # Set your dataset path
    DATASET_PATH = "/path/to/your/uml_dataset"
    
    # Check if path exists
    if not os.path.exists(DATASET_PATH):
        print(f"ERROR: Dataset path not found: {DATASET_PATH}")
        print("Please update DATASET_PATH in the script")
        return
    
    print(f"Dataset path: {DATASET_PATH}")
    
    # ========================================================================
    # STEP 2: PARSE UML DATASET
    # ========================================================================
    print("\n[STEP 2] Parsing UML Dataset")
    print("-" * 70)
    
    print("Collecting use cases...")
    all_usecases = collect_all_usecases(DATASET_PATH)
    print(f"Found {len(all_usecases)} use cases")
    
    print("\nBuilding action order...")
    action_order = build_action_order(all_usecases)
    print(f"Learned {len(action_order)} unique actions:")
    print(f"  Top 10: {action_order[:10]}")
    
    print("\nParsing and correcting UML models...")
    corrected_models = parse_and_correct_dataset(DATASET_PATH, action_order)
    print(f"Processed {len(corrected_models)} UML models")
    
    # ========================================================================
    # STEP 3: CREATE LABELS
    # ========================================================================
    print("\n[STEP 3] Creating Labels")
    print("-" * 70)
    
    # Strategy 1: Labels from directory structure
    labels = []
    pattern_types = []
    
    for root, _, files in os.walk(DATASET_PATH):
        for file in files:
            if file.endswith(".puml"):
                # Get pattern type from directory name
                pattern = os.path.basename(root)
                pattern_types.append(pattern)
    
    # Encode pattern types as numeric labels
    from sklearn.preprocessing import LabelEncoder
    label_encoder = LabelEncoder()
    labels = label_encoder.fit_transform(pattern_types)
    
    print(f"Pattern categories: {list(label_encoder.classes_)}")
    print(f"Label distribution:")
    for i, pattern in enumerate(label_encoder.classes_):
        count = (labels == i).sum()
        print(f"  {pattern}: {count} samples")
    
    # ========================================================================
    # STEP 4: BUILD GRAPHS
    # ========================================================================
    print("\n[STEP 4] Building Graphs")
    print("-" * 70)
    
    # Initialize graph builder
    graph_builder = UMLGraphBuilder()
    
    # Fit encoders on all models
    print("Fitting encoders...")
    graph_builder.fit_encoders(corrected_models)
    
    # Build PyTorch Geometric graphs
    print("Converting UML models to graphs...")
    graphs = []
    for i, model in enumerate(corrected_models):
        graph = graph_builder.build_graph(model, labels[i])
        graphs.append(graph)
    
    print(f"Created {len(graphs)} graphs")
    print(f"Example graph structure:")
    print(f"  Nodes: {graphs[0].num_nodes}")
    print(f"  Edges: {graphs[0].edge_index.shape[1]}")
    print(f"  Features: {graphs[0].x.shape}")
    
    # ========================================================================
    # STEP 5: SPLIT DATA
    # ========================================================================
    print("\n[STEP 5] Splitting Data")
    print("-" * 70)
    
    # Split into train, validation, and test
    train_graphs, test_graphs = train_test_split(
        graphs, 
        test_size=0.2, 
        random_state=42,
        stratify=labels
    )
    
    train_graphs, val_graphs = train_test_split(
        train_graphs,
        test_size=0.2,
        random_state=42
    )
    
    print(f"Train set: {len(train_graphs)} graphs")
    print(f"Validation set: {len(val_graphs)} graphs")
    print(f"Test set: {len(test_graphs)} graphs")
    
    # ========================================================================
    # STEP 6: TRAIN MODEL
    # ========================================================================
    print("\n[STEP 6] Training Model")
    print("-" * 70)
    
    # Initialize recognizer
    recognizer = UMLPatternRecognizer(
        model_type='gcn',  # Use 'gat' for Graph Attention Network
        hidden_dim=64,
        num_classes=len(label_encoder.classes_)
    )
    
    print("Model configuration:")
    print(f"  Architecture: GCN")
    print(f"  Hidden dimension: 64")
    print(f"  Number of classes: {len(label_encoder.classes_)}")
    
    print("\nStarting training...")
    train_losses, val_accuracies = recognizer.train(
        train_graphs,
        val_graphs,
        epochs=100,
        lr=0.001,
        batch_size=8
    )
    
    # ========================================================================
    # STEP 7: EVALUATE MODEL
    # ========================================================================
    print("\n[STEP 7] Evaluating Model")
    print("-" * 70)
    
    from torch_geometric.data import DataLoader
    test_loader = DataLoader(test_graphs, batch_size=8)
    
    test_accuracy = recognizer.evaluate(test_loader)
    print(f"Test Accuracy: {test_accuracy:.4f}")
    
    # ========================================================================
    # STEP 8: PREDICT ON NEW DIAGRAM
    # ========================================================================
    print("\n[STEP 8] Testing Prediction")
    print("-" * 70)
    
    # Take a test example
    test_example = corrected_models[0]
    prediction = recognizer.predict(test_example)
    predicted_pattern = label_encoder.inverse_transform([prediction])[0]
    
    print(f"Example prediction:")
    print(f"  Model: {corrected_models[0]['usecases'][0] if corrected_models[0]['usecases'] else 'N/A'}")
    print(f"  Predicted pattern: {predicted_pattern}")
    
    # ========================================================================
    # STEP 9: GENERATE EMBEDDINGS
    # ========================================================================
    print("\n[STEP 9] Generating Pattern Embeddings")
    print("-" * 70)
    
    print("Generating embeddings for similarity analysis...")
    embeddings = recognizer.get_embeddings(corrected_models[:10])
    print(f"Embedding shape: {embeddings.shape}")
    
    # Calculate similarity between first two diagrams
    from sklearn.metrics.pairwise import cosine_similarity
    similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    print(f"Similarity between diagram 0 and 1: {similarity:.4f}")
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("\n" + "="*70)
    print("TRAINING COMPLETE - SUMMARY")
    print("="*70)
    print(f"Dataset: {len(corrected_models)} UML models")
    print(f"Patterns: {len(label_encoder.classes_)} categories")
    print(f"Best validation accuracy: {max(val_accuracies):.4f}")
    print(f"Test accuracy: {test_accuracy:.4f}")
    print(f"Model saved: best_uml_gnn_model.pt")
    print("="*70)


def demo_with_synthetic_data():
    """
    Demo with synthetic data (when real dataset is not available)
    """
    print("\n" + "="*70)
    print("DEMO MODE - Using Synthetic Data")
    print("="*70)
    
    import torch
    from torch_geometric.data import Data
    
    # Create synthetic graphs
    num_graphs = 30
    num_classes = 3
    
    graphs = []
    labels = []
    
    for i in range(num_graphs):
        # Random graph structure
        num_nodes = torch.randint(5, 15, (1,)).item()
        num_edges = torch.randint(num_nodes, num_nodes * 2, (1,)).item()
        
        # Random features
        x = torch.randn(num_nodes, 4)
        
        # Random edges
        edge_index = torch.randint(0, num_nodes, (2, num_edges))
        
        # Assign label
        label = i % num_classes
        
        data = Data(x=x, edge_index=edge_index, y=torch.tensor([label]))
        graphs.append(data)
        labels.append(label)
    
    print(f"Created {len(graphs)} synthetic graphs with {num_classes} classes")
    
    # Train on synthetic data
    recognizer = UMLPatternRecognizer(
        model_type='gcn',
        hidden_dim=32,
        num_classes=num_classes
    )
    
    train_graphs = graphs[:24]
    val_graphs = graphs[24:]
    
    print("\nTraining on synthetic data...")
    recognizer.train(train_graphs, val_graphs, epochs=50, lr=0.01, batch_size=4)
    
    from torch_geometric.data import DataLoader
    val_loader = DataLoader(val_graphs, batch_size=4)
    val_acc = recognizer.evaluate(val_loader)
    
    print(f"\nValidation accuracy on synthetic data: {val_acc:.4f}")
    print("Demo complete!")


if __name__ == "__main__":
    # Choose mode
    mode = "demo"  # Change to "real" when you have real data
    
    if mode == "real":
        # Run with real UML dataset
        main()
    else:
        # Run demo with synthetic data
        demo_with_synthetic_data()
