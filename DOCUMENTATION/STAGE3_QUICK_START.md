# 🚀 STAGE 3 QUICK START GUIDE

## 📦 What You Got

1. **stage3_risk_guided_astar.py** - Complete Stage 3 implementation
2. **COMPLETE_PIPELINE_ALL_STAGES.ipynb** - Integrated notebook (Stages 1+2+3)
3. **STAGE3_DOCUMENTATION.md** - Full documentation

---

## ⚡ Quick Start (3 Steps)

### Step 1: Upload Files to Colab

```python
# Upload these files to Colab:
# - stage3_risk_guided_astar.py
# - Your .puml files
```

### Step 2: Install & Import

```python
# Install dependencies
!pip install networkx matplotlib torch torch-geometric -q

# Import Stage 3
from stage3_risk_guided_astar import (
    TestPathGenerator,
    RiskPredictor,
    export_paths_for_llm
)
```

### Step 3: Generate Test Paths

```python
# Assuming you have 'unified_graph' from Stage 2
path_gen = TestPathGenerator(unified_graph)

# Generate paths
test_paths = path_gen.generate_test_paths(
    num_paths=10,
    max_path_length=20
)

# See results
path_gen.print_path_summary()

# Visualize top path
path_gen.visualize_path(0, 'top_risk_path.png')

# Export for Stage 4
export_paths_for_llm(test_paths, unified_graph, 'test_paths.json')
```

**Done! You have test paths!** 🎉

---

## 🎯 Complete Pipeline (One Function)

```python
def uml_to_test_paths_complete(puml_file, dataset_path):
    """Complete pipeline: PlantUML → Test Paths"""
    
    # STAGE 1: Parse PlantUML
    from stage1 import parse_and_correct_plantuml, build_action_order
    
    action_order = build_action_order(collect_all_usecases(dataset_path))
    uml_dict = parse_and_correct_plantuml(puml_file, action_order)
    
    # STAGE 2: Build Graph
    from stage2 import UnifiedGraphBuilder, UMLElements
    
    uml_elements = UMLElements(
        actors=uml_dict['actors'],
        usecases=uml_dict['usecases'],
        classes=uml_dict['classes'],
        associations=uml_dict['relations']
    )
    
    builder = UnifiedGraphBuilder()
    graph = builder.build_unified_graph(uml_elements)
    
    # STAGE 3: Generate Paths
    from stage3_risk_guided_astar import TestPathGenerator
    
    path_gen = TestPathGenerator(graph)
    test_paths = path_gen.generate_test_paths(num_paths=10)
    path_gen.print_path_summary()
    
    return test_paths, graph

# Usage
test_paths, graph = uml_to_test_paths_complete(
    puml_file="/path/to/diagram.puml",
    dataset_path="/path/to/dataset"
)
```

---

## 📊 Output Example

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
  Nodes: IFAAdministration → AuditBudgets → OpenBudget → CheckTransactions → ApproveBudget

Path 2:
  Length: 6 nodes
  Risk: 0.789 (high)
  Cost: 2.156
  Coverage: 30.0%
  Nodes: IFAAdministration → AuditBudgets → OpenBudget → CheckTransactions → NotifyTeam

======================================================================
COVERAGE ANALYSIS
======================================================================
Node Coverage: 85.0% (17/20)
Edge Coverage: 78.0% (23/30)

Coverage by Type:
  actor: 100.0% (2/2)
  usecase: 80.0% (8/10)
  class: 85.7% (6/7)
```

---

## 🎨 Visualization Output

The generated visualization shows:
- 🔴 **Red nodes**: Critical risk (>0.8)
- 🟠 **Orange nodes**: High risk (0.6-0.8)
- 🟡 **Yellow nodes**: Medium risk (0.4-0.6)
- 🔵 **Cyan nodes**: Low risk (0.2-0.4)
- 🟢 **Green nodes**: Minimal risk (≤0.2)

![Example visualization](example_path.png)

---

## 📤 Export for Stage 4

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
        {"id": "N0", "name": "IFAAdministration", "type": "actor"},
        {"id": "N1", "name": "AuditBudgets", "type": "usecase"},
        {"id": "N2", "name": "OpenBudget", "type": "usecase"}
      ],
      "edges": [
        {"source": "N0", "target": "N1"},
        {"source": "N1", "target": "N2"}
      ]
    }
  ]
}
```

---

## 🔧 Customization

### Adjust Risk vs Cost Priority

```python
from stage3_risk_guided_astar import RiskGuidedAStar

# More risk focus (90% risk, 10% cost)
astar = RiskGuidedAStar(graph, risk_scores, alpha=0.9, beta=0.1)

# More cost focus (30% risk, 70% cost)
astar = RiskGuidedAStar(graph, risk_scores, alpha=0.3, beta=0.7)
```

### Filter by Risk Level

