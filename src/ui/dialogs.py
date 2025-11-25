from PySide6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDialogButtonBox, QCheckBox, QComboBox, QHBoxLayout, QPushButton, QListWidget, QAbstractItemView, QGridLayout, QWidget, QLabel
from .colors import ColorCycler

class WireTypeDialog(QDialog):
    def __init__(self, parent=None, default_name=""):
        super().__init__(parent)
        self.setWindowTitle("Add Wire Type")
        self.layout = QVBoxLayout(self)
        
        self.form = QFormLayout()
        
        # Auto-name: A, B, C...
        # We need a way to know the next available letter. 
        # For now, let's just use a random letter or simple logic if we don't have context.
        # Better: Pass existing names to init?
        # Let's assume the user will type it or we default to empty for now if we can't do it smartly without context.
        # Wait, user explicitly asked for "default to a fresh single letter capital variable if empty".
        # I'll add a static counter or logic in SignatureEditor to pass the default.
        self.name_edit = QLineEdit(default_name)
        
        # Color Selection
        self.selected_color = ColorCycler.next_color()
        self.color_display = QLabel()
        self.color_display.setStyleSheet(f"background-color: {self.selected_color}; border: 1px solid #555; min-height: 30px; border-radius: 5px;")
        # self.color_display.setEnabled(False) # No need to disable QLabel

        # Palette Grid
        self.palette_widget = QWidget()
        self.palette_layout = QGridLayout(self.palette_widget)
        self.palette_layout.setContentsMargins(0, 0, 0, 0)
        self.palette_layout.setSpacing(5)
        
        for i, color in enumerate(ColorCycler.COLORS):
            btn = QPushButton()
            btn.setFixedSize(20, 20)
            btn.setStyleSheet(f"background-color: {color}; border: none; border-radius: 10px;")
            # Fix: clicked emits (checked), so we must accept it to avoid overriding c
            btn.clicked.connect(lambda checked=False, c=color: self.set_color(c))
            self.palette_layout.addWidget(btn, i // 5, i % 5)
            
        self.monoidal_check = QCheckBox()
        
        self.form.addRow("Name:", self.name_edit)
        self.form.addRow("Color:", self.color_display)
        self.form.addRow("", self.palette_widget)
        self.form.addRow("Monoidal:", self.monoidal_check)
        
        self.layout.addLayout(self.form)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def set_color(self, color):
        self.selected_color = color
        # Force update with robust styling
        self.color_display.setStyleSheet(f"""
            QLabel {{
                background-color: {self.selected_color};
                border: 1px solid #555;
                border-radius: 5px;
                min-height: 30px;
            }}
        """)
        self.color_display.setAutoFillBackground(True) # Ensure background is painted

    def get_data(self):
        return {
            "name": self.name_edit.text(),
            "color": self.selected_color,
            "is_monoidal": self.monoidal_check.isChecked()
        }

from .morphism_editor import MorphismEditorWidget

class MorphismDialog(QDialog):
    def __init__(self, wire_types, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Morphism")
        self.resize(600, 400) # Make it bigger for the editor
        self.layout = QVBoxLayout(self)
        
        self.form = QFormLayout()
        self.name_edit = QLineEdit()
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Learnable", "Function", "Data"])
        
        self.form.addRow("Name:", self.name_edit)
        self.form.addRow("Type:", self.type_combo)
        self.layout.addLayout(self.form)
        
        # Editor
        self.editor = MorphismEditorWidget(wire_types)
        self.layout.addWidget(self.editor)
        
        # Connect type change to editor style
        self.type_combo.currentTextChanged.connect(self.editor.update_box_style)
        # Trigger initial update
        self.editor.update_box_style(self.type_combo.currentText())
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def get_data(self):
        editor_data = self.editor.get_data()
        return {
            "name": self.name_edit.text(),
            "type_name": self.type_combo.currentText(),
            "inputs": editor_data["inputs"],
            "outputs": editor_data["outputs"]
        }

    def refresh_types(self, wire_types):
        self.editor.refresh_types(wire_types)

    def set_data(self, name, type_name, inputs, outputs):
        self.name_edit.setText(name)
        self.type_combo.setCurrentText(type_name)
        self.editor.set_data(name, type_name, inputs, outputs)

class RelationDialog(QDialog):
    def __init__(self, morphisms, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Relation")
        self.layout = QVBoxLayout(self)
        
        self.form = QFormLayout()
        self.name_edit = QLineEdit()
        
        self.m1_combo = QComboBox()
        self.m1_combo.addItems(morphisms)
        
        self.m2_combo = QComboBox()
        self.m2_combo.addItems(morphisms)
        
        self.divergence_combo = QComboBox()
        self.divergence_combo.addItems(["KL", "MSE", "L1", "Cosine"])
        
        self.form.addRow("Name:", self.name_edit)
        self.form.addRow("Morphism 1:", self.m1_combo)
        self.form.addRow("Morphism 2:", self.m2_combo)
        self.form.addRow("Divergence:", self.divergence_combo)
        
        self.layout.addLayout(self.form)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def get_data(self):
        return {
            "name": self.name_edit.text(),
            "morphism_1": self.m1_combo.currentText(),
            "morphism_2": self.m2_combo.currentText(),
            "divergence": self.divergence_combo.currentText()
        }
