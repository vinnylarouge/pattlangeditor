import pytest
import json
import os
from diagram_editor_new.src.core.graph import Graph, Node, Wire
from diagram_editor_new.src.core.signature import Signature
from diagram_editor_new.src.core.serializer import Serializer
from diagram_editor_new.src.core.codegen import CodeGenerator

def test_serialization():
    # Setup
    sig = Signature()
    sig.add_wire_type("T", "#ffffff")
    sig.add_morphism("F", "Function", [{"label":"in","type":"T"}], [{"label":"out","type":"T"}])
    
    graph = Graph()
    n1 = Node("F", "Function", (0,0), id="n1")
    n1.add_input("in", "T")
    n1.add_output("out", "T")
    graph.add_node(n1)
    
    # Serialize
    json_str = Serializer.to_json(sig, graph)
    
    # Deserialize
    sig2, graph2 = Serializer.from_json(json_str)
    
    # Verify
    assert "T" in sig2.wire_types
    assert "F" in sig2.morphisms
    assert "n1" in graph2.nodes
    assert graph2.nodes["n1"].name == "F"
    assert len(graph2.nodes["n1"].inputs) == 1

def test_codegen():
    # Setup
    sig = Signature()
    sig.add_wire_type("T", "#ffffff")
    sig.add_morphism("Linear", "Learnable", [{"label":"in","type":"T"}], [{"label":"out","type":"T"}])
    
    graph = Graph()
    n1 = Node("Linear", "Learnable", (0,0), id="n1")
    n1.add_input("in", "T")
    n1.add_output("out", "T")
    graph.add_node(n1)
    
    choices = {
        "general": {"batch_size": "32", "lr": "0.01", "epochs": "5", "optimizer": "Adam"},
        "wires": {"T": "128"},
        "morphisms": {"Linear": "nn.Linear(128, 128)"}
    }
    
    codegen = CodeGenerator(sig, graph, choices)
    notebook_json = codegen.generate_notebook()
    
    # Verify JSON structure
    nb = json.loads(notebook_json)
    assert nb["nbformat"] == 4
    
    # Verify content
    code_cells = [c["source"] for c in nb["cells"] if c["cell_type"] == "code"]
    full_code = "".join(["".join(c) for c in code_cells])
    
    assert "class GeneratedModel(nn.Module):" in full_code
    assert "self.Linear_" in full_code # Check unique name generation
    assert "nn.Linear(128, 128)" in full_code
    assert "BATCH_SIZE = 32" in full_code
