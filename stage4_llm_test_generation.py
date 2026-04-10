"""
STAGE 4: LLM-BASED TEST CASE GENERATION

This module implements:
1. Path-to-Test Case Conversion using LLM
2. Test Case Validation and Ranking
3. Multiple Test Case Variations
4. Human-Readable Output Generation

Based on the project architecture from UML_TestCase_Second_Review_Neon_Theme.pptx:
- Transformer-Based LLM for test case generation
- Generates multiple variations per path
- Produces structured, human-readable test cases
- Validation and priority ranking
"""

import json
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import networkx as nx


# ============================================================================
# PART 1: DATA STRUCTURES
# ============================================================================

class TestCasePriority(Enum):
    """Test case priority levels"""
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class TestCaseType(Enum):
    """Types of test cases"""
    POSITIVE = "Positive"  # Happy path
    NEGATIVE = "Negative"  # Error handling
    BOUNDARY = "Boundary"  # Edge cases
    INTEGRATION = "Integration"  # Multi-component


@dataclass
class TestStep:
    """Individual test step"""
    step_number: int
    action: str
    expected_result: str
    notes: Optional[str] = None


@dataclass
class TestCase:
    """Complete test case structure"""
    test_id: str
    title: str
    description: str
    priority: TestCasePriority
    test_type: TestCaseType
    
    # Test details
    preconditions: List[str]
    test_steps: List[TestStep]
    expected_results: List[str]
    postconditions: List[str]
    
    # Metadata
    risk_score: float
    coverage: float
    path_length: int
    tags: List[str] = field(default_factory=list)
    
    # Optional
    test_data: Optional[Dict] = None
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'test_id': self.test_id,
            'title': self.title,
            'description': self.description,
            'priority': self.priority.value,
            'test_type': self.test_type.value,
            'preconditions': self.preconditions,
            'test_steps': [
                {
                    'step': step.step_number,
                    'action': step.action,
                    'expected': step.expected_result,
                    'notes': step.notes
                }
                for step in self.test_steps
            ],
            'expected_results': self.expected_results,
            'postconditions': self.postconditions,
            'metadata': {
                'risk_score': self.risk_score,
                'coverage': self.coverage,
                'path_length': self.path_length,
                'tags': self.tags
            },
            'test_data': self.test_data,
            'notes': self.notes
        }


# ============================================================================
# PART 2: LLM PROMPT TEMPLATES
# ============================================================================

class PromptTemplates:
    """Templates for LLM prompts"""
    
    @staticmethod
    def generate_test_case_prompt(path_info: Dict, variation: str = "positive") -> str:
        """
        Generate prompt for LLM to create test case.
        
        Args:
            path_info: Dictionary with path details from Stage 3
            variation: Type of test case to generate
            
        Returns:
            Formatted prompt string
        """
        nodes_desc = " → ".join([
            f"{node['name']} ({node['type']})" 
            for node in path_info['nodes']
        ])
        
        prompt = f"""You are a software testing expert. Generate a detailed test case based on the following UML execution path.

**Execution Path:**
{nodes_desc}

**Path Details:**
- Priority: {path_info['priority']}
- Risk Score: {path_info['risk_score']:.3f}
- Path Length: {path_info['length']} nodes

**Test Case Type:** {variation.title()}

**Instructions:**
Generate a comprehensive test case with the following structure:

1. **Test ID**: Use format TC-{path_info['priority']:03d}-{variation[:3].upper()}
2. **Title**: Clear, concise test case title (max 80 chars)
3. **Description**: Brief description of what this test validates
4. **Preconditions**: List 2-4 preconditions needed before test execution
5. **Test Steps**: Detailed step-by-step instructions (one step per node in path)
6. **Expected Results**: List expected outcomes for each major step
7. **Postconditions**: List system state after test completion
8. **Test Data**: Sample data needed for test execution

**Output Format (JSON):**
{{
    "title": "string",
    "description": "string",
    "preconditions": ["string", ...],
    "test_steps": [
        {{
            "step": 1,
            "action": "string",
            "expected": "string"
        }},
        ...
    ],
    "expected_results": ["string", ...],
    "postconditions": ["string", ...],
    "test_data": {{
        "key": "value"
    }},
    "tags": ["string", ...]
}}

Generate ONLY the JSON output, no additional text.
"""
        return prompt
    
    @staticmethod
    def validate_test_case_prompt(test_case_json: str) -> str:
        """Generate prompt for test case validation"""
        prompt = f"""You are a QA validator. Review the following test case for quality and completeness.

**Test Case:**
{test_case_json}

**Validation Criteria:**
1. Preconditions are clear and testable
2. Test steps are detailed and sequential
3. Expected results are specific and measurable
4. No ambiguous language
5. Test data is realistic and sufficient

**Output Format (JSON):**
{{
    "is_valid": true/false,
    "quality_score": 0-100,
    "issues": ["issue1", "issue2", ...],
    "suggestions": ["suggestion1", "suggestion2", ...]
}}

Generate ONLY the JSON output.
"""
        return prompt


