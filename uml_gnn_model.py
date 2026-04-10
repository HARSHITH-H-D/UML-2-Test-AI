"""
GNN Model for UML Diagram Pattern Recognition
This extends the existing UML parser to build a Graph Neural Network
for learning and recognizing patterns in UML use case diagrams.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GCNConv, GATConv, GraphSAGE, global_mean_pool
from torch_geometric.data import Data, DataLoader
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import os
import re
from collections import Counter

# ============================================================================
# PART 1: UML PARSING (From your existing code)
# ============================================================================

def parse_plantuml_raw(puml_path):
    """Parse PlantUML file and extract nodes and edges"""
    nodes = {}
    edges = []

    actor_pat   = re.compile(r'actor\s+"?(.+?)"?(\s+as\s+(\w+))?', re.I)
    usecase_pat = re.compile(r'usecase\s+"?(.+?)"?(\s+as\s+(\w+))?', re.I)
    class_pat   = re.compile(r'class\s+"?(.+?)"?(\s+as\s+(\w+))?', re.I)
    edge_pat    = re.compile(r'(.+?)\s*[-.]+[<>]*\s*(.+)')

    with open(puml_path, "r") as f:
        for line in f:
            line = line.strip()

            if not line or line.startswith("@"):
                continue

            m = actor_pat.match(line)
            if m:
                nodes[m.group(3) or m.group(1)] = "actor"
                continue

            m = usecase_pat.match(line)
            if m:
                nodes[m.group(3) or m.group(1)] = "usecase"
                continue

            m = class_pat.match(line)
            if m:
                nodes[m.group(3) or m.group(1)] = "class"
                continue

            m = edge_pat.match(line)
            if m:
                src = m.group(1).strip().strip('"')
                tgt = m.group(2).strip().strip('"')
                edges.append((src, tgt))
                nodes.setdefault(src, "usecase")
                nodes.setdefault(tgt, "usecase")

    return nodes, edges


def extract_action(name):
    """Extract action verb from use case name"""
    name = name.lower()
    tokens = re.findall(r"[a-z]+", name)
    if not tokens:
        return None

    action = tokens[0]

    if len(action) < 4:
        return None
    if action.endswith(("service", "system")):
        return None
    if action in ("user", "customer", "patient", "admin", "manager"):
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


def collect_all_usecases(dataset_root):
    """Collect all use cases from dataset"""
    all_usecases = []

    for root, _, files in os.walk(dataset_root):
        for file in files:
            if file.endswith(".puml"):
                nodes, _ = parse_plantuml_raw(os.path.join(root, file))
                for name, t in nodes.items():
                    if t == "usecase":
                        all_usecases.append(name)

    return all_usecases


# ============================================================================
# PART 2: GRAPH CONSTRUCTION FOR GNN
# ============================================================================

class UMLGraphBuilder:
    """Builds PyTorch Geometric graphs from UML diagrams"""
    
    def __init__(self):
        self.node_type_encoder = LabelEncoder()
        self.action_encoder = LabelEncoder()
        self.vocabulary = {}
        self.vocab_size = 0
        
    def fit_encoders(self, all_models):
        """Fit label encoders on all models"""
        all_types = []
        all_actions = []
        all_names = []
        
        for model in all_models:
            # Collect node types
            for node_list in [model['actors'], model['usecases'], model['classes']]:
                for _, name in node_list:
                    all_names.append(name)
                    
            all_types.extend(['actor'] * len(model['actors']))
            all_types.extend(['usecase'] * len(model['usecases']))
            all_types.extend(['class'] * len(model['classes']))
            
            # Collect actions from use cases
            for _, name in model['usecases']:
                action = extract_action(name)
                if action:
                    all_actions.append(action)
        
        # Fit encoders
        self.node_type_encoder.fit(all_types)
        if all_actions:
            self.action_encoder.fit(all_actions)
        
        # Build vocabulary for node names
        unique_names = list(set(all_names))
        self.vocabulary = {name: idx for idx, name in enumerate(unique_names)}
        self.vocab_size = len(unique_names)
        
    def create_node_features(self, model):
        """Create feature vectors for each node"""
        features = []
        node_to_idx = {}
        idx = 0
        
        # Process all nodes
        for node_type, node_list_key in [('actor', 'actors'), 
                                          ('usecase', 'usecases'), 
                                          ('class', 'classes')]:
            for node_id, name in model[node_list_key]:
                node_to_idx[node_id] = idx
                
                # Feature vector: [node_type_encoding, action_encoding, name_vocab_idx]
                type_enc = self.node_type_encoder.transform([node_type])[0]
                
                # Action encoding (for use cases)
                action = extract_action(name) if node_type == 'usecase' else None
                action_enc = self.action_encoder.transform([action])[0] if action else -1
                
                # Name vocabulary index
                name_idx = self.vocabulary.get(name, -1)
                
                # Create feature vector
                feature = [type_enc, action_enc, name_idx, len(name)]
                features.append(feature)
                
                idx += 1
                
        return torch.tensor(features, dtype=torch.float), node_to_idx
    
    def create_edge_index(self, model, node_to_idx):
        """Create edge index for PyG"""
        edges = []
        
        for src_id, tgt_id in model['relations']:
            if src_id in node_to_idx and tgt_id in node_to_idx:
                src_idx = node_to_idx[src_id]
                tgt_idx = node_to_idx[tgt_id]
                edges.append([src_idx, tgt_idx])
        
        if edges:
            return torch.tensor(edges, dtype=torch.long).t().contiguous()
        else:
            # Empty graph case
            return torch.zeros((2, 0), dtype=torch.long)
    
    def build_graph(self, model, label=None):
        """Build a PyTorch Geometric graph from UML model"""
        node_features, node_to_idx = self.create_node_features(model)
        edge_index = self.create_edge_index(model, node_to_idx)
        
        data = Data(
            x=node_features,
            edge_index=edge_index,
            num_nodes=len(node_to_idx)
        )
        
        if label is not None:
            data.y = torch.tensor([label], dtype=torch.long)
        
        return data


# ============================================================================
# PART 3: GNN ARCHITECTURES
# ============================================================================

class GCN_UML_Classifier(nn.Module):
    """Graph Convolutional Network for UML pattern classification"""
    
    def __init__(self, input_dim, hidden_dim=64, num_classes=6, dropout=0.5):
        super(GCN_UML_Classifier, self).__init__()
        
        self.conv1 = GCNConv(input_dim, hidden_dim)
        self.conv2 = GCNConv(hidden_dim, hidden_dim)
        self.conv3 = GCNConv(hidden_dim, hidden_dim)
        
        self.fc1 = nn.Linear(hidden_dim, hidden_dim // 2)
        self.fc2 = nn.Linear(hidden_dim // 2, num_classes)
        
        self.dropout = dropout
        
    def forward(self, data):
        x, edge_index, batch = data.x, data.edge_index, data.batch
        
        # Graph convolution layers
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)
        
        x = self.conv2(x, edge_index)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)
        
        x = self.conv3(x, edge_index)
        x = F.relu(x)
        
        # Global pooling
        x = global_mean_pool(x, batch)
        
        # Classification layers
        x = self.fc1(x)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)
        
        x = self.fc2(x)
        
        return F.log_softmax(x, dim=1)


class GAT_UML_Classifier(nn.Module):
    """Graph Attention Network for UML pattern classification"""
    
    def __init__(self, input_dim, hidden_dim=64, num_classes=6, heads=4, dropout=0.5):
        super(GAT_UML_Classifier, self).__init__()
        
        self.conv1 = GATConv(input_dim, hidden_dim, heads=heads, dropout=dropout)
        self.conv2 = GATConv(hidden_dim * heads, hidden_dim, heads=1, dropout=dropout)
        
        self.fc1 = nn.Linear(hidden_dim, hidden_dim // 2)
        self.fc2 = nn.Linear(hidden_dim // 2, num_classes)
        
        self.dropout = dropout
        
    def forward(self, data):
        x, edge_index, batch = data.x, data.edge_index, data.batch
        
        # Graph attention layers
        x = self.conv1(x, edge_index)
        x = F.elu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)
        
        x = self.conv2(x, edge_index)
        x = F.elu(x)
        
        # Global pooling
        x = global_mean_pool(x, batch)
        
        # Classification layers
        x = self.fc1(x)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)
        
        x = self.fc2(x)
        
        return F.log_softmax(x, dim=1)


class UMLPatternEmbedding(nn.Module):
    """Generate embeddings for UML patterns (unsupervised learning)"""
    
    def __init__(self, input_dim, hidden_dim=64, embedding_dim=32):
        super(UMLPatternEmbedding, self).__init__()
        
        self.conv1 = GCNConv(input_dim, hidden_dim)
        self.conv2 = GCNConv(hidden_dim, hidden_dim)
        self.conv3 = GCNConv(hidden_dim, embedding_dim)
        
    def forward(self, data):
        x, edge_index, batch = data.x, data.edge_index, data.batch
        
        x = F.relu(self.conv1(x, edge_index))
        x = F.relu(self.conv2(x, edge_index))
        x = self.conv3(x, edge_index)
        
        # Global pooling to get graph-level embedding
        x = global_mean_pool(x, batch)
        
        return x


# ============================================================================
# PART 4: TRAINING AND EVALUATION
# ============================================================================

class UMLPatternRecognizer:
    """Complete pipeline for UML pattern recognition"""
    
    def __init__(self, model_type='gcn', hidden_dim=64, num_classes=6):
        self.graph_builder = UMLGraphBuilder()
        self.model_type = model_type
        self.hidden_dim = hidden_dim
        self.num_classes = num_classes
        self.model = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
    def prepare_data(self, uml_models, labels=None):
        """Prepare PyG graphs from UML models"""
        # Fit encoders
        self.graph_builder.fit_encoders(uml_models)
        
        # Build graphs
        graphs = []
        for i, model in enumerate(uml_models):
            label = labels[i] if labels is not None else None
            graph = self.graph_builder.build_graph(model, label)
            graphs.append(graph)
        
        return graphs
    
    def create_model(self, input_dim):
        """Create the GNN model"""
        if self.model_type == 'gcn':
            model = GCN_UML_Classifier(
                input_dim=input_dim,
                hidden_dim=self.hidden_dim,
                num_classes=self.num_classes
            )
        elif self.model_type == 'gat':
            model = GAT_UML_Classifier(
                input_dim=input_dim,
                hidden_dim=self.hidden_dim,
                num_classes=self.num_classes
            )
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
        
        return model.to(self.device)
    
    def train(self, train_graphs, val_graphs=None, epochs=100, lr=0.001, batch_size=32):
        """Train the GNN model"""
        # Create data loaders
        train_loader = DataLoader(train_graphs, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_graphs, batch_size=batch_size) if val_graphs else None
        
        # Initialize model
        input_dim = train_graphs[0].x.shape[1]
        self.model = self.create_model(input_dim)
        
        # Optimizer and loss
        optimizer = torch.optim.Adam(self.model.parameters(), lr=lr, weight_decay=5e-4)
        criterion = nn.NLLLoss()
        
        # Training loop
        train_losses = []
        val_accuracies = []
        
        for epoch in range(epochs):
            # Training
            self.model.train()
            total_loss = 0
            
            for batch in train_loader:
                batch = batch.to(self.device)
                optimizer.zero_grad()
                
                out = self.model(batch)
                loss = criterion(out, batch.y)
                
                loss.backward()
                optimizer.step()
                
                total_loss += loss.item()
            
            avg_loss = total_loss / len(train_loader)
            train_losses.append(avg_loss)
            
            # Validation
            if val_loader:
                val_acc = self.evaluate(val_loader)
                val_accuracies.append(val_acc)
                
                if (epoch + 1) % 10 == 0:
                    print(f'Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}, Val Acc: {val_acc:.4f}')
            else:
                if (epoch + 1) % 10 == 0:
                    print(f'Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}')
        
        return train_losses, val_accuracies
    
    def evaluate(self, data_loader):
        """Evaluate model accuracy"""
        self.model.eval()
        correct = 0
        total = 0
        
        with torch.no_grad():
            for batch in data_loader:
                batch = batch.to(self.device)
                out = self.model(batch)
                pred = out.argmax(dim=1)
                
                correct += (pred == batch.y).sum().item()
                total += batch.y.size(0)
        
        return correct / total if total > 0 else 0
    
    def predict(self, uml_model):
        """Predict pattern for a single UML model"""
        self.model.eval()
        
        graph = self.graph_builder.build_graph(uml_model)
        graph = graph.to(self.device)
        
        with torch.no_grad():
            # Add batch dimension
            graph.batch = torch.zeros(graph.num_nodes, dtype=torch.long, device=self.device)
            out = self.model(graph)
            pred = out.argmax(dim=1)
        
        return pred.item()
    
    def get_embeddings(self, uml_models):
        """Get graph embeddings for UML models"""
        embedding_model = UMLPatternEmbedding(
            input_dim=4,  # Based on our feature construction
            hidden_dim=self.hidden_dim,
            embedding_dim=32
        ).to(self.device)
        
        graphs = self.prepare_data(uml_models)
        embeddings = []
        
        embedding_model.eval()
        with torch.no_grad():
            for graph in graphs:
                graph = graph.to(self.device)
                graph.batch = torch.zeros(graph.num_nodes, dtype=torch.long, device=self.device)
                emb = embedding_model(graph)
                embeddings.append(emb.cpu().numpy())
        
        return np.vstack(embeddings)


# ============================================================================
# PART 5: USAGE EXAMPLE
# ============================================================================

def main():
    """Example usage of the UML Pattern Recognizer"""
    
    # Parse your existing UML models (from your original code)
    # Assuming you have the parse_and_correct_dataset function
    
    print("Loading and parsing UML dataset...")
    # dataset_path = "/path/to/your/uml_dataset"
    # all_usecases = collect_all_usecases(dataset_path)
    # action_order = build_action_order(all_usecases)
    # corrected_models = parse_and_correct_dataset(dataset_path, action_order)
    
    # For demonstration, let's create dummy labels
    # In practice, you would label your use cases (e.g., login=0, payment=1, booking=2, etc.)
    # labels = [0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4]  # Example labels
    
    # Initialize recognizer
    recognizer = UMLPatternRecognizer(
        model_type='gcn',  # or 'gat'
        hidden_dim=64,
        num_classes=6  # Number of pattern categories
    )
    
    # Prepare data
    # graphs = recognizer.prepare_data(corrected_models, labels)
    
    # Split into train/val
    # train_graphs, val_graphs = train_test_split(graphs, test_size=0.2, random_state=42)
    
    # Train model
    # train_losses, val_accs = recognizer.train(
    #     train_graphs, 
    #     val_graphs,
    #     epochs=100,
    #     lr=0.001,
    #     batch_size=8
    # )
    
    # Predict on new UML diagram
    # prediction = recognizer.predict(new_uml_model)
    # print(f"Predicted pattern: {prediction}")
    
    print("GNN model setup complete!")


if __name__ == "__main__":
    main()
