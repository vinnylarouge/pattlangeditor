import pytest
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import Qt
from diagram_editor_new.src.ui.dialogs import WireTypeDialog
from diagram_editor_new.src.ui.nodes import get_abbreviated_label
from diagram_editor_new.src.core.graph import Graph, Node, Wire
from diagram_editor_new.src.core.signature import Signature
from diagram_editor_new.src.ui.canvas import DiagramCanvas

def test_label_abbreviation():
    assert get_abbreviated_label("Encoder") == "Enr" # First 2 (En) + Last (r)
    assert get_abbreviated_label("Dec") == "Dec"
    assert get_abbreviated_label("A") == "A"
    assert get_abbreviated_label("LongName") == "Loe"

def test_wire_type_dialog_color_selection(qtbot):
    dialog = WireTypeDialog()
    qtbot.addWidget(dialog)
    
    # Find a color button (they are in palette_layout)
    layout = dialog.palette_layout
    item = layout.itemAtPosition(0, 0)
    btn = item.widget()
    assert isinstance(btn, QPushButton)
    
    # Click it
    qtbot.mouseClick(btn, Qt.LeftButton)
    
    # Check if selected_color updated (and wasn't set to False/black)
    assert dialog.selected_color != False
    assert isinstance(dialog.selected_color, str)
    assert dialog.selected_color.startswith("#")

def test_cascade_delete():
    g = Graph()
    n1 = Node("n1", "T", (0,0))
    n2 = Node("n2", "T", (100,0))
    g.add_node(n1)
    g.add_node(n2)
    
    w = g.add_wire(n1.id, "out", n2.id, "in", "T")
    assert len(g.wires) == 1
    
    removed_wires = g.remove_node(n1.id)
    assert len(g.wires) == 0
    assert w.id in removed_wires

def test_wire_coloring(qtbot):
    # Setup Signature
    sig = Signature()
    sig.add_wire_type("RedType", "#ff0000")
    
    # Setup Canvas
    canvas = DiagramCanvas()
    canvas.set_signature(sig)
    qtbot.addWidget(canvas)
    
    # Add Nodes (needed for wire endpoints)
    n1 = Node("n1", "M", (0,0), id="node1")
    n1.add_output("out", "RedType")
    n2 = Node("n2", "M", (100,0), id="node2")
    n2.add_input("in", "RedType")
    
    canvas.add_node(n1)
    canvas.add_node(n2)
    
    # Debug: Check node items
    print(f"Node items: {canvas.node_items.keys()}")
    
    # Add Wire
    wire = Wire("node1", "out", "node2", "in", "RedType", id="w1")
    canvas.add_wire(wire)
    
    # Check WireItem color
    assert "w1" in canvas.wire_items, f"Wire w1 not found in {canvas.wire_items.keys()}"
    wire_item = canvas.wire_items["w1"]
    assert wire_item.color == QColor("#ff0000")
