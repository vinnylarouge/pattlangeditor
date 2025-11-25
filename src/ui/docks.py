from PySide6.QtWidgets import QDockWidget, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QLineEdit, QComboBox, QLabel, QMessageBox
from PySide6.QtCore import Qt, Signal
from .morphism_editor import MorphismEditorWidget

class MorphismEditorDock(QDockWidget):
    morphism_created = Signal(str, str, list, list) # name, type, inputs, outputs

    def __init__(self, signature, parent=None):
        super().__init__("Morphism Editor", parent)
        self.signature = signature
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        
        self.container = QWidget()
        self.setWidget(self.container)
        self.layout = QVBoxLayout(self.container)
        
        # Controls
        form_layout = QHBoxLayout()
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Learnable", "Function", "Data"])
        form_layout.addWidget(QLabel("Type:"))
        form_layout.addWidget(self.type_combo)
        
        self.layout.addLayout(form_layout)
        
        # Editor
        self.editor = MorphismEditorWidget(self.signature.wire_types)
        self.layout.addWidget(self.editor)
        
        # Connect type change
        self.type_combo.currentTextChanged.connect(self.editor.update_box_style)
        self.type_combo.currentTextChanged.connect(self.update_default_name)
        
        # Create Button
        self.create_btn = QPushButton("Create Morphism")
        self.create_btn.setStyleSheet("background-color: #29adff; color: white; font-weight: bold; padding: 10px;")
        self.create_btn.clicked.connect(self.create_morphism)
        self.layout.addWidget(self.create_btn)
        
        # Initial setup
        self.editor.update_box_style("Learnable")
        self.update_default_name()

    def update_default_name(self):
        # Auto-generate name: foo, bar, baz...
        # Or just simple M1, M2... or based on type?
        # User asked for "foo, bar, baz"
        # Let's try to be smart or just pick from a list
        defaults = ["foo", "bar", "baz", "qux", "quux", "corge", "grault", "garply", "waldo", "fred", "plugh", "xyzzy", "thud"]
        existing = set(self.signature.morphisms.keys())
        
        name = "morphism"
        for d in defaults:
            if d not in existing:
                name = d
                break
        else:
            # Fallback
            i = 1
            while f"morphism_{i}" in existing:
                i += 1
            name = f"morphism_{i}"
            
        self.editor.name_input.setText(name)

    def create_morphism(self):
        data = self.editor.get_data()
        name = data["name"]
        
        if not name:
            QMessageBox.warning(self, "Error", "Morphism name cannot be empty.")
            return
            
        if name in self.signature.morphisms:
            QMessageBox.warning(self, "Error", f"Morphism '{name}' already exists.")
            return

        type_name = self.type_combo.currentText()
        
        # Emit signal
        self.morphism_created.emit(name, type_name, data["inputs"], data["outputs"])
        
        # Reset for next
        self.update_default_name()
        # Maybe clear ports?
        # self.editor.clear_ports() # TODO: Implement clear
