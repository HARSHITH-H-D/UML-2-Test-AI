"""
COMPREHENSIVE SOLUTION FOR UML DIAGRAMS DATASET

This script:
1. Parses Draw.io XML files from the uploaded dataset
2. Extracts UML elements (actors, use cases, classes, relationships)
3. Generates PlantUML (.puml) files
4. Answers the training data question

Dataset: Dalpiaz2018 - User Stories to UML Diagrams
"""

import xml.etree.ElementTree as ET
import os
import re
import base64
import zlib
from pathlib import Path
from typing import Dict, List, Tuple, Set


# ============================================================================
# PART 1: DRAW.IO XML PARSER
# ============================================================================

class DrawIOParser:
    """Parse Draw.io XML files and extract UML elements"""
    
    def __init__(self):
        self.actors = []
        self.usecases = []
        self.classes = []
        self.relationships = []
        self.elements = {}
        
    def parse_xml_file(self, xml_path: str):
        """Parse a Draw.io XML file"""
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            # Draw.io stores diagrams in mxGraphModel
            diagram = root.find('.//diagram')
            if diagram is not None:
                # Decode the diagram content (it's base64 + deflate compressed)
                diagram_content = diagram.text
                if diagram_content:
                    # Decompress and decode
                    try:
                        decoded = base64.b64decode(diagram_content)
                        decompressed = zlib.decompress(decoded, -zlib.MAX_WBITS)
                        diagram_xml = decompressed.decode('utf-8')
                        
                        # Parse the decompressed XML
                        diagram_root = ET.fromstring(diagram_xml)
                        self._extract_elements(diagram_root)
                    except Exception as e:
                        print(f"Error decompressing diagram: {e}")
                        # Try parsing raw XML
                        self._extract_elements(root)
            else:
                # Direct XML structure
                self._extract_elements(root)
                
            return True
        except Exception as e:
            print(f"Error parsing {xml_path}: {e}")
            return False
    
    def _extract_elements(self, root):
        """Extract UML elements from XML"""
        # Find all mxCell elements
        for cell in root.findall('.//mxCell'):
            cell_id = cell.get('id', '')
            style = cell.get('style', '')
            value = cell.get('value', '')
            
            # Skip empty cells
            if not value or value.startswith('&lt;'):
                continue
            
            # Detect element type by style
            if 'ellipse' in style.lower() and 'uml' in style.lower():
                # Use case
                self.usecases.append((cell_id, value))
                self.elements[cell_id] = ('usecase', value)
            
            elif 'shape=umlActor' in style or 'actor' in style.lower():
                # Actor
                self.actors.append((cell_id, value))
                self.elements[cell_id] = ('actor', value)
            
            elif 'swimlane' in style.lower() or 'class' in value.lower():
                # Class
                self.classes.append((cell_id, value))
                self.elements[cell_id] = ('class', value)
            
            # Extract relationships (edges)
            source = cell.get('source')
            target = cell.get('target')
            
            if source and target:
                edge_type = self._infer_edge_type(style, value)
                self.relationships.append((source, target, edge_type))
    
    def _infer_edge_type(self, style: str, value: str) -> str:
        """Infer relationship type from style and label"""
        value_lower = value.lower()
        style_lower = style.lower()
        
        if '<<include>>' in value_lower or 'include' in value_lower:
            return 'include'
        elif '<<extend>>' in value_lower or 'extend' in value_lower:
            return 'extend'
        elif 'dashed' in style_lower:
            return 'dependency'
        else:
            return 'association'
    
    def get_elements(self):
        """Get all parsed elements"""
        return {
            'actors': self.actors,
            'usecases': self.usecases,
            'classes': self.classes,
            'relationships': self.relationships
        }


# ============================================================================
# PART 2: PLANTUML GENERATOR
# ============================================================================

