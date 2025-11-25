from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from PySide6.QtCore import Qt, Signal, QPointF
from PySide6.QtGui import QPainter, QWheelEvent, QMouseEvent, QColor, QBrush
from .nodes import NodeItem
from .wires import WireItem
from core.graph import Node, Wire

class DiagramScene(QGraphicsScene):
    node_moved = Signal(str) # node_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSceneRect(0, 0, 32000, 32000)
        self.setBackgroundBrush(QBrush(QColor("#1e1e1e")))
        self.grid_size = 20
        self.canvas = parent

    def node_moved_callback(self, node_item): # Renamed to avoid conflict with signal
        if self.canvas:
            self.canvas.node_moved(node_item)

class DiagramCanvas(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = DiagramScene(self)
        self.scene.node_moved.connect(self.update_connected_wires)
        self.setScene(self.scene)
        
        # Rendering hints
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.TextAntialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # Navigation
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        
        # Hide scrollbars
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Enable Drop
        self.setAcceptDrops(True)
        
        self.node_items = {}
        self.wire_items = {}
        
        # Signals
        # We can't define signals on QGraphicsView easily without a subclass definition with QObject, 
        # but QGraphicsView inherits QWidget which inherits QObject.
        # However, defining signals inside __init__ is not possible.
        # I will add the signal definition to the class.

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            node_type = event.mimeData().text()
            pos = self.mapToScene(event.position().toPoint())
            
            # Emit signal or call callback
            # For now, let's assume a callback is set or use a direct method if we refactor
            if hasattr(self, 'on_node_dropped'):
                self.on_node_dropped(node_type, (pos.x(), pos.y()))
            
            event.accept()
        else:
            event.ignore()

    def set_signature(self, signature):
        self.signature = signature

    def add_node(self, node: Node):
        item = NodeItem(node, self.signature)
        self.scene.addItem(item)
        self.node_items[node.id] = item

    def add_wire(self, wire: Wire):
        source_item = self.node_items.get(wire.source_node_id)
        target_item = self.node_items.get(wire.target_node_id)
        
        if source_item and target_item:
            source_pos = self.get_port_scene_pos(source_item, wire.source_port_name, is_input=False)
            target_pos = self.get_port_scene_pos(target_item, wire.target_port_name, is_input=True)
            
            # Get color from signature
            color = QColor("white")
            if self.signature and wire.type_name in self.signature.wire_types:
                color = QColor(self.signature.wire_types[wire.type_name].color)
            
            item = WireItem(wire, source_pos, target_pos, color)
            self.scene.addItem(item)
            self.wire_items[wire.id] = item

    def get_port_scene_pos(self, node_item, port_name, is_input):
        # Calculate exact position based on port index
        # This duplicates logic in NodeItem.paint_ports, ideally should be shared
        node = node_item.node
        ports = node.inputs if is_input else node.outputs
        
        index = -1
        for i, p in enumerate(ports):
            if p.name == port_name: # Wait, port names might not be unique? They are unique per node side usually.
                # Actually we used labels as names? 
                # In handle_node_drop: node.add_input(label, type)
                # So port.name is the label.
                index = i
                break
        
        if index == -1:
            return node_item.scenePos() # Fallback
            
        y = (index + 1) * (node_item.height / (len(ports) + 1))
        x = 0 if is_input else node_item.width
        return node_item.scenePos() + QPointF(x, y)

    def node_moved(self, node_item):
        # Update connected wires
        # Inefficient to search all wires, but fine for small graphs
        # Better: maintain adjacency list in Canvas
        for wire_id, wire_item in self.wire_items.items():
            wire = wire_item.wire
            if wire.source_node_id == node_item.node.id:
                new_start = self.get_port_scene_pos(node_item, wire.source_port_name, is_input=False)
                wire_item.set_endpoints(new_start, wire_item.end_pos)
            elif wire.target_node_id == node_item.node.id:
                new_end = self.get_port_scene_pos(node_item, wire.target_port_name, is_input=True)
                wire_item.set_endpoints(wire_item.start_pos, new_end)

    def update_connected_wires(self, node_id):
        # Find all wires connected to this node
        for wire_id, wire_item in self.wire_items.items():
            wire = wire_item.wire
            if wire.source_node_id == node_id or wire.target_node_id == node_id:
                source_item = self.node_items.get(wire.source_node_id)
                target_item = self.node_items.get(wire.target_node_id)
                
                if source_item and target_item:
                    new_start = self.get_port_scene_pos(source_item, wire.source_port_name, is_input=False)
                    new_end = self.get_port_scene_pos(target_item, wire.target_port_name, is_input=True)
                    wire_item.set_endpoints(new_start, new_end)

    def remove_wire(self, wire_id):
        if wire_id in self.wire_items:
            item = self.wire_items[wire_id]
            self.scene.removeItem(item)
            del self.wire_items[wire_id]

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            item = self.itemAt(event.position().toPoint())
            if isinstance(item, NodeItem):
                # Check for port click
                pos = item.mapFromScene(self.mapToScene(event.position().toPoint()))
                port_info = item.get_port_at(pos)
                if port_info:
                    port, scene_pos = port_info
                    if not port.is_input: # Start drag from output
                        self.drag_start_port = port
                        self.drag_start_pos = scene_pos
                        self.temp_wire = WireItem(None, scene_pos, self.mapToScene(event.position().toPoint()))
                        self.scene.addItem(self.temp_wire)
                        return # Consume event

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if hasattr(self, 'temp_wire') and self.temp_wire:
            self.temp_wire.set_endpoints(self.drag_start_pos, self.mapToScene(event.position().toPoint()))
            return # Consume event
            
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if hasattr(self, 'temp_wire') and self.temp_wire:
            # Check for drop on input port
            item = self.itemAt(event.position().toPoint())
            if isinstance(item, NodeItem):
                pos = item.mapFromScene(self.mapToScene(event.position().toPoint()))
                port_info = item.get_port_at(pos)
                if port_info:
                    port, scene_pos = port_info
                    if port.is_input:
                        # Create Wire
                        # TODO: Check types
                        if hasattr(self, 'on_wire_created'):
                            self.on_wire_created(self.drag_start_port, port)
            
            # Cleanup
            self.scene.removeItem(self.temp_wire)
            self.temp_wire = None
            self.drag_start_port = None
            return

        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Backspace or event.key() == Qt.Key_Delete:
            # Delete selected items
            for item in self.scene.selectedItems():
                if isinstance(item, NodeItem):
                    # TODO: Notify main window to update graph
                    if hasattr(self, 'on_nodes_deleted'):
                        self.on_nodes_deleted([item.node.id])
                    self.scene.removeItem(item)
                    del self.node_items[item.node.id]
                elif isinstance(item, WireItem):
                    self.remove_wire(item.wire.id)
                    # Remove from graph
                    if item.wire.id in self.scene.canvas.graph.wires:
                        self.scene.canvas.graph.remove_wire(item.wire.id)
        else:
            super().keyPressEvent(event)
