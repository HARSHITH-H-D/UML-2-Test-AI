"""
STAGE 4: LLM-BASED TEST CASE GENERATION (WITH GEMINI API INTEGRATION)

✨ NEW: Google Gemini API integration added
🆓 FREE API - No credit card required

Get your FREE API key: https://makersuite.google.com/app/apikey
"""

# ============================================================================
# 🔑 API KEY CONFIGURATION - CHANGE THIS!
# ============================================================================

# Option 1: Set your API key here directly
GEMINI_API_KEY = "AIzaSyAWG7Pdsv8iiKkzQT0teVF2gOl3e9bvyhw"  # ← REPLACE THIS with your key from https://makersuite.google.com/app/apikey

# Option 2: Or use environment variable (more secure)
import os
# GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')  # Uncomment to use environment variable

# ============================================================================
# IMPORTS
# ============================================================================

import json
import re
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import networkx as nx

# For Gemini API (install with: pip install google-generativeai)
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ google-generativeai not installed. Run: pip install google-generativeai")


# ============================================================================
# PART 1: DATA STRUCTURES (Same as before)
# ============================================================================

class TestCasePriority(Enum):
    """Test case priority levels"""
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class TestCaseType(Enum):
    """Types of test cases"""
    POSITIVE = "Positive"
    NEGATIVE = "Negative"
    BOUNDARY = "Boundary"
    INTEGRATION = "Integration"


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
    
    preconditions: List[str]
    test_steps: List[TestStep]
    expected_results: List[str]
    postconditions: List[str]
    
    risk_score: float
    coverage: float
    path_length: int
    tags: List[str] = field(default_factory=list)
    
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
# PART 2: PROMPT TEMPLATES
# ============================================================================

class PromptTemplates:
    """Templates for LLM prompts"""
    
    @staticmethod
    def generate_test_case_prompt(path_info: Dict, variation: str = "positive") -> str:
        """Generate prompt for Gemini to create test case"""
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

**Output Format (JSON ONLY):**
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


# ============================================================================
# PART 3: LLM TEST CASE GENERATOR (WITH GEMINI INTEGRATION)
# ============================================================================

