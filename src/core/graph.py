from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import uuid

@dataclass
class Port:
    name: str
    type_name: str
    is_input: bool
    node_id: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

@dataclass
class Node:
    name: str
    type_name: str  # "Learnable", "Function", "Copy", "Delete", or custom
    position: Tuple[float, float]
    inputs: List[Port] = field(default_factory=list)
    outputs: List[Port] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def add_input(self, name: str, type_name: str) -> Port:
        port = Port(name, type_name, True, self.id)
        self.inputs.append(port)
        return port

    def add_output(self, name: str, type_name: str) -> Port:
        port = Port(name, type_name, False, self.id)
        self.outputs.append(port)
        return port

@dataclass
class Wire:
    source_node_id: str
    source_port_name: str
    target_node_id: str
    target_port_name: str
    type_name: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

class Graph:
    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.wires: Dict[str, Wire] = {}

    def clear(self):
        self.nodes.clear()
        self.wires.clear()

    def add_node(self, node: Node):
        self.nodes[node.id] = node

    def remove_node(self, node_id: str) -> List[str]:
        if node_id in self.nodes:
            del self.nodes[node_id]
            # Remove connected wires
            wires_to_remove = []
            for wire_id, wire in self.wires.items():
                if wire.source_node_id == node_id or wire.target_node_id == node_id:
                    wires_to_remove.append(wire_id)
            
            for wire_id in wires_to_remove:
                del self.wires[wire_id]
                
            return wires_to_remove # Return removed wire IDs
        return []

    def add_wire(self, source_node_id: str, source_port_name: str, 
                 target_node_id: str, target_port_name: str, type_name: str) -> Optional[Wire]:
        # Validation
        # Check if target input already has a wire (unless monoidal - TODO: check type definition)
        # For now, assume non-monoidal means single input
        for wire in self.wires.values():
            if wire.target_node_id == target_node_id and wire.target_port_name == target_port_name:
                # Input already connected
                # TODO: Check if type is monoidal
                return None

        wire = Wire(source_node_id, source_port_name, target_node_id, target_port_name, type_name)
        self.wires[wire.id] = wire
        return wire

    def remove_wire(self, wire_id: str):
        if wire_id in self.wires:
            del self.wires[wire_id]