# ============================================================================
# PART 3: LLM TEST CASE GENERATOR
# ============================================================================

class LLMTestCaseGenerator:
    """
    Generates test cases from test paths using LLM.
    
    Note: This is a template-based implementation.
    For production, integrate with actual LLM API (OpenAI, Claude, etc.)
    """
    
    def __init__(self, use_llm: bool = False, api_key: Optional[str] = None):
        """
        Initialize generator.
        
        Args:
            use_llm: Whether to use actual LLM API (requires API key)
            api_key: API key for LLM service
        """
        self.use_llm = use_llm
        self.api_key = api_key
        
        if use_llm and not api_key:
            print("⚠️ Warning: LLM API key not provided. Using template-based generation.")
            self.use_llm = False
    
    def generate_test_case(self, 
                          path_info: Dict, 
                          variation: str = "positive") -> TestCase:
        """
        Generate test case from path information.
        
        Args:
            path_info: Path dictionary from Stage 3 export
            variation: Test case variation type
            
        Returns:
            TestCase object
        """
        if self.use_llm:
            return self._generate_with_llm(path_info, variation)
        else:
            return self._generate_with_template(path_info, variation)
    
    def _generate_with_template(self, path_info: Dict, variation: str) -> TestCase:
        """
        Template-based test case generation.
        (Fallback when LLM is not available)
        """
        nodes = path_info['nodes']
        priority = path_info['priority']
        risk_score = path_info['risk_score']
        
        # Determine priority level
        if risk_score > 0.8:
            priority_level = TestCasePriority.CRITICAL
        elif risk_score > 0.6:
            priority_level = TestCasePriority.HIGH
        elif risk_score > 0.4:
            priority_level = TestCasePriority.MEDIUM
        else:
            priority_level = TestCasePriority.LOW
        
        # Determine test type
        test_type_map = {
            'positive': TestCaseType.POSITIVE,
            'negative': TestCaseType.NEGATIVE,
            'boundary': TestCaseType.BOUNDARY,
            'integration': TestCaseType.INTEGRATION
        }
        test_type = test_type_map.get(variation, TestCaseType.POSITIVE)
        
        # Generate test ID
        test_id = f"TC-{priority:03d}-{variation[:3].upper()}-{hash(str(nodes)) % 1000:03d}"
        
        # Extract actors and use cases
        actors = [n for n in nodes if n['type'] == 'actor']
        usecases = [n for n in nodes if n['type'] == 'usecase']
        classes = [n for n in nodes if n['type'] == 'class']
        
        # Generate title
        if usecases:
            main_flow = " → ".join([uc['name'] for uc in usecases[:3]])
            if len(usecases) > 3:
                main_flow += " → ..."
            title = f"Verify {main_flow}"
        else:
            title = f"Test path with {len(nodes)} components"
        
        # Generate description
        if actors:
            actor_name = actors[0]['name']
            description = f"Verify that {actor_name} can successfully execute the workflow: {main_flow}"
        else:
            description = f"Verify the execution flow through {len(nodes)} components"
        
        # Generate preconditions
        preconditions = []
        if actors:
            preconditions.append(f"{actors[0]['name']} has valid credentials and permissions")
        preconditions.append("System is in stable state")
        preconditions.append("All required services are running")
        if classes:
            preconditions.append(f"{classes[0]['name']} is properly initialized")
        
        # Generate test steps
        test_steps = []
        for i, node in enumerate(nodes, 1):
            if node['type'] == 'actor':
                action = f"Login as {node['name']}"
                expected = f"{node['name']} successfully authenticated"
            elif node['type'] == 'usecase':
                action = f"Execute {node['name']}"
                expected = f"{node['name']} completes successfully"
            elif node['type'] == 'class':
                action = f"Interact with {node['name']}"
                expected = f"{node['name']} responds correctly"
            else:
                action = f"Process {node['name']}"
                expected = f"{node['name']} executes as expected"
            
            test_steps.append(TestStep(
                step_number=i,
                action=action,
                expected_result=expected,
                notes=None
            ))
        
        # Generate expected results
        expected_results = [
            "All steps complete without errors",
            "System remains in consistent state",
            "Expected outputs are produced"
        ]
        if usecases:
            expected_results.append(f"Workflow completes: {' → '.join([uc['name'] for uc in usecases])}")
        
        # Generate postconditions
        postconditions = [
            "System returns to stable state",
            "All resources are properly released",
            "Audit logs are updated correctly"
        ]
        
        # Generate tags
        tags = [node['name'] for node in usecases[:3]]
        tags.append(variation)
        if risk_score > 0.6:
            tags.append('high-risk')
        
        # Generate test data
        test_data = {
            'username': 'test_user',
            'password': 'Test@1234',
            'environment': 'test'
        }
        
        # Add specific data based on node names
        for node in nodes:
            name_lower = node['name'].lower()
            if 'budget' in name_lower:
                test_data['budget_id'] = 'BUD-001'
                test_data['amount'] = '1000.00'
            elif 'payment' in name_lower:
                test_data['payment_method'] = 'credit_card'
                test_data['card_number'] = '4111111111111111'
            elif 'user' in name_lower:
                test_data['user_id'] = 'USR-123'
        
        return TestCase(
            test_id=test_id,
            title=title,
            description=description,
            priority=priority_level,
            test_type=test_type,
            preconditions=preconditions,
            test_steps=test_steps,
            expected_results=expected_results,
            postconditions=postconditions,
            risk_score=risk_score,
            coverage=path_info['coverage'],
            path_length=path_info['length'],
            tags=tags,
            test_data=test_data,
            notes=f"Generated from path with {len(nodes)} nodes, risk score: {risk_score:.3f}"
        )
    
    def _generate_with_llm(self, path_info: Dict, variation: str) -> TestCase:
        """
        LLM-based test case generation.
        
        Note: Requires actual LLM API integration.
        This is a placeholder for the integration point.
        """
        # TODO: Integrate with actual LLM API (OpenAI, Anthropic, etc.)
        # For now, fall back to template
        print("⚠️ LLM API not fully integrated. Using template-based generation.")
        return self._generate_with_template(path_info, variation)


