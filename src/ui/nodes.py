from PySide6.QtWidgets import QGraphicsItem, QGraphicsTextItem
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPainterPath
from core.graph import Node, Port

def get_abbreviated_label(name: str) -> str:
    if len(name) > 3:
        return name[:2] + name[-1]
    return name

class NodeItem(QGraphicsItem):
    def __init__(self, node: Node, signature=None):
        super().__init__()
        self.node = node
        self.signature = signature
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        
        self.width = 100
        self.height = 60
        self.radius = 10
        
        # Set position from node data
        self.setPos(node.position[0], node.position[1])
        
        # Colors
        self.color = QColor("#3c3c3c") # Default dark grey
        self.symbol = "?"
        
        if self.node.type_name == "Learnable":
            self.color = QColor("#000000") # Black
            self.symbol = "θ"
        elif self.node.type_name == "Function":
            self.color = QColor("#29adff") # Blue (or White as per new req?)
            # User said Function should be white in Signature, maybe here too?
            # Keeping Blue for now as per original spec, but can change if requested for canvas too.
            self.symbol = "ƒ"
        elif self.node.type_name == "Data":
            self.color = QColor("#29adff")
            self.symbol = "D"
        else:
            self.color = QColor(100, 100, 100)
            self.symbol = "?"

        self.hovered_port = None # (is_input, index)

    def hoverMoveEvent(self, event):
        # Check if hovering over a port
        port_info = self.get_port_at(event.pos())
        if port_info:
            port, _ = port_info
            # Find index
            if port.is_input:
                idx = self.node.inputs.index(port)
                self.hovered_port = (True, idx)
            else:
                idx = self.node.outputs.index(port)
                self.hovered_port = (False, idx)
        else:
            self.hovered_port = None
        
        self.update()
        super().hoverMoveEvent(event)

    def hoverLeaveEvent(self, event):
        self.hovered_port = None
        self.update()
        super().hoverLeaveEvent(event)

    def boundingRect(self) -> QRectF:
        # Add some margin for the pen width and selection border
        return QRectF(0, 0, self.width, self.height).adjusted(-2, -2, 2, 2)

    def paint(self, painter: QPainter, option, widget=None):
        # Draw Body
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width, self.height, self.radius, self.radius)
        
        painter.setBrush(self.color)
        painter.setPen(QPen(Qt.white, 2 if self.isSelected() else 0))
        painter.drawPath(path)
        
        # Draw Label
        painter.setPen(Qt.white)
        font = painter.font()
        font.setPointSize(12)
        font.setBold(True)
        painter.setFont(font)
        
        # Abbreviate label: First 2 chars + Last char if len > 3
        label = get_abbreviated_label(self.node.name)
            
        painter.drawText(self.boundingRect(), Qt.AlignCenter, label)
        
        # Draw Ports
        self.paint_ports(painter)

    def paint_ports(self, painter):
        # Inputs
        for i, port in enumerate(self.node.inputs):
            y = (i + 1) * (self.height / (len(self.node.inputs) + 1))
            pt = QPointF(0, y)
            
            # Get color from signature
            color = QColor("#888888")
            if self.signature and port.type_name in self.signature.wire_types:
                color = QColor(self.signature.wire_types[port.type_name].color)
            
            # Highlight if hovered
            if self.hovered_port == (True, i):
                color = QColor("white")
                painter.setBrush(QBrush(color))
                painter.setPen(QPen(Qt.white, 2)) # Glow effect?
                painter.drawEllipse(pt, 6, 6) # Slightly larger
            else:
                painter.setBrush(QBrush(color))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(pt, 4, 4)
            
        # Outputs
        for i, port in enumerate(self.node.outputs):
            y = (i + 1) * (self.height / (len(self.node.outputs) + 1))
            pt = QPointF(self.width, y)
            
            # Get color from signature
            color = QColor("#888888")
            if self.signature and port.type_name in self.signature.wire_types:
                color = QColor(self.signature.wire_types[port.type_name].color)

            # Highlight if hovered
            if self.hovered_port == (False, i):
                color = QColor("white")
                painter.setBrush(QBrush(color))
                painter.setPen(QPen(Qt.white, 2))
                painter.drawEllipse(pt, 6, 6)
            else:
                painter.setBrush(QBrush(color))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(pt, 4, 4)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            self.node.position = (value.x(), value.y())
            if self.scene():
                self.scene().node_moved.emit(self.node.id)
        return super().itemChange(change, value)

    def get_port_at(self, pos: QPointF) -> tuple[Port, QPointF] | None:
        # Check inputs
        for i, port in enumerate(self.node.inputs):
            y = (self.height / (len(self.node.inputs) + 1)) * (i + 1)
            p_pos = QPointF(0, y)
            if (pos - p_pos).manhattanLength() < 10:
                return port, self.mapToScene(p_pos)

        # Check outputs
        for i, port in enumerate(self.node.outputs):
            y = (self.height / (len(self.node.outputs) + 1)) * (i + 1)
            p_pos = QPointF(self.width, y)
            if (pos - p_pos).manhattanLength() < 10:
                return port, self.mapToScene(p_pos)
        
        return None
