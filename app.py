"""
🚀 PLANTUML → AI TEST CASE GENERATOR
Streamlit App — Complete 4-Stage Pipeline
"""

import streamlit as st
import os, re, json, time, heapq, io, tempfile, zipfile
import requests
import numpy as np
import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
import pandas as pd
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple, Optional
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, HRFlowable)
from reportlab.lib.units import inch

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="UML2Test AI",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Syne', sans-serif; }

/* ── Hero Banner ── */
.hero {
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    border-radius: 16px;
    padding: 36px 40px;
    margin-bottom: 28px;
    color: white;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: '';
    position: absolute; inset: 0;
    background: radial-gradient(ellipse at 70% 50%, rgba(99,102,241,.35) 0%, transparent 70%);
}
.hero h1 { font-size: 2.2rem; font-weight: 800; margin: 0 0 6px; position:relative; }
.hero p  { font-size: 1rem; opacity: .75; margin: 0; position: relative; }
.hero .badge {
    display: inline-block;
    background: rgba(255,255,255,.12);
    border: 1px solid rgba(255,255,255,.2);
    border-radius: 20px;
    padding: 3px 12px;
    font-size: .75rem;
    margin: 10px 4px 0 0;
    position: relative;
}

/* ── Stage Cards ── */
.stage-card {
    background: #1e1e2e;
    border: 1px solid #2d2d44;
    border-radius: 12px;
    padding: 18px 20px;
    margin-bottom: 14px;
    color: #cdd6f4;
}
.stage-card h4 { margin: 0 0 6px; color: #cba6f7; font-size: .95rem; font-family: 'JetBrains Mono'; }
.stage-card p  { margin: 0; font-size: .82rem; opacity: .75; }

/* ── Metric Pills ── */
.metric-row { display: flex; gap: 12px; flex-wrap: wrap; margin: 14px 0; }
.metric-pill {
    background: #1e1e2e;
    border: 1px solid #313244;
    border-radius: 8px;
    padding: 10px 18px;
    text-align: center;
    min-width: 100px;
    flex: 1;
}
.metric-pill .num { font-size: 1.6rem; font-weight: 800; color: #cba6f7; font-family:'JetBrains Mono'; }
.metric-pill .lbl { font-size: .72rem; color: #6c7086; text-transform: uppercase; letter-spacing: .05em; }

/* ── Priority Badges ── */
.p-critical { background:#ff5555; color:white; padding:2px 9px; border-radius:12px; font-size:.72rem; font-weight:700; }
.p-high     { background:#ff8800; color:white; padding:2px 9px; border-radius:12px; font-size:.72rem; font-weight:700; }
.p-medium   { background:#f1c40f; color:#111;  padding:2px 9px; border-radius:12px; font-size:.72rem; font-weight:700; }
.p-low      { background:#50fa7b; color:#111;  padding:2px 9px; border-radius:12px; font-size:.72rem; font-weight:700; }
.t-positive    { background:#6272a4; color:white; padding:2px 9px; border-radius:12px; font-size:.72rem; }
.t-negative    { background:#ff5555; color:white; padding:2px 9px; border-radius:12px; font-size:.72rem; }
.t-boundary    { background:#bd93f9; color:white; padding:2px 9px; border-radius:12px; font-size:.72rem; }
.t-integration { background:#50fa7b; color:#111;  padding:2px 9px; border-radius:12px; font-size:.72rem; }

/* ── Test Case Card ── */
.tc-card {
    background: #1e1e2e;
    border: 1px solid #313244;
    border-left: 4px solid #cba6f7;
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 14px;
    color: #cdd6f4;
}
.tc-card .tc-id   { font-family:'JetBrains Mono'; font-size:.8rem; color:#6272a4; }
.tc-card .tc-title{ font-size:1rem; font-weight:700; margin:4px 0 8px; }
.tc-card .tc-desc { font-size:.85rem; color:#a6adc8; margin-bottom:10px; }
.tc-meta { font-size:.75rem; color:#6c7086; margin-top:10px; }

/* ── Download Buttons ── */
.stDownloadButton > button {
    background: linear-gradient(135deg, #cba6f7, #89b4fa) !important;
    color: #1e1e2e !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 10px 20px !important;
    font-family: 'Syne', sans-serif !important;
    transition: opacity .2s !important;
}
.stDownloadButton > button:hover { opacity: .85 !important; }

/* ── Progress / Spinner ── */
.stProgress > div > div { background: linear-gradient(90deg, #cba6f7, #89b4fa); }

/* ── File Uploader ── */
.stFileUploader { background: #1e1e2e; border-radius: 12px; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] { background: #181825; }
section[data-testid="stSidebar"] * { color: #cdd6f4; }

/* ── Expander ── */
.streamlit-expanderHeader { background: #1e1e2e; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
HF_API_URL = "https://router.huggingface.co/v1/chat/completions"
MODEL      = "meta-llama/Llama-3.1-8B-Instruct"

# ── API KEY — Set your Hugging Face key here (programmer config only) ──────
HF_API_KEY = "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"   # ← Replace with your actual key

# ─────────────────────────────────────────────────────────────────────────────
# DATA CLASSES
# ─────────────────────────────────────────────────────────────────────────────
class TestCasePriority(Enum):
    CRITICAL = "Critical"
    HIGH     = "High"
    MEDIUM   = "Medium"
    LOW      = "Low"

class TestCaseType(Enum):
    POSITIVE    = "Positive"
    NEGATIVE    = "Negative"
    BOUNDARY    = "Boundary"
    INTEGRATION = "Integration"

@dataclass
class TestStep:
    step_number: int
    action: str
    expected_result: str
    notes: Optional[str] = None

@dataclass
class TestCase:
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
    source_file: str = ""
    tags: List[str] = field(default_factory=list)
    test_data: Optional[Dict] = None
    notes: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "test_id": self.test_id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "test_type": self.test_type.value,
            "source_file": self.source_file,
            "preconditions": self.preconditions,
            "test_steps": [
                {"step": s.step_number, "action": s.action, "expected": s.expected_result}
                for s in self.test_steps
            ],
            "expected_results": self.expected_results,
            "postconditions": self.postconditions,
            "metadata": {
                "risk_score": self.risk_score,
                "coverage": self.coverage,
                "path_length": self.path_length,
            },
            "tags": self.tags,
            "notes": self.notes,
        }

@dataclass
class TestPath:
    priority: int
    risk_score: float
    length: int
    nodes: List[Dict]
    edges: List[Tuple[str, str]]
    coverage: float

    def to_dict(self) -> Dict:
        return {
            "priority": self.priority, "risk_score": self.risk_score,
            "length": self.length,     "nodes": self.nodes,
            "edges": self.edges,       "coverage": self.coverage,
        }

# ─────────────────────────────────────────────────────────────────────────────
# STAGE 1 — PARSER
# ─────────────────────────────────────────────────────────────────────────────
class PlantUMLParser:
    def __init__(self):
        self.actors = []; self.usecases = []; self.classes = []; self.relations = []
        self.node_counter = 0

    def parse_content(self, content: str) -> Dict:
        self._parse_actors(content)
        self._parse_usecases(content)
        self._parse_classes(content)
        self._parse_relations(content)
        self._correct_edge_directions()
        return {"actors": self.actors, "usecases": self.usecases,
                "classes": self.classes, "relations": self.relations}

    def _get_next_id(self) -> str:
        nid = f"N{self.node_counter}"; self.node_counter += 1; return nid

    def _parse_actors(self, c):
        for name, alias in re.findall(r'actor\s+"([^"]+)"(?:\s+as\s+(\w+))?', c):
            self.actors.append({"id": self._get_next_id(), "name": name,
                                 "alias": alias or name, "type": "actor"})
        for name in re.findall(r'actor\s+(\w+)(?!\s+as)', c):
            if not any(a["name"] == name for a in self.actors):
                self.actors.append({"id": self._get_next_id(), "name": name,
                                     "alias": name, "type": "actor"})

    def _parse_usecases(self, c):
        for name, alias in re.findall(r'usecase\s+"([^"]+)"(?:\s+as\s+(\w+))?', c):
            self.usecases.append({"id": self._get_next_id(), "name": name,
                                   "alias": alias or name, "type": "usecase"})
        for name in re.findall(r'usecase\s+(\w+)(?!\s+as)', c):
            if not any(u["name"] == name for u in self.usecases):
                self.usecases.append({"id": self._get_next_id(), "name": name,
                                       "alias": name, "type": "usecase"})

    def _parse_classes(self, c):
        for name in re.findall(r'class\s+(\w+)', c):
            if not any(cl["name"] == name for cl in self.classes):
                self.classes.append({"id": self._get_next_id(), "name": name,
                                      "alias": name, "type": "class"})

    def _parse_relations(self, c):
        patterns = [
            (r'(\w+)\s*-->\s*(\w+)', "association"),
            (r'(\w+)\s*\.\.\s*>\s*(\w+)', "include"),
            (r'(\w+)\s*<\.\.\s*(\w+)', "extend"),
        ]
        for pattern, rel_type in patterns:
            for src, tgt in re.findall(pattern, c):
                if not any(r["source"] == src and r["target"] == tgt
                           for r in self.relations):
                    self.relations.append({"source": src, "target": tgt,
                                           "type": rel_type})

    def _correct_edge_directions(self):
        all_aliases = (
            {a["alias"] for a in self.actors} |
            {u["alias"] for u in self.usecases} |
            {cl["alias"] for cl in self.classes}
        )
        actor_aliases = {a["alias"] for a in self.actors}
        corrected = []
        for r in self.relations:
            if r["source"] in all_aliases and r["target"] in all_aliases:
                if r["target"] in actor_aliases and r["source"] not in actor_aliases:
                    r["source"], r["target"] = r["target"], r["source"]
                corrected.append(r)
        self.relations = corrected

# ─────────────────────────────────────────────────────────────────────────────
# STAGE 2 — GRAPH BUILDER
# ─────────────────────────────────────────────────────────────────────────────
class UnifiedGraphBuilder:
    def __init__(self):
        self.graph = nx.DiGraph(); self.node_map = {}

    def build_graph(self, parsed_data: Dict) -> nx.DiGraph:
        for node_list in [parsed_data["actors"], parsed_data["usecases"],
                          parsed_data["classes"]]:
            for n in node_list:
                self.graph.add_node(n["id"], **n)
                self.node_map[n["alias"]] = n["id"]
        for rel in parsed_data["relations"]:
            src = self.node_map.get(rel["source"])
            tgt = self.node_map.get(rel["target"])
            if src and tgt:
                self.graph.add_edge(src, tgt, type=rel["type"], weight=1.0)
        return self.graph

    def visualize(self) -> plt.Figure:
        fig, ax = plt.subplots(figsize=(10, 7))
        fig.patch.set_facecolor("#1e1e2e")
        ax.set_facecolor("#1e1e2e")
        pos = nx.spring_layout(self.graph, k=2.5, iterations=80, seed=42)

        colors_map = {"actor": "#89b4fa", "usecase": "#a6e3a1", "class": "#fab387"}
        shapes_map = {"actor": "s",       "usecase": "o",        "class": "^"}

        for ntype, shape in shapes_map.items():
            nodes = [n for n, d in self.graph.nodes(data=True) if d.get("type") == ntype]
            nx.draw_networkx_nodes(self.graph, pos, nodelist=nodes,
                                   node_color=colors_map[ntype], node_size=900,
                                   node_shape=shape, ax=ax, alpha=.9)

        nx.draw_networkx_edges(self.graph, pos, edge_color="#6c7086",
                               arrows=True, arrowsize=18, width=1.5, ax=ax,
                               connectionstyle="arc3,rad=0.05")
        labels = {n: d["name"] for n, d in self.graph.nodes(data=True)}
        nx.draw_networkx_labels(self.graph, pos, labels,
                                font_size=7, font_color="#cdd6f4", ax=ax)

        from matplotlib.patches import Patch
        legend = [Patch(color="#89b4fa", label="Actor"),
                  Patch(color="#a6e3a1", label="Use Case"),
                  Patch(color="#fab387", label="Class")]
        ax.legend(handles=legend, facecolor="#313244", edgecolor="#45475a",
                  labelcolor="#cdd6f4", fontsize=8, loc="upper left")
        ax.set_title("UML Dependency Graph", color="#cba6f7",
                     fontsize=13, fontweight="bold", pad=12)
        ax.axis("off")
        plt.tight_layout()
        return fig

# ─────────────────────────────────────────────────────────────────────────────
# STAGE 3 — RISK & PATH GENERATOR
# ─────────────────────────────────────────────────────────────────────────────
class SimpleGNN(nn.Module):
    def __init__(self, input_dim=10, hidden_dim=16):
        super().__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        return self.sigmoid(self.fc2(torch.relu(self.fc1(x))))

class RiskPredictor:
    def __init__(self, graph: nx.DiGraph):
        self.graph = graph; self.model = SimpleGNN(); self.risk_scores = {}

    def predict_risks(self) -> Dict[str, float]:
        for node in self.graph.nodes():
            feats = self._features(node)
            with torch.no_grad():
                self.risk_scores[node] = self.model(
                    torch.FloatTensor(feats).unsqueeze(0)).item()
        return self.risk_scores

    def _features(self, node) -> List[float]:
        ntype = self.graph.nodes[node].get("type", "usecase")
        enc = {"actor": [1,0,0], "usecase": [0,1,0], "class": [0,0,1]}.get(ntype, [0,0,0])
        ideg, odeg = self.graph.in_degree(node), self.graph.out_degree(node)
        total = ideg + odeg
        enc += [ideg/(total+1), odeg/(total+1), total/max(len(self.graph),1),
                .5, .5, len(list(self.graph.neighbors(node)))/max(len(self.graph),1)]
        while len(enc) < 10: enc.append(0.0)
        return enc[:10]

class RiskGuidedAStar:
    def __init__(self, graph: nx.DiGraph, risk_scores: Dict[str, float]):
        self.graph = graph; self.risk_scores = risk_scores

    def find_paths(self, start, goal, num_paths=3):
        all_paths, visited = [], set()
        for _ in range(num_paths * 3):
            p = self._astar(start, goal, visited)
            if p and len(p) > 1:
                pt = tuple(p)
                if pt not in visited:
                    all_paths.append(p); visited.add(pt)
                    if len(all_paths) >= num_paths: break
        return all_paths

    def _astar(self, start, goal, avoid):
        frontier = [(0, 0, start, [start])]; visited = set()
        while frontier:
            f, g, cur, path = heapq.heappop(frontier)
            if cur == goal: return path
            if cur in visited or len(path) >= 10: continue
            visited.add(cur)
            for nb in self.graph.successors(cur):
                if nb not in path:
                    np_ = path + [nb]; ng = g + 1
                    h = self._h(nb, goal, np_)
                    heapq.heappush(frontier, (ng+h, ng, nb, np_))
        return None

    def _h(self, node, goal, path):
        r = self.risk_scores.get(node, .5)
        return (1 - r) + len(path) * .1

class TestPathGenerator:
    def __init__(self, graph: nx.DiGraph, risk_scores: Dict[str, float]):
        self.graph = graph; self.risk_scores = risk_scores

    def generate_paths(self, num_paths=10) -> List[TestPath]:
        nodes = list(self.graph.nodes())
        if len(nodes) < 2: return self._fallback_paths(num_paths)
        astar = RiskGuidedAStar(self.graph, self.risk_scores)
        all_raw, seen = [], set()
        for start in nodes:
            for end in nodes:
                if start != end:
                    for p in astar.find_paths(start, end, 2):
                        pt = tuple(p)
                        if pt not in seen:
                            seen.add(pt); all_raw.append(p)
        all_raw.sort(
            key=lambda p: -sum(self.risk_scores.get(n, .5) for n in p)/max(len(p),1))
        paths = []
        for i, raw in enumerate(all_raw[:num_paths], 1):
            node_data = [dict(self.graph.nodes[n]) for n in raw]
            edges = list(zip(raw[:-1], raw[1:]))
            avg_risk = sum(self.risk_scores.get(n, .5) for n in raw) / len(raw)
            cov = len(set(raw)) / max(len(self.graph), 1)
            paths.append(TestPath(priority=i, risk_score=avg_risk,
                                  length=len(raw), nodes=node_data,
                                  edges=edges, coverage=cov))
        return paths if paths else self._fallback_paths(num_paths)

    def _fallback_paths(self, n) -> List[TestPath]:
        nodes_list = [dict(self.graph.nodes[nd]) for nd in list(self.graph.nodes())[:3]]
        if not nodes_list: nodes_list = [{"id":"N0","name":"System","type":"usecase"}]
        return [TestPath(priority=i+1, risk_score=.5+i*.05, length=len(nodes_list),
                         nodes=nodes_list, edges=[], coverage=.3)
                for i in range(min(n, 3))]

# ─────────────────────────────────────────────────────────────────────────────
# STAGE 4 — AI TEST CASE GENERATOR
# ─────────────────────────────────────────────────────────────────────────────
class Llama31APIClient:
    def __init__(self, api_key: str):
        self.api_key = api_key; self.last_req = 0

    def generate(self, prompt: str, max_tokens=2000) -> str:
        elapsed = time.time() - self.last_req
        if elapsed < 0.5: time.sleep(0.5 - elapsed)
        messages = [
            {"role": "system",
             "content": "You are an expert software testing engineer. Generate detailed test cases in valid JSON format only."},
            {"role": "user", "content": prompt},
        ]
        for attempt in range(3):
            try:
                r = requests.post(HF_API_URL,
                    headers={"Authorization": f"Bearer {self.api_key}",
                             "Content-Type": "application/json"},
                    json={"messages": messages, "model": MODEL,
                          "max_tokens": max_tokens, "temperature": 0.7},
                    timeout=120)
                self.last_req = time.time()
                if r.status_code == 503:
                    if attempt < 2: time.sleep(20); continue
                if r.status_code == 200:
                    return r.json()["choices"][0]["message"]["content"]
                raise Exception(f"API {r.status_code}: {r.text[:200]}")
            except Exception as e:
                if attempt < 2: time.sleep(5)
                else: raise
        raise Exception("Failed after 3 attempts")

class TestCaseGenerator:
    def __init__(self, api_key: str = None):
        self.use_ai = False
        if api_key and api_key.startswith("hf_"):
            try:
                self.api = Llama31APIClient(api_key); self.use_ai = True
            except: pass

    def generate(self, path_info: Dict, variation: str,
                 source_file: str = "") -> TestCase:
        tc = (self._generate_with_ai(path_info, variation)
              if self.use_ai else self._generate_template(path_info, variation))
        tc.source_file = source_file
        return tc

    def _generate_with_ai(self, path_info, variation) -> TestCase:
        try:
            nodes_desc = " → ".join(
                f"{n['name']} ({n['type']})" for n in path_info["nodes"])
            prompt = f"""Generate a test case in JSON format.

Path: {nodes_desc}
Priority: {path_info['priority']}
Risk: {path_info['risk_score']:.3f}
Type: {variation.title()}

Required JSON:
{{
  "title": "Test title",
  "description": "Description",
  "preconditions": ["condition 1"],
  "test_steps": [{{"step": 1, "action": "action", "expected": "result"}}],
  "expected_results": ["result 1"],
  "postconditions": ["state 1"],
  "test_data": {{"key": "value"}},
  "tags": ["tag1"]
}}

Generate ONLY valid JSON (no markdown, no backticks):"""
            raw = self.api.generate(prompt)
            raw = raw.strip()
            if "```json" in raw: raw = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw:   raw = raw.split("```")[1].split("```")[0].strip()
            data = json.loads(raw)
            return self._from_json(data, path_info, variation)
        except Exception:
            return self._generate_template(path_info, variation)

    def _from_json(self, data, path_info, variation) -> TestCase:
        priority = self._risk_to_priority(path_info["risk_score"])
        test_type = {"positive": TestCaseType.POSITIVE,
                     "negative": TestCaseType.NEGATIVE,
                     "boundary": TestCaseType.BOUNDARY,
                     "integration": TestCaseType.INTEGRATION
                     }.get(variation, TestCaseType.POSITIVE)
        tid = (f"TC-{path_info['priority']:03d}-{variation[:3].upper()}-"
               f"{abs(hash(str(path_info['nodes']))) % 1000:03d}")
        steps = [TestStep(s["step"], s["action"], s["expected"])
                 for s in data.get("test_steps", [])]
        return TestCase(
            test_id=tid, title=data.get("title", "Test Case"),
            description=data.get("description", ""),
            priority=priority, test_type=test_type,
            preconditions=data.get("preconditions", []),
            test_steps=steps,
            expected_results=data.get("expected_results", []),
            postconditions=data.get("postconditions", []),
            risk_score=path_info["risk_score"], coverage=path_info["coverage"],
            path_length=path_info["length"],
            tags=data.get("tags", []), test_data=data.get("test_data"),
            notes=f"✨ AI-Generated by Llama 3.1 ({variation})")

    def _generate_template(self, path_info, variation) -> TestCase:
        nodes = path_info["nodes"]; risk = path_info["risk_score"]
        priority = self._risk_to_priority(risk)
        test_type = {"positive": TestCaseType.POSITIVE,
                     "negative": TestCaseType.NEGATIVE
                     }.get(variation, TestCaseType.POSITIVE)
        tid = (f"TC-{path_info['priority']:03d}-{variation[:3].upper()}-"
               f"{abs(hash(str(nodes))) % 1000:03d}")
        title = f"Test {' → '.join(n['name'] for n in nodes[:3])}"
        steps = [TestStep(i, f"Execute: {n['name']}",
                          f"{n['name']} completes successfully")
                 for i, n in enumerate(nodes, 1)]
        pos_neg = ("All steps succeed" if variation == "positive"
                   else "System handles error gracefully")
        return TestCase(
            test_id=tid, title=title,
            description=f"Verify {variation} flow through {len(nodes)} components",
            priority=priority, test_type=test_type,
            preconditions=["System is operational", "Valid user credentials available",
                           "Test environment is configured"],
            test_steps=steps,
            expected_results=[pos_neg, "No data corruption occurs", "Logs are updated"],
            postconditions=["System returns to stable state", "Session is cleaned up"],
            risk_score=risk, coverage=path_info["coverage"],
            path_length=path_info["length"],
            tags=[variation, priority.value.lower()],
            test_data={"username": "test_user", "environment": "staging"},
            notes=f"Template-generated ({variation})")

    @staticmethod
    def _risk_to_priority(risk: float) -> TestCasePriority:
        if risk > .8: return TestCasePriority.CRITICAL
        if risk > .6: return TestCasePriority.HIGH
        if risk > .4: return TestCasePriority.MEDIUM
        return TestCasePriority.LOW

# ─────────────────────────────────────────────────────────────────────────────
# PERCENTILE-BASED PRIORITY ASSIGNMENT
# ─────────────────────────────────────────────────────────────────────────────
def assign_priorities_by_percentile(test_cases: List[TestCase]) -> List[TestCase]:
    """
    Re-assigns priority based on where each test case's GNN risk score sits
    relative to the full distribution — not fixed absolute thresholds.

    The GNN scores are used as-is for ranking (their relative ordering is
    fully preserved). Only the final label (Critical/High/Medium/Low) is
    determined by quartile position, guaranteeing an even spread across
    all four bands regardless of how clustered the raw GNN outputs are.

        Top 25%    → Critical
        50–75th %  → High
        25–50th %  → Medium
        Bottom 25% → Low
    """
    if not test_cases:
        return test_cases

    scores = np.array([tc.risk_score for tc in test_cases])
    p75 = np.percentile(scores, 75)
    p50 = np.percentile(scores, 50)
    p25 = np.percentile(scores, 25)

    for tc in test_cases:
        if tc.risk_score >= p75:
            tc.priority = TestCasePriority.CRITICAL
        elif tc.risk_score >= p50:
            tc.priority = TestCasePriority.HIGH
        elif tc.risk_score >= p25:
            tc.priority = TestCasePriority.MEDIUM
        else:
            tc.priority = TestCasePriority.LOW

    return test_cases

# ─────────────────────────────────────────────────────────────────────────────
# EXPORT HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def export_json(test_cases: List[TestCase]) -> bytes:
    data = {
        "metadata": {
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_test_cases": len(test_cases),
            "generator": "PlantUML → AI Test Case Generator",
        },
        "test_cases": [tc.to_dict() for tc in test_cases],
    }
    return json.dumps(data, indent=2).encode("utf-8")

def export_csv(test_cases: List[TestCase]) -> bytes:
    rows = []
    for tc in test_cases:
        rows.append({
            "Test ID": tc.test_id,
            "Title": tc.title,
            "Description": tc.description,
            "Priority": tc.priority.value,
            "Type": tc.test_type.value,
            "Source File": tc.source_file,
            "Risk Score": round(tc.risk_score, 3),
            "Coverage": f"{tc.coverage:.1%}",
            "Path Length": tc.path_length,
            "Preconditions": " | ".join(tc.preconditions),
            "Test Steps": " | ".join(
                f"{s.step_number}. {s.action} → {s.expected_result}"
                for s in tc.test_steps),
            "Expected Results": " | ".join(tc.expected_results),
            "Postconditions": " | ".join(tc.postconditions),
            "Tags": ", ".join(tc.tags),
            "Notes": tc.notes or "",
        })
    return pd.DataFrame(rows).to_csv(index=False).encode("utf-8")

def export_pdf(test_cases: List[TestCase]) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=.65*inch, rightMargin=.65*inch,
                            topMargin=.75*inch, bottomMargin=.65*inch)
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("H1", parent=styles["Title"], fontSize=20,
                         textColor=colors.HexColor("#6c63ff"), spaceAfter=4)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=11,
                         textColor=colors.HexColor("#4a4a8a"), spaceAfter=4)
    body = ParagraphStyle("Body", parent=styles["Normal"], fontSize=8.5,
                           leading=12, spaceAfter=3)
    story = [
        Paragraph("🧪 AI-Generated Test Cases", h1),
        Paragraph(
            f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}  |  "
            f"Total: {len(test_cases)} test cases",
            ParagraphStyle("Meta", parent=styles["Normal"],
                           fontSize=8, textColor=colors.grey)),
        Spacer(1, .25*inch),
    ]
    p_colors = {
        "Critical": colors.HexColor("#ff5555"),
        "High":     colors.HexColor("#ff8800"),
        "Medium":   colors.HexColor("#f1c40f"),
        "Low":      colors.HexColor("#50fa7b"),
    }
    for tc in test_cases:
        pc = p_colors.get(tc.priority.value, colors.grey)
        hdr = [[
            Paragraph(f"<b>{tc.test_id}</b>", body),
            Paragraph(f"<b>{tc.title}</b>", body),
            Paragraph(tc.priority.value, body),
            Paragraph(tc.test_type.value, body),
            Paragraph(tc.source_file, body),
        ]]
        ht = Table(hdr, colWidths=[1.1*inch, 2.6*inch, .8*inch, .9*inch, 1.1*inch])
        ht.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), pc),
            ("TEXTCOLOR",  (0,0), (-1,0), colors.white
             if tc.priority.value not in ("Medium","Low") else colors.black),
            ("FONTSIZE",   (0,0), (-1,0), 8),
            ("GRID",       (0,0), (-1,-1), .4, colors.lightgrey),
            ("PADDING",    (0,0), (-1,-1), 5),
            ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
        ]))
        story.append(ht)
        story.append(Paragraph(tc.description, body))
        story.append(Spacer(1, .05*inch))

        if tc.preconditions:
            story.append(Paragraph("<b>Preconditions:</b>", body))
            for p in tc.preconditions:
                story.append(Paragraph(f"&nbsp;&nbsp;• {p}", body))

        if tc.test_steps:
            story.append(Paragraph("<b>Test Steps:</b>", body))
            step_data = [["#", "Action", "Expected Result"]] + [
                [str(s.step_number), s.action, s.expected_result]
                for s in tc.test_steps]
            st_table = Table(step_data,
                             colWidths=[.35*inch, 3.15*inch, 3.0*inch])
            st_table.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#4472C4")),
                ("TEXTCOLOR",  (0,0), (-1,0), colors.white),
                ("FONTSIZE",   (0,0), (-1,-1), 7.5),
                ("GRID",       (0,0), (-1,-1), .3, colors.HexColor("#dddddd")),
                ("PADDING",    (0,0), (-1,-1), 4),
                ("ROWBACKGROUNDS", (0,1), (-1,-1),
                 [colors.white, colors.HexColor("#eef2ff")]),
                ("VALIGN",     (0,0), (-1,-1), "TOP"),
            ]))
            story.append(st_table)
            story.append(Spacer(1, .05*inch))

        if tc.expected_results:
            story.append(Paragraph("<b>Expected Results:</b>", body))
            for r in tc.expected_results:
                story.append(Paragraph(f"&nbsp;&nbsp;✓ {r}", body))

        meta_txt = (f"Risk: {tc.risk_score:.3f}  |  "
                    f"Coverage: {tc.coverage:.1%}  |  "
                    f"Path Length: {tc.path_length}  |  "
                    f"Tags: {', '.join(tc.tags)}")
        story.append(Paragraph(
            f"<font size=7 color='#888888'>{meta_txt}</font>",
            ParagraphStyle("meta", parent=styles["Normal"], fontSize=7)))
        story.append(HRFlowable(width="100%", thickness=.5,
                                color=colors.HexColor("#cccccc")))
        story.append(Spacer(1, .12*inch))

    doc.build(story)
    return buf.getvalue()

def export_html(test_cases: List[TestCase]) -> bytes:
    p_colors = {"Critical": "#ff5555", "High": "#ff8800",
                "Medium": "#f1c40f",   "Low":  "#50fa7b"}
    t_colors = {"Positive": "#6272a4", "Negative": "#ff5555",
                "Boundary": "#bd93f9", "Integration": "#50fa7b"}

    # Summary stats
    by_priority = {k: sum(1 for tc in test_cases if tc.priority.value == k)
                   for k in ["Critical","High","Medium","Low"]}
    by_type = {k: sum(1 for tc in test_cases if tc.test_type.value == k)
               for k in ["Positive","Negative","Boundary","Integration"]}

    stats_html = "".join(
        f'<div class="stat"><div class="stat-num" style="color:{p_colors[k]}">'
        f'{v}</div><div class="stat-lbl">{k}</div></div>'
        for k, v in by_priority.items())

    cards = ""
    for tc in test_cases:
        pc = p_colors.get(tc.priority.value, "#888")
        tc_color = t_colors.get(tc.test_type.value, "#888")
        text_col = "white" if tc.priority.value not in ("Medium","Low") else "#111"

        steps_rows = "".join(
            f"<tr><td>{s.step_number}</td><td>{s.action}</td>"
            f"<td>{s.expected_result}</td></tr>"
            for s in tc.test_steps)
        preconds = "".join(f"<li>{p}</li>" for p in tc.preconditions)
        results  = "".join(f"<li>{r}</li>" for r in tc.expected_results)
        postconds= "".join(f"<li>{p}</li>" for p in tc.postconditions)
        tags_html = "".join(
            f'<span class="tag">{t}</span>' for t in tc.tags)

        cards += f"""
<div class="card" data-priority="{tc.priority.value}" data-type="{tc.test_type.value}"
     data-source="{tc.source_file}">
  <div class="card-header" style="border-left-color:{pc}">
    <div class="header-top">
      <span class="tc-id">{tc.test_id}</span>
      <span class="badge" style="background:{pc};color:{text_col}">{tc.priority.value}</span>
      <span class="badge" style="background:{tc_color};color:white">{tc.test_type.value}</span>
      <span class="src-badge">{tc.source_file}</span>
    </div>
    <div class="tc-title">{tc.title}</div>
    <div class="tc-desc">{tc.description}</div>
    <div class="tags">{tags_html}</div>
  </div>
  <div class="card-body">
    <div class="section">
      <div class="section-title">📋 Preconditions</div>
      <ul>{preconds}</ul>
    </div>
    <div class="section">
      <div class="section-title">🔧 Test Steps</div>
      <table>
        <thead><tr><th>#</th><th>Action</th><th>Expected Result</th></tr></thead>
        <tbody>{steps_rows}</tbody>
      </table>
    </div>
    <div class="section">
      <div class="section-title">✅ Expected Results</div>
      <ul>{results}</ul>
    </div>
    <div class="section">
      <div class="section-title">🔁 Postconditions</div>
      <ul>{postconds}</ul>
    </div>
    <div class="meta">
      <span>⚠️ Risk: {tc.risk_score:.3f}</span>
      <span>📊 Coverage: {tc.coverage:.1%}</span>
      <span>🔗 Path: {tc.path_length}</span>
      <span>💬 {tc.notes or ''}</span>
    </div>
  </div>
</div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI Test Cases Report</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap');
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Syne',sans-serif;background:#0f0f1a;color:#cdd6f4;min-height:100vh}}
.hero{{background:linear-gradient(135deg,#0f0c29,#302b63,#24243e);padding:40px;}}
.hero h1{{font-size:2rem;font-weight:800;color:white;margin-bottom:6px}}
.hero p{{color:rgba(255,255,255,.6);font-size:.95rem}}
.stats{{display:flex;gap:16px;padding:24px 40px;flex-wrap:wrap;background:#13131f;
        border-bottom:1px solid #1e1e2e}}
.stat{{background:#1e1e2e;border-radius:10px;padding:14px 22px;text-align:center;
       min-width:90px;flex:1}}
.stat-num{{font-size:1.8rem;font-weight:800;font-family:'JetBrains Mono'}}
.stat-lbl{{font-size:.7rem;color:#6c7086;text-transform:uppercase;letter-spacing:.05em;margin-top:3px}}
.controls{{padding:20px 40px;background:#13131f;display:flex;gap:12px;flex-wrap:wrap;
           align-items:center;border-bottom:1px solid #1e1e2e}}
.controls input{{background:#1e1e2e;border:1px solid #313244;border-radius:8px;
                  padding:9px 14px;color:#cdd6f4;font-size:.9rem;
                  font-family:'Syne',sans-serif;min-width:260px}}
.controls input:focus{{outline:none;border-color:#cba6f7}}
.controls select{{background:#1e1e2e;border:1px solid #313244;border-radius:8px;
                   padding:9px 14px;color:#cdd6f4;font-size:.85rem;
                   font-family:'Syne',sans-serif}}
.count{{color:#6c7086;font-size:.85rem;margin-left:auto}}
.container{{padding:24px 40px;max-width:1400px;margin:0 auto}}
.card{{background:#1e1e2e;border:1px solid #313244;border-radius:12px;
       margin-bottom:16px;overflow:hidden;transition:box-shadow .2s}}
.card:hover{{box-shadow:0 4px 24px rgba(203,166,247,.15)}}
.card-header{{padding:18px 22px;border-left:4px solid #cba6f7}}
.header-top{{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:8px}}
.tc-id{{font-family:'JetBrains Mono';font-size:.78rem;color:#6272a4}}
.tc-title{{font-size:1.05rem;font-weight:700;margin-bottom:5px}}
.tc-desc{{font-size:.83rem;color:#a6adc8;line-height:1.5}}
.tags{{margin-top:8px;display:flex;gap:6px;flex-wrap:wrap}}
.tag{{background:#313244;color:#cdd6f4;padding:2px 9px;border-radius:12px;font-size:.7rem}}
.badge{{padding:3px 10px;border-radius:20px;font-size:.72rem;font-weight:700}}
.src-badge{{background:#181825;border:1px solid #313244;color:#6c7086;
            padding:2px 9px;border-radius:12px;font-size:.7rem;
            font-family:'JetBrains Mono'}}
.card-body{{padding:0 22px 18px}}
.section{{margin-top:14px}}
.section-title{{font-size:.8rem;font-weight:700;color:#cba6f7;
                text-transform:uppercase;letter-spacing:.05em;margin-bottom:7px}}
ul{{padding-left:18px;font-size:.84rem;color:#a6adc8;line-height:1.8}}
table{{width:100%;border-collapse:collapse;font-size:.8rem}}
th{{background:#313244;color:#cdd6f4;padding:8px 10px;text-align:left;
    font-weight:700;font-size:.75rem;text-transform:uppercase;letter-spacing:.04em}}
td{{padding:7px 10px;border-bottom:1px solid #1e1e2e;color:#a6adc8;vertical-align:top}}
tr:nth-child(even) td{{background:#181825}}
.meta{{display:flex;gap:16px;flex-wrap:wrap;margin-top:14px;padding-top:12px;
       border-top:1px solid #313244;font-size:.75rem;color:#6c7086}}
.hidden{{display:none}}
footer{{text-align:center;padding:30px;color:#45475a;font-size:.8rem;
        border-top:1px solid #1e1e2e;margin-top:20px}}
</style>
</head>
<body>
<div class="hero">
  <h1>🧪 AI-Generated Test Cases</h1>
  <p>Generated: {time.strftime('%Y-%m-%d %H:%M:%S')} &nbsp;|&nbsp;
     Total: <strong>{len(test_cases)}</strong> test cases</p>
</div>
<div class="stats">{stats_html}</div>
<div class="controls">
  <input type="text" id="search" placeholder="🔍 Search by title, ID, description...">
  <select id="filterPriority" onchange="applyFilters()">
    <option value="">All Priorities</option>
    <option>Critical</option><option>High</option>
    <option>Medium</option><option>Low</option>
  </select>
  <select id="filterType" onchange="applyFilters()">
    <option value="">All Types</option>
    <option>Positive</option><option>Negative</option>
    <option>Boundary</option><option>Integration</option>
  </select>
  <select id="filterSource" onchange="applyFilters()">
    <option value="">All Sources</option>
    {"".join(f'<option>{s}</option>' for s in sorted(set(tc.source_file for tc in test_cases)))}
  </select>
  <span class="count" id="countLabel">{len(test_cases)} test cases</span>
</div>
<div class="container" id="cardContainer">{cards}</div>
<footer>Generated by PlantUML → AI Test Case Generator &nbsp;|&nbsp;
  Powered by Meta Llama 3.1 &amp; GNN Risk Analysis</footer>
<script>
document.getElementById('search').addEventListener('input', applyFilters);
function applyFilters() {{
  const q  = document.getElementById('search').value.toLowerCase();
  const pr = document.getElementById('filterPriority').value;
  const tp = document.getElementById('filterType').value;
  const sc = document.getElementById('filterSource').value;
  const cards = document.querySelectorAll('.card');
  let shown = 0;
  cards.forEach(c => {{
    const text = c.innerText.toLowerCase();
    const match =
      (!q  || text.includes(q)) &&
      (!pr || c.dataset.priority === pr) &&
      (!tp || c.dataset.type === tp) &&
      (!sc || c.dataset.source === sc);
    c.classList.toggle('hidden', !match);
    if (match) shown++;
  }});
  document.getElementById('countLabel').textContent = shown + ' test cases';
}}
</script>
</body>
</html>"""
    return html.encode("utf-8")

# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE RUNNER
# ─────────────────────────────────────────────────────────────────────────────
def run_pipeline_for_file(content: str, filename: str,
                           api_key: str, num_paths: int,
                           variations: List[str],
                           progress_callback=None) -> Tuple[List[TestCase], dict, plt.Figure]:
    steps = {}

    # Stage 1
    if progress_callback: progress_callback(0.1, f"[{filename}] Stage 1: Parsing…")
    parser = PlantUMLParser()
    parsed = parser.parse_content(content)
    steps["parsed"] = parsed

    # Stage 2
    if progress_callback: progress_callback(0.3, f"[{filename}] Stage 2: Building graph…")
    builder = UnifiedGraphBuilder()
    graph = builder.build_graph(parsed)
    fig = builder.visualize()
    steps["graph_info"] = {
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges()
    }

    # Stage 3
    if progress_callback: progress_callback(0.5, f"[{filename}] Stage 3: Risk analysis & paths…")
    rp = RiskPredictor(graph)
    risk_scores = rp.predict_risks()
    tpg = TestPathGenerator(graph, risk_scores)
    test_paths = tpg.generate_paths(num_paths=num_paths)
    steps["num_paths"] = len(test_paths)

    # Stage 4
    if progress_callback: progress_callback(0.7, f"[{filename}] Stage 4: Generating test cases…")
    gen = TestCaseGenerator(HF_API_KEY)
    test_cases = []
    for path in test_paths:
        for var in variations:
            try:
                tc = gen.generate(path.to_dict(), var, source_file=filename)
                test_cases.append(tc)
            except Exception as e:
                st.warning(f"⚠️ Skipped path ({var}): {e}")

    # Re-assign priorities using percentile ranking on the GNN risk scores.
    # Guarantees all four priority bands are represented regardless of
    # how clustered the raw GNN outputs are.
    test_cases = assign_priorities_by_percentile(test_cases)

    if progress_callback: progress_callback(1.0, f"[{filename}] ✅ Done!")
    return test_cases, steps, fig

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    st.markdown("---")

    st.markdown("### 🛤️ Pipeline Settings")
    num_paths = st.slider("Paths per file", 2, 20, 8,
                          help="More paths = more test cases, longer runtime")
    variations = st.multiselect(
        "Test variations",
        ["positive", "negative", "boundary", "integration"],
        default=["positive", "negative"],
        help="Each variation generates a separate test case per path"
    )
    if not variations:
        st.warning("⚠️ Select at least one variation")
        variations = ["positive"]

    st.markdown("---")
    st.markdown("### 📊 Pipeline Flow")
    for step in [
        ("🟢 Stage 1", "PlantUML Parser"),
        ("🔵 Stage 2", "Graph Builder"),
        ("🟡 Stage 3", "Risk-Guided A* Paths"),
        ("🔴 Stage 4", "AI Test Case Gen"),
    ]:
        st.markdown(
            f'<div class="stage-card"><h4>{step[0]}</h4><p>{step[1]}</p></div>',
            unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# MAIN PAGE
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>🧪 PlantUML → AI Test Case Generator</h1>
  <p>Upload your PlantUML diagrams and get AI-powered test cases in seconds.</p>
  <span class="badge">4-Stage Pipeline</span>
  <span class="badge">GNN Risk Analysis</span>
  <span class="badge">A* Path Search</span>
  <span class="badge">Meta Llama 3.1</span>
  <span class="badge">JSON · PDF · CSV · HTML</span>
</div>
""", unsafe_allow_html=True)

# ── File Upload ──
st.markdown("### 📂 Upload PlantUML Files")
uploaded_files = st.file_uploader(
    "Drop one or more `.puml` files here",
    type=["puml", "plantuml", "txt"],
    accept_multiple_files=True,
    label_visibility="collapsed"
)

if uploaded_files:
    st.success(f"✅ {len(uploaded_files)} file(s) loaded: "
               f"{', '.join(f.name for f in uploaded_files)}")

    # Preview
    with st.expander("👁️ Preview uploaded files"):
        for uf in uploaded_files:
            st.markdown(f"**{uf.name}**")
            st.code(uf.read().decode("utf-8", errors="replace"), language="text")
            uf.seek(0)

    st.markdown("---")

    # ── Run Button ──
    if st.button("🚀 Run Full Pipeline", type="primary", use_container_width=True):
        all_test_cases: List[TestCase] = []
        all_stages: Dict[str, dict] = {}
        all_figs: Dict[str, plt.Figure] = {}

        progress_bar = st.progress(0)
        status_text  = st.empty()

        for idx, uf in enumerate(uploaded_files):
            content = uf.read().decode("utf-8", errors="replace")
            base_progress = idx / len(uploaded_files)
            step_size = 1 / len(uploaded_files)

            def _progress(frac, msg, bp=base_progress, ss=step_size):
                progress_bar.progress(min(bp + frac * ss, 1.0))
                status_text.markdown(f"⏳ {msg}")

            try:
                tcs, stages, fig = run_pipeline_for_file(
                    content, uf.name, HF_API_KEY,
                    num_paths, variations, _progress)
                all_test_cases.extend(tcs)
                all_stages[uf.name] = stages
                all_figs[uf.name] = fig
            except Exception as e:
                st.error(f"❌ Failed on {uf.name}: {e}")

        progress_bar.progress(1.0)
        status_text.markdown("✅ **Pipeline complete!**")

        if not all_test_cases:
            st.error("No test cases were generated. Check your .puml files and try again.")
            st.stop()

        # ── Store in session state ──
        st.session_state["test_cases"] = all_test_cases
        st.session_state["stages"]     = all_stages
        st.session_state["figures"]    = all_figs

# ─────────────────────────────────────────────────────────────────────────────
# RESULTS SECTION
# ─────────────────────────────────────────────────────────────────────────────
if "test_cases" in st.session_state:
    all_test_cases: List[TestCase] = st.session_state["test_cases"]
    all_stages  = st.session_state["stages"]
    all_figs    = st.session_state["figures"]

    st.markdown("---")
    st.markdown("## 📊 Results")

    # ── Metrics ──
    total   = len(all_test_cases)
    crit    = sum(1 for tc in all_test_cases if tc.priority == TestCasePriority.CRITICAL)
    high    = sum(1 for tc in all_test_cases if tc.priority == TestCasePriority.HIGH)
    ai_gen  = sum(1 for tc in all_test_cases if tc.notes and "Llama" in tc.notes)
    sources = len(set(tc.source_file for tc in all_test_cases))

    st.markdown(
        f'<div class="metric-row">'
        f'<div class="metric-pill"><div class="num">{total}</div><div class="lbl">Test Cases</div></div>'
        f'<div class="metric-pill"><div class="num" style="color:#ff5555">{crit}</div><div class="lbl">Critical</div></div>'
        f'<div class="metric-pill"><div class="num" style="color:#ff8800">{high}</div><div class="lbl">High</div></div>'
        f'<div class="metric-pill"><div class="num" style="color:#89b4fa">{ai_gen}</div><div class="lbl">AI-Generated</div></div>'
        f'<div class="metric-pill"><div class="num" style="color:#a6e3a1">{sources}</div><div class="lbl">Source Files</div></div>'
        f'</div>',
        unsafe_allow_html=True)

    # ── Stage Details ──
    with st.expander("🔬 Pipeline Stage Details"):
        for fname, stages in all_stages.items():
            st.markdown(f"**📄 {fname}**")
            p = stages.get("parsed", {})
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Actors",    len(p.get("actors",    [])))
            col2.metric("Use Cases", len(p.get("usecases",  [])))
            col3.metric("Classes",   len(p.get("classes",   [])))
            col4.metric("Graph Nodes", stages.get("graph_info",{}).get("nodes",0))
            col5.metric("Paths",     stages.get("num_paths", 0))
            st.markdown("---")

    # ── Graph Visualizations ──
    with st.expander("🕸️ UML Dependency Graphs"):
        cols = st.columns(min(len(all_figs), 3))
        for i, (fname, fig) in enumerate(all_figs.items()):
            with cols[i % len(cols)]:
                st.markdown(f"**{fname}**")
                st.pyplot(fig, use_container_width=True)
                plt.close(fig)

    # ── Test Cases Preview ──
    st.markdown("### 🧾 Test Cases Preview")
    p_icons = {"Critical":"🔴","High":"🟠","Medium":"🟡","Low":"🟢"}

    # Filter controls
    col_search, col_p, col_t, col_src = st.columns([3,1,1,2])
    with col_search:
        search_q = st.text_input("🔍 Search", placeholder="title, ID, description…",
                                  label_visibility="collapsed")
    with col_p:
        filter_priority = st.selectbox("Priority", ["All","Critical","High","Medium","Low"],
                                        label_visibility="collapsed")
    with col_t:
        filter_type = st.selectbox("Type",
                                    ["All","Positive","Negative","Boundary","Integration"],
                                    label_visibility="collapsed")
    with col_src:
        sources_list = ["All"] + sorted(set(tc.source_file for tc in all_test_cases))
        filter_src = st.selectbox("Source", sources_list, label_visibility="collapsed")

    # Apply filters
    filtered = all_test_cases
    if search_q:
        q = search_q.lower()
        filtered = [tc for tc in filtered if
                    q in tc.title.lower() or q in tc.test_id.lower()
                    or q in tc.description.lower()]
    if filter_priority != "All":
        filtered = [tc for tc in filtered if tc.priority.value == filter_priority]
    if filter_type != "All":
        filtered = [tc for tc in filtered if tc.test_type.value == filter_type]
    if filter_src != "All":
        filtered = [tc for tc in filtered if tc.source_file == filter_src]

    st.caption(f"Showing {len(filtered)} of {total} test cases")

    for tc in filtered[:50]:
        p_icon = p_icons.get(tc.priority.value, "⚪")
        with st.expander(
            f"{p_icon} **{tc.test_id}** — {tc.title} "
            f"| {tc.priority.value} | {tc.test_type.value} | `{tc.source_file}`"
        ):
            c1, c2 = st.columns([2,1])
            with c1:
                st.markdown(f"**Description:** {tc.description}")
                st.markdown("**Preconditions:**")
                for pre in tc.preconditions:
                    st.markdown(f"  - {pre}")
            with c2:
                st.metric("Risk Score", f"{tc.risk_score:.3f}")
                st.metric("Coverage",   f"{tc.coverage:.1%}")
                st.metric("Path Length", tc.path_length)
                if tc.tags:
                    st.markdown(f"**Tags:** {', '.join(tc.tags)}")

            st.markdown("**Test Steps:**")
            if tc.test_steps:
                step_df = pd.DataFrame([
                    {"#": s.step_number, "Action": s.action,
                     "Expected Result": s.expected_result}
                    for s in tc.test_steps])
                st.dataframe(step_df, use_container_width=True, hide_index=True)

            if tc.expected_results:
                st.markdown("**Expected Results:**")
                for r in tc.expected_results: st.markdown(f"  ✅ {r}")
            if tc.notes:
                st.caption(f"💬 {tc.notes}")

    if len(filtered) > 50:
        st.info(f"Showing first 50 of {len(filtered)} results. Download exports for full list.")

    # ─────────────────────────────────────────────────────────────────────────
    # DOWNLOAD SECTION
    # ─────────────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("## 📥 Download Test Cases")

    with st.spinner("Preparing exports…"):
        json_bytes = export_json(all_test_cases)
        csv_bytes  = export_csv(all_test_cases)
        pdf_bytes  = export_pdf(all_test_cases)
        html_bytes = export_html(all_test_cases)

    dcol1, dcol2, dcol3, dcol4 = st.columns(4)

    with dcol1:
        st.markdown("#### 📋 JSON")
        st.markdown("Structured data with full metadata. Ideal for importing into test management tools.")
        st.download_button(
            "⬇️ Download JSON",
            data=json_bytes,
            file_name="test_cases.json",
            mime="application/json",
            use_container_width=True)

    with dcol2:
        st.markdown("#### 📊 CSV")
        st.markdown("Spreadsheet-ready format. Open in Excel, Google Sheets, or Jira.")
        st.download_button(
            "⬇️ Download CSV",
            data=csv_bytes,
            file_name="test_cases.csv",
            mime="text/csv",
            use_container_width=True)

    with dcol3:
        st.markdown("#### 📄 PDF")
        st.markdown("Professional report with colour-coded priority headers and step tables.")
        st.download_button(
            "⬇️ Download PDF",
            data=pdf_bytes,
            file_name="test_cases.pdf",
            mime="application/pdf",
            use_container_width=True)

    with dcol4:
        st.markdown("#### 🌐 HTML")
        st.markdown("Interactive web page with search & filter. Share with your team instantly.")
        st.download_button(
            "⬇️ Download HTML",
            data=html_bytes,
            file_name="test_cases.html",
            mime="text/html",
            use_container_width=True)

    st.markdown("---")
    # ZIP bundle
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("test_cases.json", json_bytes)
        zf.writestr("test_cases.csv",  csv_bytes)
        zf.writestr("test_cases.pdf",  pdf_bytes)
        zf.writestr("test_cases.html", html_bytes)
    zip_buf.seek(0)
    st.download_button(
        "📦 Download All Formats (ZIP)",
        data=zip_buf.getvalue(),
        file_name="test_cases_all_formats.zip",
        mime="application/zip",
        use_container_width=True,
        type="primary")

# ─────────────────────────────────────────────────────────────────────────────
# EMPTY STATE
# ─────────────────────────────────────────────────────────────────────────────
else:
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    for col, emoji, title, desc in [
        (c1, "📂", "Upload .puml Files",
         "Drag and drop one or multiple PlantUML diagram files above."),
        (c2, "⚙️", "Configure Settings",
         "Add your HuggingFace API key and choose test variations in the sidebar."),
        (c3, "🚀", "Generate & Export",
         "Click Run Pipeline and download results in JSON, CSV, PDF, or HTML."),
    ]:
        with col:
            st.markdown(
                f'<div class="stage-card" style="text-align:center;padding:28px">'
                f'<div style="font-size:2rem;margin-bottom:10px">{emoji}</div>'
                f'<h4 style="color:#cdd6f4;margin-bottom:8px">{title}</h4>'
                f'<p>{desc}</p></div>',
                unsafe_allow_html=True)