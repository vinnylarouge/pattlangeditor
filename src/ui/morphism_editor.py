from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame, QScrollArea, QLineEdit, QListWidget, QListWidgetItem, QAbstractItemView, QPushButton
from PySide6.QtCore import Qt, QMimeData, QSize
from PySide6.QtGui import QDrag, QPixmap, QPainter, QColor, QBrush, QPen

class DraggableCircle(QLabel):
    def __init__(self, type_name, color, parent=None):
        super().__init__(parent)
        self.type_name = type_name
        self.color = color
        self.setFixedSize(30, 30)
        self.setStyleSheet(f"""
            background-color: {color};
            border-radius: 15px;
            border: 2px solid white;
        """)
        self.setToolTip(type_name)
        self.setAlignment(Qt.AlignCenter)
        # self.setText(type_name[:1]) # Optional: Show first letter

    def mouseMoveEvent(self, e):
        if e.buttons() != Qt.LeftButton:
            return

        drag = QDrag(self)
        mime = QMimeData()
        mime.setText(self.type_name)
        mime.setData("application/x-wiretype", self.type_name.encode())
        mime.setData("application/x-color", self.color.encode())
        drag.setMimeData(mime)

        pixmap = QPixmap(30, 30)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setBrush(QColor(self.color))
        painter.setPen(QPen(Qt.white, 2))
        painter.drawEllipse(1, 1, 28, 28)
        painter.end()

        drag.setPixmap(pixmap)
        drag.setHotSpot(e.position().toPoint())
        drag.exec_(Qt.CopyAction)