# ============================================================================
# PART 4: TEST CASE VALIDATOR
# ============================================================================

class TestCaseValidator:
    """Validates and ranks test cases"""
    
    @staticmethod
    def validate_test_case(test_case: TestCase) -> Tuple[bool, float, List[str]]:
        """
        Validate test case quality.
        
        Returns:
            (is_valid, quality_score, issues)
        """
        issues = []
        score = 100.0
        
        # Check title
        if not test_case.title or len(test_case.title) > 100:
            issues.append("Title missing or too long")
            score -= 10
        
        # Check preconditions
        if not test_case.preconditions or len(test_case.preconditions) < 2:
            issues.append("Insufficient preconditions (need at least 2)")
            score -= 15
        
        # Check test steps
        if not test_case.test_steps or len(test_case.test_steps) < 2:
            issues.append("Insufficient test steps (need at least 2)")
            score -= 20
        
        # Check expected results
        if not test_case.expected_results:
            issues.append("Expected results missing")
            score -= 15
        
        # Check for ambiguous language
        ambiguous_words = ['maybe', 'might', 'could', 'should possibly']
        for step in test_case.test_steps:
            if any(word in step.action.lower() for word in ambiguous_words):
                issues.append(f"Ambiguous language in step {step.step_number}")
                score -= 5
        
        is_valid = score >= 70.0
        
        return is_valid, max(0, score), issues
    
    @staticmethod
    def rank_test_cases(test_cases: List[TestCase]) -> List[TestCase]:
        """
        Rank test cases by importance.
        
        Ranking criteria:
        1. Risk score (higher = more important)
        2. Coverage (higher = more important)
        3. Priority level
        """
        def rank_score(tc: TestCase) -> float:
            priority_weights = {
                TestCasePriority.CRITICAL: 4.0,
                TestCasePriority.HIGH: 3.0,
                TestCasePriority.MEDIUM: 2.0,
                TestCasePriority.LOW: 1.0
            }
            
            return (
                tc.risk_score * 0.5 +
                tc.coverage * 0.3 +
                priority_weights.get(tc.priority, 1.0) * 0.2
            )
        
        return sorted(test_cases, key=rank_score, reverse=True)


# ============================================================================
# PART 5: TEST CASE FORMATTER
# ============================================================================

