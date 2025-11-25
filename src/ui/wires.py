from PySide6.QtWidgets import QGraphicsItem, QGraphicsPathItem
from PySide6.QtCore import Qt, QRectF, QPointF, QLineF
from PySide6.QtGui import QPainter, QColor, QPen, QPainterPath
from core.graph import Wire

class WireItem(QGraphicsPathItem):
    def __init__(self, wire: Wire, start_pos: QPointF, end_pos: QPointF, color: QColor = QColor("white")):
        super().__init__()
        self.wire = wire
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.color = color
        
        self.setZValue(-1) # Draw behind nodes
        self.setFlags(QGraphicsItem.ItemIsSelectable)
        self.update_path()

    def set_endpoints(self, start_pos: QPointF, end_pos: QPointF):
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.update_path()

    def update_path(self):
        path = QPainterPath()
        path.moveTo(self.start_pos)
        
        dx = self.end_pos.x() - self.start_pos.x()
        dy = self.end_pos.y() - self.start_pos.y()
        
        # Adjust control points for a smoother curve, potentially considering dy
        # For a horizontal-ish curve, dx is the primary factor
        ctrl1 = QPointF(self.start_pos.x() + dx * 0.5, self.start_pos.y())
        ctrl2 = QPointF(self.end_pos.x() - dx * 0.5, self.end_pos.y())
        
        path.cubicTo(ctrl1, ctrl2, self.end_pos)
        self.setPath(path)

    def boundingRect(self) -> QRectF:
        # Add generous margin for pen width and selection highlight
        return super().boundingRect().adjusted(-5, -5, 5, 5)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw selection highlight
        if self.isSelected():
            pen = QPen(Qt.white, 6)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(self.path())

        # Draw wire
        pen = QPen(self.color, 3)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(self.path())
