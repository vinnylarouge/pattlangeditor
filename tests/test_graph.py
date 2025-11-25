import sys
import os
import pytest

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from core.graph import Graph, Node

def test_add_node():
    graph = Graph()
    node = Node("TestNode", "Learnable", (0, 0))
    graph.add_node(node)
    assert len(graph.nodes) == 1
    assert graph.nodes[node.id] == node

def test_remove_node():
    graph = Graph()
    node = Node("TestNode", "Learnable", (0, 0))
    graph.add_node(node)
    graph.remove_node(node.id)
    assert len(graph.nodes) == 0

def test_add_wire():
    graph = Graph()
    node1 = Node("N1", "Learnable", (0, 0))
    node1.add_output("out", "Image")
    node2 = Node("N2", "Learnable", (100, 0))
    node2.add_input("in", "Image")
    
    graph.add_node(node1)
    graph.add_node(node2)
    
    wire = graph.add_wire(node1.id, "out", node2.id, "in", "Image")
    assert len(graph.wires) == 1
    assert wire.source_node_id == node1.id
    assert wire.target_node_id == node2.id

def test_remove_node_removes_wires():
    graph = Graph()
    node1 = Node("N1", "Learnable", (0, 0))
    node1.add_output("out", "Image")
    node2 = Node("N2", "Learnable", (100, 0))
    node2.add_input("in", "Image")
    
    graph.add_node(node1)
    graph.add_node(node2)
    graph.add_wire(node1.id, "out", node2.id, "in", "Image")
    
    graph.remove_node(node1.id)
    assert len(graph.nodes) == 1
    assert len(graph.wires) == 0