class LLMTestCaseGenerator:
    """
    Generates test cases using Google Gemini API (FREE)
    
    🔑 API Key Setup:
    1. Get FREE key from: https://makersuite.google.com/app/apikey
    2. Set GEMINI_API_KEY at top of this file
    3. Run: pip install google-generativeai
    """
    
    def __init__(self, use_llm: bool = False, api_key: Optional[str] = None):
        """
        Initialize generator.
        
        Args:
            use_llm: Whether to use Gemini API
            api_key: Your Gemini API key (or set GEMINI_API_KEY global)
        """
        self.use_llm = use_llm
        self.api_key = api_key or GEMINI_API_KEY
        
        # Initialize Gemini if requested
        if use_llm:
            if not GEMINI_AVAILABLE:
                print("❌ google-generativeai not installed!")
                print("   Run: pip install google-generativeai")
                self.use_llm = False
            elif not self.api_key or self.api_key == "YOUR_API_KEY_HERE":
                print("❌ GEMINI_API_KEY not set!")
                print("   Get your FREE key: https://makersuite.google.com/app/apikey")
                print("   Then set it at the top of this file")
                self.use_llm = False
            else:
                try:
                    # Configure Gemini
                    genai.configure(api_key=self.api_key)
                    self.model = genai.GenerativeModel('gemini-pro')
                    self.last_request_time = 0
                    self.min_request_interval = 1.0  # Rate limiting
                    print("✅ Gemini API initialized successfully!")
                    print("   Model: gemini-pro (FREE tier)")
                except Exception as e:
                    print(f"❌ Failed to initialize Gemini: {e}")
                    self.use_llm = False
        
        if not self.use_llm:
            print("ℹ️  Using template-based generation (no API)")
    
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
            return self._generate_with_gemini(path_info, variation)
        else:
            return self._generate_with_template(path_info, variation)
    
    def _generate_with_gemini(self, path_info: Dict, variation: str) -> TestCase:
        """
        🆓 Generate test case using FREE Gemini API
        
        This is where the magic happens!
        """
        # Rate limiting (respect free tier: 60 requests/minute)
        self._rate_limit()
        
        # Generate prompt
        prompt = PromptTemplates.generate_test_case_prompt(path_info, variation)
        
        try:
            # 🚀 Call Gemini API
            print(f"  🤖 Calling Gemini API for {variation} test case...")
            response = self.model.generate_content(prompt)
            
            # Extract JSON from response
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()
            
            # Parse JSON
            test_case_data = json.loads(response_text)
            
            # Build TestCase object
            return self._build_test_case_from_json(test_case_data, path_info, variation)
            
        except Exception as e:
            print(f"  ⚠️  Gemini API error: {e}")
            print(f"  ℹ️  Falling back to template-based generation...")
            return self._generate_with_template(path_info, variation)
    
    def _rate_limit(self):
        """Respect API rate limits (60/minute for free tier)"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _build_test_case_from_json(self, data: Dict, path_info: Dict, variation: str) -> TestCase:
        """Build TestCase object from Gemini's JSON response"""
        # Determine priority
        risk_score = path_info['risk_score']
        if risk_score > 0.8:
            priority = TestCasePriority.CRITICAL
        elif risk_score > 0.6:
            priority = TestCasePriority.HIGH
        elif risk_score > 0.4:
            priority = TestCasePriority.MEDIUM
        else:
            priority = TestCasePriority.LOW
        
        # Determine test type
        test_type_map = {
            'positive': TestCaseType.POSITIVE,
            'negative': TestCaseType.NEGATIVE,
            'boundary': TestCaseType.BOUNDARY,
            'integration': TestCaseType.INTEGRATION
        }
        test_type = test_type_map.get(variation, TestCaseType.POSITIVE)
        
        # Generate test ID
        test_id = f"TC-{path_info['priority']:03d}-{variation[:3].upper()}-{hash(str(path_info['nodes'])) % 1000:03d}"
        
        # Build test steps
        test_steps = []
        for step_data in data.get('test_steps', []):
            test_steps.append(TestStep(
                step_number=step_data['step'],
                action=step_data['action'],
                expected_result=step_data['expected'],
                notes=step_data.get('notes')
            ))
        
        return TestCase(
            test_id=test_id,
            title=data['title'],
            description=data['description'],
            priority=priority,
            test_type=test_type,
            preconditions=data.get('preconditions', []),
            test_steps=test_steps,
            expected_results=data.get('expected_results', []),
            postconditions=data.get('postconditions', []),
            risk_score=risk_score,
            coverage=path_info['coverage'],
            path_length=path_info['length'],
            tags=data.get('tags', []),
            test_data=data.get('test_data'),
            notes=f"✨ Generated by Gemini AI (variation: {variation})"
        )
    
    def _generate_with_template(self, path_info: Dict, variation: str) -> TestCase:
        """
        Template-based test case generation (fallback)
        """
        # ... (Keep all the existing template code from the original file)
        # This is the same as before - I'll keep it for brevity
        nodes = path_info['nodes']
        priority = path_info['priority']
        risk_score = path_info['risk_score']
        
        if risk_score > 0.8:
            priority_level = TestCasePriority.CRITICAL
        elif risk_score > 0.6:
            priority_level = TestCasePriority.HIGH
        elif risk_score > 0.4:
            priority_level = TestCasePriority.MEDIUM
        else:
            priority_level = TestCasePriority.LOW
        
        test_type_map = {
            'positive': TestCaseType.POSITIVE,
            'negative': TestCaseType.NEGATIVE,
            'boundary': TestCaseType.BOUNDARY,
            'integration': TestCaseType.INTEGRATION
        }
        test_type = test_type_map.get(variation, TestCaseType.POSITIVE)
        
        test_id = f"TC-{priority:03d}-{variation[:3].upper()}-{hash(str(nodes)) % 1000:03d}"
        
        actors = [n for n in nodes if n['type'] == 'actor']
        usecases = [n for n in nodes if n['type'] == 'usecase']
        classes = [n for n in nodes if n['type'] == 'class']
        
        if usecases:
            main_flow = " → ".join([uc['name'] for uc in usecases[:3]])
            if len(usecases) > 3:
                main_flow += " → ..."
            title = f"Verify {main_flow}"
        else:
            title = f"Test path with {len(nodes)} components"
        
        if actors:
            actor_name = actors[0]['name']
            description = f"Verify that {actor_name} can successfully execute the workflow: {main_flow}"
        else:
            description = f"Verify the execution flow through {len(nodes)} components"
        
        preconditions = []
        if actors:
            preconditions.append(f"{actors[0]['name']} has valid credentials and permissions")
        preconditions.append("System is in stable state")
        preconditions.append("All required services are running")
        if classes:
            preconditions.append(f"{classes[0]['name']} is properly initialized")
        
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
        
        expected_results = [
            "All steps complete without errors",
            "System remains in consistent state",
            "Expected outputs are produced"
        ]
        if usecases:
            expected_results.append(f"Workflow completes: {' → '.join([uc['name'] for uc in usecases])}")
        
        postconditions = [
            "System returns to stable state",
            "All resources are properly released",
            "Audit logs are updated correctly"
        ]
        
        tags = [node['name'] for node in usecases[:3]]
        tags.append(variation)
        if risk_score > 0.6:
            tags.append('high-risk')
        
        test_data = {
            'username': 'test_user',
            'password': 'Test@1234',
            'environment': 'test'
        }
        
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


# ============================================================================
# PART 4 & 5: VALIDATOR & FORMATTER (Keep same as original)
# ============================================================================

# (Include the rest of the original code: TestCaseValidator, TestCaseFormatter, etc.)
# ... (keeping for brevity - use the rest from your original file)

print("="*70)
print("Stage 4 Module Loaded with Gemini API Support")
print("="*70)
if GEMINI_AVAILABLE:
    print("✅ google-generativeai installed")
else:
    print("⚠️  google-generativeai NOT installed")
    print("   Install with: pip install google-generativeai")

if GEMINI_API_KEY and GEMINI_API_KEY != "YOUR_API_KEY_HERE":
    print("✅ API key configured")
else:
    print("⚠️  API key NOT set - using template mode")
    print("   Get FREE key: https://makersuite.google.com/app/apikey")
print("="*70)