class TestCaseFormatter:
    """Formats test cases for different outputs"""
    
    @staticmethod
    def to_markdown(test_case: TestCase) -> str:
        """Convert test case to Markdown format"""
        md = f"# {test_case.test_id}: {test_case.title}\n\n"
        md += f"**Priority:** {test_case.priority.value}  \n"
        md += f"**Type:** {test_case.test_type.value}  \n"
        md += f"**Risk Score:** {test_case.risk_score:.3f}  \n\n"
        
        md += f"## Description\n{test_case.description}\n\n"
        
        md += "## Preconditions\n"
        for i, pre in enumerate(test_case.preconditions, 1):
            md += f"{i}. {pre}\n"
        md += "\n"
        
        md += "## Test Steps\n"
        md += "| Step | Action | Expected Result |\n"
        md += "|------|--------|----------------|\n"
        for step in test_case.test_steps:
            md += f"| {step.step_number} | {step.action} | {step.expected_result} |\n"
        md += "\n"
        
        md += "## Expected Results\n"
        for i, result in enumerate(test_case.expected_results, 1):
            md += f"{i}. {result}\n"
        md += "\n"
        
        md += "## Postconditions\n"
        for i, post in enumerate(test_case.postconditions, 1):
            md += f"{i}. {post}\n"
        md += "\n"
        
        if test_case.test_data:
            md += "## Test Data\n```json\n"
            md += json.dumps(test_case.test_data, indent=2)
            md += "\n```\n\n"
        
        if test_case.tags:
            md += f"**Tags:** {', '.join(test_case.tags)}\n"
        
        return md
    
    @staticmethod
    def to_html(test_case: TestCase) -> str:
        """Convert test case to HTML format"""
        html = f"""
<div class="test-case" id="{test_case.test_id}">
    <h2>{test_case.test_id}: {test_case.title}</h2>
    <div class="metadata">
        <span class="priority {test_case.priority.value.lower()}">{test_case.priority.value}</span>
        <span class="type">{test_case.test_type.value}</span>
        <span class="risk">Risk: {test_case.risk_score:.3f}</span>
    </div>
    
    <h3>Description</h3>
    <p>{test_case.description}</p>
    
    <h3>Preconditions</h3>
    <ol>
        {''.join([f'<li>{pre}</li>' for pre in test_case.preconditions])}
    </ol>
    
    <h3>Test Steps</h3>
    <table>
        <thead>
            <tr>
                <th>Step</th>
                <th>Action</th>
                <th>Expected Result</th>
            </tr>
        </thead>
        <tbody>
            {''.join([f'<tr><td>{s.step_number}</td><td>{s.action}</td><td>{s.expected_result}</td></tr>' for s in test_case.test_steps])}
        </tbody>
    </table>
    
    <h3>Expected Results</h3>
    <ul>
        {''.join([f'<li>{result}</li>' for result in test_case.expected_results])}
    </ul>
    
    <h3>Postconditions</h3>
    <ol>
        {''.join([f'<li>{post}</li>' for post in test_case.postconditions])}
    </ol>
</div>
"""
        return html


# ============================================================================
# PART 6: COMPLETE STAGE 4 PIPELINE
# ============================================================================

