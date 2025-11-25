from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QFrame, QTreeWidget, QTreeWidgetItem, QHeaderView
from PySide6.QtCore import Qt, QMimeData, Signal
from PySide6.QtGui import QDrag, QPixmap, QPainter, QColor
from core.signature import Signature, Morphism
from .dialogs import WireTypeDialog, MorphismDialog, RelationDialog

class MorphismTree(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setHeaderHidden(True)
        self.setStyleSheet("""
            QTreeWidget {
                background-color: #3c3c3c;
                border: none;
                border-radius: 5px;
            }
            QTreeWidget::item {
                padding: 5px;
            }
            QTreeWidget::item:hover {
                background-color: #555555;
            }
        """)

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if not item:
            return
            
        morphism = item.data(0, Qt.UserRole)
        if not isinstance(morphism, Morphism):
            return # Only drag morphisms
            
        drag = QDrag(self)
        mime = QMimeData()
        mime.setText(morphism.name) # Pass morphism name
        drag.setMimeData(mime)
        
        # Pixmap
        pixmap = QPixmap(120, 80)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setBrush(QColor("#3c3c3c")) # Default color
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, 120, 80, 10, 10)
        painter.setPen(Qt.white)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, morphism.name)
        painter.end()
        
        drag.setPixmap(pixmap)
        drag.setHotSpot(pixmap.rect().center())
        drag.exec_(Qt.CopyAction)

class SignatureEditor(QWidget):
    add_morphism_requested = Signal()

    def __init__(self, signature: Signature):
        super().__init__()
        self.signature = signature
        self.setFixedWidth(250)
        self.setStyleSheet("background-color: #2b2b2b; color: white;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header = QLabel("Signature")
        header.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # Buttons
        btn_layout = QVBoxLayout()
        self.add_type_btn = QPushButton("Add Wire Type")
        self.add_type_btn.clicked.connect(self.add_wire_type)
        btn_layout.addWidget(self.add_type_btn)
        
        self.add_morphism_btn = QPushButton("Add Morphism")
        self.add_morphism_btn.clicked.connect(self.add_morphism)
        btn_layout.addWidget(self.add_morphism_btn)
        
        self.add_relation_btn = QPushButton("Add Relation")
        self.add_relation_btn.clicked.connect(self.add_relation)
        btn_layout.addWidget(self.add_relation_btn)
        
        layout.addLayout(btn_layout)
        
        # Tree Widget
        self.tree = MorphismTree()
        self.tree.itemClicked.connect(self.edit_item)
        layout.addWidget(self.tree)
        
        self.refresh_tree()

    def refresh_tree(self):
        self.tree.clear()
        
        # Wire Types Category
        types_item = QTreeWidgetItem(["Wire Types"])
        types_item.setExpanded(True)
        self.tree.addTopLevelItem(types_item)
        
        for name, wt in self.signature.wire_types.items():
            item = QTreeWidgetItem([name])
            item.setForeground(0, QColor(wt.color))
            types_item.addChild(item)
            
        # Morphisms Category
        morphisms_item = QTreeWidgetItem(["Morphisms"])
        morphisms_item.setExpanded(True)
        self.tree.addTopLevelItem(morphisms_item)
        
        for name, m in self.signature.morphisms.items():
            item = QTreeWidgetItem([name])
            item.setData(0, Qt.UserRole, m) # Store morphism object
            morphisms_item.addChild(item)
            
        # Relations Category
        relations_item = QTreeWidgetItem(["Relations"])
        relations_item.setExpanded(True)
        self.tree.addTopLevelItem(relations_item)
        
        for name, r in self.signature.relations.items():
            item = QTreeWidgetItem([f"{name}: {r.morphism_1} ~ {r.morphism_2}"])
            relations_item.addChild(item)

    def add_wire_type(self):
        # Generate default name: A, B, C...
        existing = set(self.signature.wire_types.keys())
        default_name = "A"
        for char_code in range(65, 91): # A-Z
            char = chr(char_code)
            if char not in existing:
                default_name = char
                break
        
        dialog = WireTypeDialog(self, default_name)
        if dialog.exec_():
            data = dialog.get_data()
            if data["name"]:
                self.signature.add_wire_type(data["name"], data["color"], data["is_monoidal"])
                self.refresh_tree()

    def add_morphism(self):
        self.add_morphism_requested.emit()
        # Old dialog logic removed
        # dialog = MorphismDialog(self.signature.wire_types, self)
        # if dialog.exec_():
        #     data = dialog.get_data()
        #     if data["name"]:
        #         # TODO: Validate input/output types exist
        #         self.signature.add_morphism(data["name"], data["type_name"], data["inputs"], data["outputs"])
        #         self.refresh_tree()

    def add_relation(self):
        dialog = RelationDialog(list(self.signature.morphisms.keys()), self)
        if dialog.exec_():
            data = dialog.get_data()
            if data["name"]:
                self.signature.add_relation(data["name"], data["morphism_1"], data["morphism_2"], data["divergence"])
                self.refresh_tree()

    def edit_item(self, item, column):
        # Check what kind of item it is
        parent = item.parent()
        if not parent:
            return # Top level category
            
        category = parent.text(0)
        name = item.text(0)
        
        if category == "Wire Types":
            wt = self.signature.wire_types.get(name)
            if wt:
                # Open dialog with existing data
                dialog = WireTypeDialog(self, wt.name)
                dialog.setWindowTitle("Edit Wire Type")
                dialog.set_color(wt.color)
                dialog.monoidal_check.setChecked(wt.is_monoidal)
                
                if dialog.exec_():
                    data = dialog.get_data()
                    if data["name"]:
                        # Update existing object
                        # If name changed, we need to handle key change in dict
                        if data["name"] != name:
                            del self.signature.wire_types[name]
                            self.signature.wire_types[data["name"]] = wt
                            wt.name = data["name"]
                            
                        wt.color = data["color"]
                        wt.is_monoidal = data["is_monoidal"]
                        self.refresh_tree()
                        
        elif category == "Morphisms":
            m = item.data(0, Qt.UserRole)
            if m:
                dialog = MorphismDialog(self.signature.wire_types, self)
                dialog.setWindowTitle("Edit Morphism")
                dialog.set_data(m.name, m.type_name, m.inputs, m.outputs)
                
                if dialog.exec_():
                    data = dialog.get_data()
                    if data["name"]:
                        # Update existing object
                        if data["name"] != m.name:
                            del self.signature.morphisms[m.name]
                            self.signature.morphisms[data["name"]] = m
                            m.name = data["name"]
                            
                        m.type_name = data["type_name"]
                        m.inputs = data["inputs"]
                        m.outputs = data["outputs"]
                        self.refresh_tree()
