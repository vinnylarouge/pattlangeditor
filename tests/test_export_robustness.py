import pytest
import json
from diagram_editor_new.src.core.graph import Graph, Node, Wire
from diagram_editor_new.src.core.signature import Signature
from diagram_editor_new.src.core.serializer import Serializer
from diagram_editor_new.src.core.codegen import CodeGenerator

def test_malformed_load():
    """Safety: Loading malformed JSON should raise an exception (to be caught by UI)."""
    malformed_json = "{ 'invalid': json "
    
    with pytest.raises(json.JSONDecodeError):
        Serializer.from_json(malformed_json)
        
    # Test valid JSON but missing fields
    incomplete_json = json.dumps({"graph": {}}) # Missing signature
    
    # Depending on implementation, this might pass (empty sig) or fail.
    # Current implementation uses .get(), so it should be robust and return empty sig.
    sig, graph = Serializer.from_json(incomplete_json)
    assert isinstance(sig, Signature)
    assert isinstance(graph, Graph)
    assert len(sig.wire_types) == 0

def test_state_clearing():
    """Safety: Loading a new file must clear previous state."""
    # 1. Create initial state
    sig = Signature()
    sig.add_wire_type("InitialType", "#000000")
    graph = Graph()
    node = Node("InitialNode", "Learnable", (0,0))
    graph.add_node(node)
    
    # 2. "Load" new state (simulate logic in MainWindow)
    # MainWindow logic:
    # new_sig, new_graph = Serializer.from_json(...)
    # self.signature.clear()
    # self.graph.clear()
    # self.signature.update(new_sig) ...
    
    # Let's verify the clear() methods work as expected
    sig.clear()
    graph.clear()
    
    assert "InitialType" not in sig.wire_types
    assert len(graph.nodes) == 0
    
    # 3. Simulate loading new content
    new_json = Serializer.to_json(Signature(), Graph()) # Empty
    new_sig, new_graph = Serializer.from_json(new_json)
    
    sig.wire_types.update(new_sig.wire_types)
    graph.nodes.update(new_graph.nodes)
    
    assert len(sig.wire_types) == 0
    assert len(graph.nodes) == 0

def test_complex_round_trip():
    """Goodness: Lossless round-trip of complex data."""
    sig = Signature()
    sig.add_wire_type("Tensor", "#ff0000")
    sig.add_wire_type("Scalar", "#00ff00", is_monoidal=True)
    sig.add_morphism("ComplexMorphism", "Learnable", 
                    [{"label": "in1", "type": "Tensor"}, {"label": "in2", "type": "Scalar"}],
                    [{"label": "out", "type": "Tensor"}])
    sig.add_relation("Rel1", "ComplexMorphism", "ComplexMorphism", "MSE")
    
    graph = Graph()
    n1 = Node("ComplexMorphism", "Learnable", (10, 20), id="n1")
    n1.add_input("in1", "Tensor")
    n1.add_input("in2", "Scalar")
    n1.add_output("out", "Tensor")
    graph.add_node(n1)
    
    n2 = Node("ComplexMorphism", "Learnable", (100, 200), id="n2")
    n2.add_input("in1", "Tensor")
    n2.add_input("in2", "Scalar")
    n2.add_output("out", "Tensor")
    graph.add_node(n2)
    
    wire = Wire("n1", "out", "n2", "in1", "Tensor", id="w1")
    graph.add_wire(n1.id, "out", n2.id, "in1", "Tensor") # Note: add_wire logic in graph might differ from direct Wire init
    # Graph.add_wire returns the wire object and adds it
    
    # Serialize
    json_str = Serializer.to_json(sig, graph)
    
    # Deserialize
    sig2, graph2 = Serializer.from_json(json_str)
    
    # Verify Signature
    assert "Tensor" in sig2.wire_types
    assert sig2.wire_types["Scalar"].is_monoidal == True
    assert "ComplexMorphism" in sig2.morphisms
    assert len(sig2.morphisms["ComplexMorphism"].inputs) == 2
    assert "Rel1" in sig2.relations
    assert sig2.relations["Rel1"].divergence == "MSE"
    
    # Verify Graph
    assert len(graph2.nodes) == 2
    assert "n1" in graph2.nodes
    assert graph2.nodes["n1"].position == [10, 20] # JSON might convert tuple to list
    assert len(graph2.wires) == 1
    w = list(graph2.wires.values())[0]
    assert w.type_name == "Tensor"
    assert w.source_node_id == "n1"
    assert w.target_node_id == "n2"

def test_notebook_validity():
    """Goodness: Exported notebook is valid JSON and has cells."""
    sig = Signature()
    graph = Graph()
    choices = {
        "general": {},
        "wires": {},
        "morphisms": {}
    }
    
    codegen = CodeGenerator(sig, graph, choices)
    nb_json = codegen.generate_notebook()
    
    nb = json.loads(nb_json)
    assert "cells" in nb
    assert "metadata" in nb
    assert nb["nbformat"] == 4
    
    # Check for at least one code cell
    assert len(nb["cells"]) >= 3 # Setup, Model, Train
    assert nb["cells"][0]["cell_type"] == "code"