class PortWidget(QWidget):
    def __init__(self, type_name, color, label_text="", on_remove=None, parent=None):
        super().__init__(parent)
        self.type_name = type_name
        self.color = color
        self.on_remove = on_remove
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(5)
        
        # Circle
        self.circle = QLabel()
        self.circle.setFixedSize(20, 20)
        self.circle.setStyleSheet(f"""
            background-color: {color};
            border-radius: 10px;
            border: 1px solid white;
        """)
        layout.addWidget(self.circle)
        
        # Label Edit
        self.label_edit = QLineEdit(label_text or type_name[:3])
        self.label_edit.setMaxLength(3)
        self.label_edit.setFixedWidth(30)
        self.label_edit.setStyleSheet("background: transparent; color: white; border: none; font-size: 10px;")
        self.label_edit.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label_edit)
        
        # Remove Button
        self.remove_btn = QPushButton("×")
        self.remove_btn.setFixedSize(16, 16)
        self.remove_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #888;
                border: none;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #ff4d4d;
            }
        """)
        self.remove_btn.clicked.connect(self.handle_remove)
        layout.addWidget(self.remove_btn)

    def handle_remove(self):
        if self.on_remove:
            self.on_remove(self)

class DropZone(QListWidget):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(True) # Allow internal reordering
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setMinimumWidth(100)
        self.setStyleSheet("""
            QListWidget {
                background-color: #333; 
                border-radius: 5px;
                border: 1px solid #555;
            }
            QListWidget::item {
                background: transparent;
            }
        """)
        
        # Title (Header)
        self.header = QLabel(title)
        self.header.setStyleSheet("color: #888; font-size: 10px; font-weight: bold; padding: 5px;")
        self.header.setAlignment(Qt.AlignCenter)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-wiretype"):
            event.accept()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat("application/x-wiretype"):
            event.accept()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasFormat("application/x-wiretype"):
            type_name = event.mimeData().text()
            color = event.mimeData().data("application/x-color").data().decode()
            self.add_port(type_name, color)
            event.accept()
        else:
            super().dropEvent(event)

    def add_port(self, type_name, color, label=""):
        item = QListWidgetItem(self)
        item.setSizeHint(QSize(100, 30)) # Adjusted size for horizontal layout
        
        port_widget = PortWidget(type_name, color, label, on_remove=self.remove_port_widget)
        self.setItemWidget(item, port_widget)

    def remove_port_widget(self, widget):
        # Find item for this widget
        for i in range(self.count()):
            item = self.item(i)
            if self.itemWidget(item) == widget:
                self.takeItem(i)
                break

    def get_ports(self):
        ports = []
        for i in range(self.count()):
            item = self.item(i)
            widget = self.itemWidget(item)
            if widget:
                ports.append({"type": widget.type_name, "label": widget.label_edit.text()})
        return ports

class MorphismEditorWidget(QWidget):
    def __init__(self, wire_types, parent=None):
        super().__init__(parent)
        self.wire_types = wire_types
        self.setMinimumHeight(300)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 1. Source Palette (Left)
        palette_container = QWidget()
        palette_layout = QVBoxLayout(palette_container)
        palette_layout.addWidget(QLabel("Types"))
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        
        self.refresh_types(wire_types)
            
        self.scroll_layout.addStretch()
        scroll.setWidget(self.scroll_content)
        palette_layout.addWidget(scroll)
        layout.addWidget(palette_container, 1)
        
        # 2. Input Zone
        input_container = QWidget()
        input_layout = QVBoxLayout(input_container)
        input_layout.addWidget(QLabel("INPUTS"))
        self.input_zone = DropZone("INPUTS")
        input_layout.addWidget(self.input_zone)
        layout.addWidget(input_container, 1)
        
        # 3. Morphism Box (Center Visual)
        self.box = QFrame()
        self.box.setFixedSize(60, 100)
        box_layout = QVBoxLayout(self.box)
        
        self.name_input = QLineEdit("M")
        self.name_input.setAlignment(Qt.AlignCenter)
        self.name_input.setStyleSheet("""
            QLineEdit {
                background: transparent;
                color: white;
                font-weight: bold;
                font-size: 20px;
                border: none;
            }
        """)
        box_layout.addWidget(self.name_input, 0, Qt.AlignCenter)
        layout.addWidget(self.box, 0, Qt.AlignCenter)
        
        self.update_box_style("Learnable") # Default, call after creating name_input
        
        # 4. Output Zone
        output_container = QWidget()
        output_layout = QVBoxLayout(output_container)
        output_layout.addWidget(QLabel("OUTPUTS"))
        self.output_zone = DropZone("OUTPUTS")
        output_layout.addWidget(self.output_zone)
        layout.addWidget(output_container, 1)

    def refresh_types(self, wire_types):
        # Clear existing items
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        # Add new items
        for name, wt in wire_types.items():
            circle = DraggableCircle(name, wt.color)
            self.scroll_layout.addWidget(circle)
            
        self.scroll_layout.addStretch()

    def update_box_style(self, type_name):
        if type_name == "Learnable":
            self.box.setStyleSheet("background-color: #000000; border-radius: 5px; border: 2px solid white;")
            self.name_input.setStyleSheet("background: transparent; color: white; font-weight: bold; font-size: 20px; border: none;")
        elif type_name == "Function":
            self.box.setStyleSheet("background-color: #ffffff; border-radius: 5px; border: 2px solid black;")
            self.name_input.setStyleSheet("background: transparent; color: black; font-weight: bold; font-size: 20px; border: none;")
        else:
            self.box.setStyleSheet("background-color: #29adff; border-radius: 5px; border: 2px solid white;")
            self.name_input.setStyleSheet("background: transparent; color: white; font-weight: bold; font-size: 20px; border: none;")

    def get_data(self):
        return {
            "name": self.name_input.text(),
            "inputs": self.input_zone.get_ports(),
            "outputs": self.output_zone.get_ports()
        }

    def set_data(self, name, type_name, inputs, outputs):
        self.name_input.setText(name)
        self.update_box_style(type_name)
        
        # Clear zones
        self.input_zone.clear()
        self.output_zone.clear()
        
    def set_data(self, name, type_name, inputs, outputs):
        self.name_input.setText(name)
        self.update_box_style(type_name)
        
        # Clear zones
        self.input_zone.clear()
        self.output_zone.clear()
        
        # Add inputs
        for p in inputs:
            wt_name = p["type"]
            color = "#ffffff"
            if wt_name in self.wire_types:
                color = self.wire_types[wt_name].color
            self.input_zone.add_port(wt_name, color, p["label"])
            
        # Add outputs
        for p in outputs:
            wt_name = p["type"]
            color = "#ffffff"
            if wt_name in self.wire_types:
                color = self.wire_types[wt_name].color
            self.output_zone.add_port(wt_name, color, p["label"])
