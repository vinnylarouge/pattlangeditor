import pytest
from PySide6.QtCore import Qt, QPointF
from diagram_editor_new.src.ui.canvas import DiagramCanvas, DiagramScene
from diagram_editor_new.src.ui.wires import WireItem
from diagram_editor_new.src.core.graph import Graph, Node, Wire
from diagram_editor_new.src.core.signature import Signature
from diagram_editor_new.src.ui.palette import SignatureEditor

def test_wire_deletion(qtbot):
    # Setup
    graph = Graph()
    scene = DiagramScene()
    canvas = DiagramCanvas()
    canvas.scene = scene
    canvas.graph = graph # Mocking what MainWindow does
    # Actually Canvas doesn't store graph directly usually, it accesses it via parent or we inject it?
    # In my implementation of remove_wire in canvas.py:
    # self.scene.canvas.graph.remove_wire(item.wire.id)
    # So scene.canvas must be the canvas, and canvas must have graph.
    scene.canvas = canvas
    canvas.graph = graph
    
    # Add nodes and wire
    n1 = Node("A", "Learnable", (0,0), id="n1")
    n2 = Node("B", "Learnable", (100,0), id="n2")
    graph.add_node(n1)
    graph.add_node(n2)
    
    wire = Wire("n1", "out", "n2", "in", "T", id="w1")
    graph.wires["w1"] = wire
    
    # Add items to scene
    wire_item = WireItem(wire, QPointF(0,0), QPointF(100,0))
    scene.addItem(wire_item)
    canvas.wire_items["w1"] = wire_item
    
    # Select wire
    wire_item.setSelected(True)
    
    # Press Backspace
    # We need to simulate key press on the canvas/scene
    # qtbot.keyClick(canvas, Qt.Key_Backspace) 
    # But canvas is a View.
    
    # Manually call keyPressEvent to avoid focus issues in headless
    class MockEvent:
        def key(self): return Qt.Key_Backspace
        
    canvas.keyPressEvent(MockEvent())
    
    # Verify
    assert "w1" not in graph.wires
    assert "w1" not in canvas.wire_items
    assert wire_item not in scene.items()

def test_signature_edit_wire_type(qtbot):
    sig = Signature()
    sig.add_wire_type("T", "#ff0000")
    editor = SignatureEditor(sig)
    
    # Mock Dialog execution
    # We can't easily mock the dialog exec_ in this integration test without monkeypatching
    # But we can test the logic if we extract it or just trust the manual verification for UI dialogs.
    # Let's verify the data update logic if we were to call it.
    
    # Simulate editing "T"
    wt = sig.wire_types["T"]
    wt.color = "#00ff00" # Change color
    
    editor.refresh_tree()
    
    # Verify tree item color
    # Root -> Wire Types -> T
    root = editor.tree.topLevelItem(0)
    child = root.child(0)
    assert child.text(0) == "T"
    assert child.foreground(0).color().name() == "#00ff00"

def test_signature_edit_morphism(qtbot):
    sig = Signature()
    sig.add_wire_type("T", "#ffffff")
    sig.add_morphism("M", "Learnable", [{"label":"in","type":"T"}], [])
    editor = SignatureEditor(sig)
    
    # Simulate rename
    m = sig.morphisms["M"]
    del sig.morphisms["M"]
    m.name = "M_new"
    sig.morphisms["M_new"] = m
    
    editor.refresh_tree()
    
    root = editor.tree.topLevelItem(1) # Morphisms
    child = root.child(0)
    assert child.text(0) == "M_new"