class PlantUMLGenerator:
    """Generate PlantUML files from parsed UML elements"""
    
    @staticmethod
    def generate_puml(elements: Dict, output_path: str):
        """Generate a PlantUML file"""
        puml_content = ["@startuml"]
        
        # Add actors
        for actor_id, actor_name in elements['actors']:
            clean_name = PlantUMLGenerator._clean_name(actor_name)
            puml_content.append(f"actor {clean_name}")
        
        # Add use cases
        for uc_id, uc_name in elements['usecases']:
            clean_name = PlantUMLGenerator._clean_name(uc_name)
            puml_content.append(f"usecase \"{uc_name}\" as {clean_name}")
        
        # Add classes
        for class_id, class_name in elements['classes']:
            clean_name = PlantUMLGenerator._clean_name(class_name)
            puml_content.append(f"class {clean_name}")
        
        # Add relationships
        id_to_name = {}
        for actor_id, actor_name in elements['actors']:
            id_to_name[actor_id] = PlantUMLGenerator._clean_name(actor_name)
        for uc_id, uc_name in elements['usecases']:
            id_to_name[uc_id] = PlantUMLGenerator._clean_name(uc_name)
        for class_id, class_name in elements['classes']:
            id_to_name[class_id] = PlantUMLGenerator._clean_name(class_name)
        
        puml_content.append("")  # Empty line
        
        for source_id, target_id, rel_type in elements['relationships']:
            source = id_to_name.get(source_id, source_id)
            target = id_to_name.get(target_id, target_id)
            
            if rel_type == 'include':
                puml_content.append(f"{source} ..> {target} : <<include>>")
            elif rel_type == 'extend':
                puml_content.append(f"{source} ..> {target} : <<extend>>")
            elif rel_type == 'dependency':
                puml_content.append(f"{source} ..> {target}")
            else:
                puml_content.append(f"{source} --> {target}")
        
        puml_content.append("@enduml")
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(puml_content))
        
        return output_path
    
    @staticmethod
    def _clean_name(name: str) -> str:
        """Clean name for PlantUML identifier"""
        # Remove special characters
        clean = re.sub(r'[^\w\s]', '', name)
        # Replace spaces with underscore
        clean = re.sub(r'\s+', '_', clean)
        # Limit length
        return clean[:50]


# ============================================================================
# PART 3: BATCH PROCESSOR
# ============================================================================

def process_uml_dataset(input_dir: str, output_dir: str):
    """
    Process entire UML dataset
    
    Args:
        input_dir: Directory containing UML_DIAGRAMS
        output_dir: Output directory for PUML files
    """
    os.makedirs(output_dir, exist_ok=True)
    
    parser = DrawIOParser()
    stats = {
        'total_files': 0,
        'successful': 0,
        'failed': 0,
        'total_actors': 0,
        'total_usecases': 0,
        'total_classes': 0,
        'total_relationships': 0
    }
    
    print("="*70)
    print("PROCESSING UML DATASET TO PLANTUML")
    print("="*70)
    
    # Find all XML files
    xml_files = []
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.endswith('.xml'):
                xml_files.append(os.path.join(root, file))
    
    stats['total_files'] = len(xml_files)
    print(f"\nFound {len(xml_files)} XML files")
    
    # Process each file
    for i, xml_path in enumerate(xml_files, 1):
        parser = DrawIOParser()
        
        if parser.parse_xml_file(xml_path):
            elements = parser.get_elements()
            
            # Skip if no elements found
            if not any(elements.values()):
                print(f"[{i}/{len(xml_files)}] ⚠️  {os.path.basename(xml_path)} - No elements found")
                stats['failed'] += 1
                continue
            
            # Generate output path
            relative_path = os.path.relpath(xml_path, input_dir)
            output_path = os.path.join(
                output_dir,
                relative_path.replace('.xml', '.puml')
            )
            
            # Create output directory
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Generate PlantUML
            PlantUMLGenerator.generate_puml(elements, output_path)
            
            # Update stats
            stats['successful'] += 1
            stats['total_actors'] += len(elements['actors'])
            stats['total_usecases'] += len(elements['usecases'])
            stats['total_classes'] += len(elements['classes'])
            stats['total_relationships'] += len(elements['relationships'])
            
            print(f"[{i}/{len(xml_files)}] ✓ {os.path.basename(xml_path)} -> {os.path.basename(output_path)}")
            print(f"           Actors: {len(elements['actors'])}, UseCases: {len(elements['usecases'])}, "
                  f"Classes: {len(elements['classes'])}, Relations: {len(elements['relationships'])}")
        else:
            print(f"[{i}/{len(xml_files)}] ✗ {os.path.basename(xml_path)} - Failed to parse")
            stats['failed'] += 1
    
    # Print summary
    print("\n" + "="*70)
    print("PROCESSING COMPLETE")
    print("="*70)
    print(f"Total files processed: {stats['total_files']}")
    print(f"Successful: {stats['successful']}")
    print(f"Failed: {stats['failed']}")
    print(f"\nExtracted Elements:")
    print(f"  Actors: {stats['total_actors']}")
    print(f"  Use Cases: {stats['total_usecases']}")
    print(f"  Classes: {stats['total_classes']}")
    print(f"  Relationships: {stats['total_relationships']}")
    print("="*70)
    
    return stats


# ============================================================================
# PART 4: ANSWER TRAINING DATA QUESTION
# ============================================================================

