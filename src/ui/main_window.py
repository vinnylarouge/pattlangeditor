from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QDockWidget, QMenuBar, QMenu, QFileDialog, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from .canvas import DiagramCanvas
from .palette import SignatureEditor
from .palette import SignatureEditor
# from .docks import MorphismEditorDock # Removed
from .export_dialog import ExportDialog
from .export_dialog import ExportDialog
from core.graph import Graph, Node, Wire
from core.signature import Signature
from core.serializer import Serializer
from core.codegen import CodeGenerator

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ML Diagram Editor")
        self.resize(1200, 800)
        
        # Menu Bar
        self.setup_menu()
        
        # Central Widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Layout
        self.layout = QHBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Initialize Signature
        self.signature = Signature()
        
        # Signature Editor (Left)
        self.signature_editor = SignatureEditor(self.signature)
        self.signature_editor.add_morphism_requested.connect(self.open_morphism_dock)
        
        dock = QDockWidget("Signature", self)
        dock.setWidget(self.signature_editor)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)
        
        # Morphism Dialog (Windowed, Non-Modal)
        from .dialogs import MorphismDialog
        self.morphism_dialog = MorphismDialog(self.signature.wire_types, self)
        self.morphism_dialog.accepted.connect(self.handle_morphism_dialog_accepted)
        # We want it non-modal, so we use show() but we need to handle "Create" button manually?
        # QDialog with standard buttons usually closes on accept.
        # If we want it to stay open or behave like a tool window, we might need adjustments.
        # But "windowed as before" implies standard dialog behavior.
        # Let's stick to standard dialog behavior for now (modal or non-modal but closes on action).
        # User said "optional-minimise tabs", implying they want to keep it open?
        # "Windowed as before" -> Before it was a modal dialog that closed on create.
        # Let's implement it as a non-modal tool window that stays open?
        # No, let's stick to the standard QDialog pattern first as it's safest "as before".
        # But we'll use show() instead of exec_() to make it non-blocking if desired, 
        # OR just exec_() if they want true "as before".
        # "glitching... stretched" suggests the dock was the problem.
        # Let's use a non-modal dialog that closes on Create.
        self.morphism_dialog.setModal(False) # Non-blocking


        # Central Canvas
        self.canvas = DiagramCanvas()
        self.canvas.on_node_dropped = self.handle_node_drop
        self.canvas.on_wire_created = self.handle_wire_created
        self.canvas.on_nodes_deleted = self.handle_nodes_deleted
        self.layout.addWidget(self.canvas)
        
        # Initialize Graph
        self.graph = Graph()
        
        # Pass Signature to Canvas for color lookup
        self.canvas.set_signature(self.signature)

    def handle_wire_created(self, source_port, target_port):
        # Create wire in graph
        wire = self.graph.add_wire(
            source_port.node_id, source_port.name,
            target_port.node_id, target_port.name,
            source_port.type_name # Assume types match for now
        )
        if wire:
            self.canvas.add_wire(wire)
        else:
            # TODO: Show feedback (e.g. "Input already connected")
            pass

    def handle_nodes_deleted(self, node_ids):
        for node_id in node_ids:
            removed_wires = self.graph.remove_node(node_id)
            # Remove wires from canvas
            for wire_id in removed_wires:
                self.canvas.remove_wire(wire_id)
            
            # Node is already removed from canvas by the canvas itself before emitting signal
            # But we should ensure consistency if we change flow later.
            # Currently canvas removes item then emits signal.

    def open_morphism_dock(self):
        self.morphism_dialog.refresh_types(self.signature.wire_types)
        self.morphism_dialog.show()
        self.morphism_dialog.raise_()
        self.morphism_dialog.activateWindow()

    def handle_morphism_dialog_accepted(self):
        data = self.morphism_dialog.get_data()
        self.handle_morphism_created(data["name"], data["type_name"], data["inputs"], data["outputs"])

    def handle_morphism_created(self, name, type_name, inputs, outputs):
        self.signature.add_morphism(name, type_name, inputs, outputs)
        self.signature_editor.refresh_tree()
        # Optional: Flash success message or status bar
        self.statusBar().showMessage(f"Morphism '{name}' created.", 3000)

    def handle_node_drop(self, morphism_name, position):
        # Look up morphism in signature
        morphism = self.signature.morphisms.get(morphism_name)
        if not morphism:
            return
            
        node = Node(morphism.name, morphism.type_name, position)
        
        # Add ports from morphism definition
        for input_def in morphism.inputs:
            # input_def is {"type": str, "label": str}
            node.add_input(input_def["label"], input_def["type"])
            
        for output_def in morphism.outputs:
            node.add_output(output_def["label"], output_def["type"])
            
        self.graph.add_node(node)
        self.canvas.add_node(node)

    def setup_menu(self):
        menu_bar = self.menuBar()
        
        # File Menu
        file_menu = menu_bar.addMenu("File")
        
        save_action = QAction("Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        load_action = QAction("Load", self)
        load_action.setShortcut("Ctrl+O")
        load_action.triggered.connect(self.load_file)
        file_menu.addAction(load_action)
        
        file_menu.addSeparator()
        
        export_action = QAction("Export to Colab...", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self.export_notebook)
        file_menu.addAction(export_action)

    def save_file(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save Diagram", "", "JSON Files (*.json)")
        if filename:
            try:
                json_str = Serializer.to_json(self.signature, self.graph)
                with open(filename, 'w') as f:
                    f.write(json_str)
                self.statusBar().showMessage(f"Saved to {filename}", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save: {str(e)}")

    def load_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Load Diagram", "", "JSON Files (*.json)")
        if filename:
            try:
                with open(filename, 'r') as f:
                    json_str = f.read()
                
                # Deserialize
                new_sig, new_graph = Serializer.from_json(json_str)
                
                # Clear current
                self.signature.clear()
                self.graph.clear()
                
                # Restore Signature
                self.signature.wire_types.update(new_sig.wire_types)
                self.signature.morphisms.update(new_sig.morphisms)
                self.signature.relations.update(new_sig.relations)
                
                # Restore Graph
                self.graph.nodes.update(new_graph.nodes)
                self.graph.wires.update(new_graph.wires)
                
                # Refresh UI
                self.signature_editor.refresh_tree()
                
                # Refresh Canvas
                self.canvas.scene.clear()
                self.canvas.node_items.clear()
                self.canvas.wire_items.clear()
                
                # Re-add nodes
                for node in self.graph.nodes.values():
                    self.canvas.add_node(node)
                    
                # Re-add wires
                for wire in self.graph.wires.values():
                    self.canvas.add_wire(wire)
                    
                self.statusBar().showMessage(f"Loaded {filename}", 3000)
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load: {str(e)}")

    def export_notebook(self):
        dialog = ExportDialog(self.signature, self)
        if dialog.exec_():
            choices = dialog.get_data()
            
            filename, _ = QFileDialog.getSaveFileName(self, "Export Notebook", "", "Jupyter Notebook (*.ipynb)")
            if filename:
                try:
                    codegen = CodeGenerator(self.signature, self.graph, choices)
                    notebook_json = codegen.generate_notebook()
                    
                    with open(filename, 'w') as f:
                        f.write(notebook_json)
                        
                    self.statusBar().showMessage(f"Exported to {filename}", 3000)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to export: {str(e)}")