```python
# Get only critical paths
critical_paths = [p for p in test_paths if p.risk_score > 0.8]

# Get only high-coverage paths
high_coverage = [p for p in test_paths if p.coverage > 0.5]
```

### Adjust Path Length

```python
# Short paths for unit testing
short_paths = path_gen.generate_test_paths(
    num_paths=20,
    max_path_length=5
)

# Long paths for integration testing
long_paths = path_gen.generate_test_paths(
    num_paths=5,
    max_path_length=30
)
```

---

## 🎯 Your PlantUML Example

From your uploaded file:

```plantuml
@startuml
actor IFAAdministration
actor Team
usecase AuditBudgets
usecase OpenBudget
usecase CheckTransactions
usecase ApproveBudget
usecase NotifyTeam
class BudgetSystem

IFAAdministration --> AuditBudgets
AuditBudgets --> OpenBudget
OpenBudget --> CheckTransactions
CheckTransactions --> ApproveBudget
ApproveBudget --> NotifyTeam
NotifyTeam --> BudgetSystem
Team --> BudgetSystem
@enduml
```

### Expected Output

**Test Path 1** (Highest Risk):
```
IFAAdministration → AuditBudgets → OpenBudget → CheckTransactions → ApproveBudget → NotifyTeam → BudgetSystem
```

**Test Path 2**:
```
IFAAdministration → AuditBudgets → OpenBudget → CheckTransactions → ApproveBudget
```

**Test Path 3**:
```
Team → BudgetSystem
```

---

## 📋 Checklist

- [ ] Upload `stage3_risk_guided_astar.py` to Colab
- [ ] Install dependencies (`pip install networkx matplotlib torch torch-geometric`)
- [ ] Import Stage 3 classes
- [ ] Load your unified graph from Stage 2
- [ ] Create `TestPathGenerator` instance
- [ ] Generate test paths
- [ ] Review summary and visualizations
- [ ] Export JSON for Stage 4
- [ ] Proceed to Stage 4: LLM Test Case Generation

---

## ❓ Troubleshooting

### Issue: "No paths generated"
**Solution**: Check if your graph has proper connections between actors and usecases.

### Issue: "All paths have low risk"
**Solution**: The GNN is untrained. For production, train the GNN on labeled data.

### Issue: "Too many redundant paths"
**Solution**: Increase `redundancy_threshold` to 0.9 or higher.

### Issue: "Paths too short"
**Solution**: Increase `max_path_length` parameter.

---

## 🎓 Key Concepts

### Risk Score
- **0.0-0.2**: Minimal risk (green)
- **0.2-0.4**: Low risk (cyan)
- **0.4-0.6**: Medium risk (yellow)
- **0.6-0.8**: High risk (orange)
- **0.8-1.0**: Critical risk (red)

### Path Cost
- Lower = shorter, more direct path
- Higher = longer, more complex path
- A* balances risk and cost

### Coverage
- Percentage of nodes/edges covered by all paths
- Target: >80% for comprehensive testing

---

## 🚀 Next Steps

### Stage 4: LLM Test Case Generation

Use the exported JSON to:
1. Convert paths to natural language
2. Generate test steps
3. Add preconditions and expected results
4. Create test data

Example Stage 4 output:
```
Test Case 1: Audit Budget Approval Flow
Priority: High
Risk: Critical

Preconditions:
- User has IFA Administrator role
- Budget exists in system

Steps:
1. Login as IFA Administrator
2. Navigate to Audit Budgets
3. Open Budget for review
4. Check all transactions
5. Approve the budget
6. Verify notification sent to team

Expected Result:
- Budget status updated to "Approved"
- Team receives notification
- Changes logged in BudgetSystem
```

---

## 📚 Resources

- **Full Documentation**: See `STAGE3_DOCUMENTATION.md`
- **Complete Notebook**: See `COMPLETE_PIPELINE_ALL_STAGES.ipynb`
- **Source Code**: See `stage3_risk_guided_astar.py`

---

## 💡 Tips

1. **Start Small**: Test with 1-2 diagrams first
2. **Adjust Parameters**: Tune `alpha`, `beta`, `num_paths` based on your needs
3. **Visualize**: Always visualize top paths to verify quality
4. **Check Coverage**: Aim for >80% node coverage
5. **Remove Redundancy**: Set threshold to 0.8 or higher

---

## ✅ Success Criteria

You've successfully completed Stage 3 when:
- ✅ Test paths generated with risk scores
- ✅ Paths prioritized by risk level
- ✅ Coverage >80% achieved
- ✅ Redundant paths removed
- ✅ Visualizations created
- ✅ JSON exported for Stage 4

🎉 **Congratulations! Stage 3 Complete!** 🎉

Now proceed to **Stage 4: LLM-based Test Case Generation** to convert these paths into human-readable test cases!