class TestCaseGenerationPipeline:
    """Complete Stage 4 pipeline"""
    
    def __init__(self, use_llm: bool = False, api_key: Optional[str] = None):
        self.generator = LLMTestCaseGenerator(use_llm, api_key)
        self.validator = TestCaseValidator()
        self.formatter = TestCaseFormatter()
    
    def generate_test_cases_from_paths(self,
                                      paths_json_file: str,
                                      variations: List[str] = None,
                                      validate: bool = True) -> List[TestCase]:
        """
        Generate test cases from exported paths (Stage 3 output).
        
        Args:
            paths_json_file: Path to JSON file from Stage 3
            variations: List of variations to generate ['positive', 'negative', etc.]
            validate: Whether to validate generated test cases
            
        Returns:
            List of TestCase objects
        """
        if variations is None:
            variations = ['positive']
        
        print("="*70)
        print("STAGE 4: LLM-BASED TEST CASE GENERATION")
        print("="*70)
        
        # Load paths from Stage 3
        print(f"\n[1/4] Loading test paths from {paths_json_file}...")
        with open(paths_json_file, 'r') as f:
            data = json.load(f)
        
        paths = data.get('paths', [])
        print(f"  ✓ Loaded {len(paths)} test paths")
        
        # Generate test cases
        print(f"\n[2/4] Generating test cases ({len(variations)} variation(s) per path)...")
        all_test_cases = []
        
        for i, path in enumerate(paths, 1):
            print(f"  Path {i}/{len(paths)}: {path['length']} nodes, risk={path['risk_score']:.3f}")
            
            for variation in variations:
                try:
                    test_case = self.generator.generate_test_case(path, variation)
                    all_test_cases.append(test_case)
                    print(f"    ✓ Generated {variation} test case: {test_case.test_id}")
                except Exception as e:
                    print(f"    ✗ Failed to generate {variation}: {e}")
        
        print(f"\n  ✓ Total test cases generated: {len(all_test_cases)}")
        
        # Validate test cases
        if validate:
            print(f"\n[3/4] Validating test cases...")
            valid_count = 0
            total_quality = 0.0
            
            for tc in all_test_cases:
                is_valid, quality, issues = self.validator.validate_test_case(tc)
                total_quality += quality
                
                if is_valid:
                    valid_count += 1
                else:
                    print(f"  ⚠️ {tc.test_id}: Quality={quality:.1f}%, Issues: {issues}")
            
            avg_quality = total_quality / len(all_test_cases) if all_test_cases else 0
            print(f"  ✓ Valid: {valid_count}/{len(all_test_cases)} ({valid_count/len(all_test_cases)*100:.1f}%)")
            print(f"  ✓ Average quality: {avg_quality:.1f}%")
        
        # Rank test cases
        print(f"\n[4/4] Ranking test cases by importance...")
        ranked_cases = self.validator.rank_test_cases(all_test_cases)
        
        print(f"\n{'='*70}")
        print("GENERATION COMPLETE")
        print(f"{'='*70}")
        print(f"Total test cases: {len(ranked_cases)}")
        print(f"Variations: {', '.join(variations)}")
        
        return ranked_cases
    
    def export_test_cases(self,
                         test_cases: List[TestCase],
                         output_format: str = 'json',
                         output_file: str = 'test_cases.json'):
        """
        Export test cases to file.
        
        Args:
            test_cases: List of TestCase objects
            output_format: 'json', 'markdown', or 'html'
            output_file: Output file path
        """
        print(f"\nExporting {len(test_cases)} test cases to {output_format.upper()}...")
        
        if output_format == 'json':
            with open(output_file, 'w') as f:
                json.dump([tc.to_dict() for tc in test_cases], f, indent=2)
        
        elif output_format == 'markdown':
            with open(output_file, 'w') as f:
                f.write("# Test Cases\n\n")
                for tc in test_cases:
                    f.write(self.formatter.to_markdown(tc))
                    f.write("\n---\n\n")
        
        elif output_format == 'html':
            with open(output_file, 'w') as f:
                f.write("<html><head><style>")
                f.write(self._get_html_styles())
                f.write("</style></head><body>")
                f.write("<h1>Test Cases</h1>")
                for tc in test_cases:
                    f.write(self.formatter.to_html(tc))
                f.write("</body></html>")
        
        print(f"  ✓ Exported to: {output_file}")
    
    def _get_html_styles(self) -> str:
        """Get CSS styles for HTML output"""
        return """
        body { font-family: Arial, sans-serif; margin: 20px; }
        .test-case { border: 1px solid #ddd; padding: 20px; margin-bottom: 20px; }
        .metadata { margin: 10px 0; }
        .metadata span { padding: 5px 10px; margin-right: 10px; border-radius: 3px; }
        .priority { font-weight: bold; }
        .priority.critical { background: #ff4444; color: white; }
        .priority.high { background: #ff8800; color: white; }
        .priority.medium { background: #ffcc00; }
        .priority.low { background: #88cc00; }
        table { width: 100%; border-collapse: collapse; margin: 10px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background: #f0f0f0; font-weight: bold; }
        """
    
    def print_summary(self, test_cases: List[TestCase]):
        """Print summary of generated test cases"""
        print("\n" + "="*70)
        print("TEST CASE SUMMARY")
        print("="*70)
        
        # Count by priority
        priority_counts = {}
        for tc in test_cases:
            priority_counts[tc.priority.value] = priority_counts.get(tc.priority.value, 0) + 1
        
        print("\nBy Priority:")
        for priority, count in priority_counts.items():
            print(f"  {priority}: {count}")
        
        # Count by type
        type_counts = {}
        for tc in test_cases:
            type_counts[tc.test_type.value] = type_counts.get(tc.test_type.value, 0) + 1
        
        print("\nBy Type:")
        for test_type, count in type_counts.items():
            print(f"  {test_type}: {count}")
        
        # Top 5 by risk
        print("\nTop 5 Highest Risk:")
        for i, tc in enumerate(test_cases[:5], 1):
            print(f"  {i}. {tc.test_id}: {tc.title[:50]}... (Risk: {tc.risk_score:.3f})")


if __name__ == "__main__":
    print("Stage 4: LLM-Based Test Case Generation")
    print("This module is imported by the main pipeline.")