def answer_training_data_question():
    """
    Answer: Do I need error data to train the model, or is normal data enough?
    """
    answer = """
╔══════════════════════════════════════════════════════════════════════════╗
║           TRAINING DATA QUESTION - COMPREHENSIVE ANSWER                  ║
╚══════════════════════════════════════════════════════════════════════════╝

QUESTION:
"Do I need error data to train it or normal data is enough for this project?"

SHORT ANSWER:
For UML Pattern Recognition with GNN, you primarily need NORMAL (correct) data.
Error data is optional but can be beneficial for specific advanced tasks.

DETAILED EXPLANATION:

┌────────────────────────────────────────────────────────────────────────┐
│ 1. PRIMARY USE CASE: Pattern Recognition/Classification               │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│ What you need: NORMAL DATA ONLY                                        │
│                                                                         │
│ Why:                                                                    │
│ - Your goal is to classify UML diagrams into pattern categories        │
│ - GNN learns from correct examples of each pattern                     │
│ - Training: "This is a Login pattern, this is a Payment pattern"       │
│                                                                         │
│ Dataset Requirements:                                                  │
│ ✓ Well-formed UML diagrams                                            │
│ ✓ Labeled by pattern type (login, payment, booking, etc.)             │
│ ✓ Diverse examples of each pattern                                    │
│ ✓ Minimum 20-30 examples per pattern category                         │
│                                                                         │
│ Example Training Data:                                                 │
│   File: login_001.puml         → Label: "Login"                       │
│   File: payment_003.puml       → Label: "Payment"                     │
│   File: booking_002.puml       → Label: "Booking"                     │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│ 2. WHEN ERROR DATA IS USEFUL (Advanced/Optional)                      │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│ Error data becomes useful for:                                         │
│                                                                         │
│ a) Quality Assessment / Anomaly Detection                              │
│    - Detect anti-patterns or design flaws                             │
│    - Identify incomplete diagrams                                      │
│    - Find violations of UML best practices                            │
│                                                                         │
│ b) Robustness Training                                                 │
│    - Make model robust to noisy/imperfect input                       │
│    - Handle real-world messy diagrams                                 │
│                                                                         │
│ c) Binary Classification Tasks                                         │
│    - "Is this diagram well-formed?" (Yes/No)                          │
│    - "Does this follow best practices?" (Yes/No)                      │
│                                                                         │
│ Types of Error Data:                                                   │
│   ✗ Missing actors in use case diagrams                               │
│   ✗ Disconnected components                                           │
│   ✗ Circular dependencies                                             │
│   ✗ Incomplete relationships                                          │
│   ✗ Anti-patterns (God class, spaghetti connections)                 │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│ 3. YOUR PROJECT SPECIFICALLY                                          │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│ Based on your workflow:                                                │
│   PlantUML → Unified Graph (Stage 2) → GNN Training                  │
│                                                                         │
│ RECOMMENDATION: START WITH NORMAL DATA ONLY                            │
│                                                                         │
│ Reasons:                                                               │
│ 1. Your Stage 2 (Unified Graph Construction) is designed for          │
│    well-formed UML diagrams                                            │
│                                                                         │
│ 2. Pattern recognition works best with clean, labeled examples        │
│                                                                         │
│ 3. Error data adds complexity without clear benefit for basic         │
│    classification                                                      │
│                                                                         │
│ 4. You can always add error detection as Phase 2 later                │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│ 4. RECOMMENDED TRAINING STRATEGY                                       │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│ PHASE 1: Pattern Recognition (NORMAL DATA ONLY)                       │
│ ──────────────────────────────────────────────────────────────────────│
│ Goal: Classify diagrams into pattern categories                       │
│                                                                         │
│ Dataset Composition:                                                   │
│   Training Set (70%):   Well-formed diagrams with labels              │
│   Validation Set (15%): Clean diagrams for tuning                     │
│   Test Set (15%):       Clean diagrams for evaluation                 │
│                                                                         │
│ What you have:                                                         │
│   ✓ IFA Football dataset (23 diagrams)                                │
│   ✓ Dalpiaz2018 dataset (your uploaded files)                        │
│   ✓ PyUNML dataset examples                                          │
│                                                                         │
│ Status: SUFFICIENT for Phase 1                                         │
│                                                                         │
│ ──────────────────────────────────────────────────────────────────────│
│ PHASE 2: Quality Assessment (OPTIONAL - ADD ERROR DATA)               │
│ ──────────────────────────────────────────────────────────────────────│
│ Goal: Detect diagram quality issues                                   │
│                                                                         │
│ Dataset Composition:                                                   │
│   Positive Examples (50%): Well-formed diagrams                       │
│   Negative Examples (50%): Diagrams with known errors                 │
│                                                                         │
│ How to create error data:                                             │
│   1. Manually introduce errors in correct diagrams                    │
│   2. Collect real-world messy diagrams                                │
│   3. Generate synthetic errors programmatically                       │
│                                                                         │
│ Status: NOT NEEDED YET                                                 │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│ 5. DATA AUGMENTATION (Better than Error Data)                         │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│ Instead of error data, use AUGMENTATION on normal data:               │
│                                                                         │
│ Techniques:                                                            │
│   1. Node Dropout:  Randomly remove some nodes                        │
│   2. Edge Dropout:  Randomly remove some edges                        │
│   3. Node Feature Noise: Add noise to node attributes                │
│   4. Subgraph Sampling: Extract subgraphs                             │
│   5. Graph Perturbation: Small structural changes                    │
│                                                                         │
│ Benefits:                                                              │
│   ✓ Makes model more robust                                          │
│   ✓ Prevents overfitting                                             │
│   ✓ Increases effective dataset size                                 │
│   ✓ No need to manually create error examples                        │
│                                                                         │
│ Implementation:                                                        │
│   Already supported in PyTorch Geometric!                             │
│   Can be added during training loop                                   │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│ 6. MINIMUM DATASET SIZE                                                │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│ For Pattern Recognition (your use case):                              │
│                                                                         │
│   Minimum per category:  20-30 diagrams                               │
│   Recommended:           50-100 diagrams                              │
│   Ideal:                 200+ diagrams                                │
│                                                                         │
│ What you have:                                                         │
│   IFA Football:          23 diagrams (6 categories)                   │
│   Dalpiaz2018:           ~40+ diagrams (estimated)                    │
│   Combined:              ~60-70 diagrams                              │
│                                                                         │
│ Status:                  SUFFICIENT for initial training              │
│                                                                         │
│ Tips to improve:                                                       │
│   1. Combine multiple datasets                                        │
│   2. Create 3 variations per use case (as you did)                    │
│   3. Use data augmentation                                            │
│   4. Transfer learning from pre-trained GNN                           │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│ 7. PRACTICAL EXAMPLE                                                  │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│ YOUR TRAINING DATA:                                                    │
│                                                                         │
│ ✓ NORMAL DATA (Use this!)                                            │
│ ├── Login patterns (10 diagrams)                                      │
│ ├── Payment patterns (10 diagrams)                                    │
│ ├── Booking patterns (10 diagrams)                                    │
│ ├── Healthcare patterns (10 diagrams)                                 │
│ └── E-commerce patterns (10 diagrams)                                 │
│                                                                         │
│ ✗ ERROR DATA (Skip for now!)                                         │
│ ├── Incomplete diagrams                                               │
│ ├── Malformed relationships                                           │
│ └── Anti-patterns                                                     │
│                                                                         │
│ TRAINING PROCESS:                                                      │
│ 1. Parse all normal diagrams                                          │
│ 2. Build unified graphs (Stage 2)                                     │
│ 3. Convert to PyG format                                              │
│ 4. Train GNN to classify patterns                                     │
│ 5. Evaluate on test set                                               │
│ 6. Deploy for new diagram classification                              │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘

FINAL RECOMMENDATION:
═══════════════════════════════════════════════════════════════════════

✅ FOR YOUR PROJECT: Use NORMAL DATA ONLY

   What you need:
   • Well-formed UML diagrams
   • Labeled by pattern type
   • Diverse examples (3+ per pattern)
   • 50-100+ total diagrams

   What you DON'T need (yet):
   • Error examples
   • Malformed diagrams
   • Anti-patterns
   • Noisy data

   Next steps:
   1. ✓ Use the Dalpiaz2018 dataset (uploaded)
   2. ✓ Use the IFA Football dataset (created)
   3. ✓ Convert all to PlantUML
   4. ✓ Label by pattern type
   5. ✓ Train GNN model
   6. ✓ Evaluate results

   Optional future enhancement:
   • Add error detection as Phase 2
   • Use data augmentation for robustness
   • Create synthetic variations

═══════════════════════════════════════════════════════════════════════
"""
    
    print(answer)
    return answer


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    # Answer the training data question
    answer_training_data_question()
    
    print("\n\n")
    
    # Process the uploaded dataset
    input_dir = "/home/claude/UML_DIAGRAMS"
    output_dir = "/home/claude/generated_puml"
    
    if os.path.exists(input_dir):
        stats = process_uml_dataset(input_dir, output_dir)
        
        print(f"\n✓ Generated PlantUML files saved to: {output_dir}")
        print(f"\nYou can now use these files with:")
        print(f"  1. Stage 2: Unified Graph Construction")
        print(f"  2. GNN Training Pipeline")
    else:
        print(f"Input directory not found: {input_dir}")
