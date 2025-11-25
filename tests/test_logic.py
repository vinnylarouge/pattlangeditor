import sys
import os
import pytest

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from core.graph import Graph, Node
from core.signature import Signature

def test_signature_defaults():
    sig = Signature()
    assert "Image" in sig.wire_types
    assert "Encoder" in sig.morphisms

def test_add_wire_type():
    sig = Signature()
    sig.add_wire_type("Tensor", "#000000", is_monoidal=True)
    assert "Tensor" in sig.wire_types
    assert sig.wire_types["Tensor"].is_monoidal

def test_add_morphism():
    sig = Signature()
    sig.add_morphism("MyOp", "Function", ["Image"], ["Latent"])
    assert "MyOp" in sig.morphisms
    assert sig.morphisms["MyOp"].inputs == ["Image"]

def test_single_input_constraint():
    graph = Graph()
    n1 = Node("N1", "Learnable", (0,0))
    n1.add_output("out", "Image")
    n2 = Node("N2", "Learnable", (100,0))
    n2.add_input("in", "Image")
    n3 = Node("N3", "Learnable", (0,100))
    n3.add_output("out", "Image")
    
    graph.add_node(n1)
    graph.add_node(n2)
    graph.add_node(n3)
    
    # First wire: Success
    w1 = graph.add_wire(n1.id, "out", n2.id, "in", "Image")
    assert w1 is not None
    
    # Second wire to same input: Fail
    w2 = graph.add_wire(n3.id, "out", n2.id, "in", "Image")
    assert w2 is None

def test_multiple_outputs_allowed():
    graph = Graph()
    n1 = Node("N1", "Learnable", (0,0))
    n1.add_output("out", "Image")
    n2 = Node("N2", "Learnable", (100,0))
    n2.add_input("in", "Image")
    n3 = Node("N3", "Learnable", (100,100))
    n3.add_input("in", "Image")
    
    graph.add_node(n1)
    graph.add_node(n2)
    graph.add_node(n3)
    
    # First wire
    w1 = graph.add_wire(n1.id, "out", n2.id, "in", "Image")
    assert w1 is not None
    
    # Second wire from same output
    w2 = graph.add_wire(n1.id, "out", n3.id, "in", "Image")
    assert w2 is not None
