from dataclasses import dataclass, field
from typing import List, Dict, Optional
import uuid

@dataclass
class WireType:
    name: str
    color: str # Hex color
    is_monoidal: bool = False
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

@dataclass
class Morphism:
    name: str
    type_name: str # "Learnable", "Function", "Data"
    inputs: List[Dict[str, str]] # List of {"type": str, "label": str}
    outputs: List[Dict[str, str]] # List of {"type": str, "label": str}
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

@dataclass
class Relation:
    name: str
    morphism_1: str
    morphism_2: str
    divergence: str # "KL", "MSE", etc.
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

class Signature:
    def __init__(self):
        self.wire_types: Dict[str, WireType] = {}
        self.morphisms: Dict[str, Morphism] = {}
        self.relations: Dict[str, Relation] = {}
        
        # Start Empty as per new requirements
        # self.add_wire_type("Image", "#29adff")
        # self.add_wire_type("Latent", "#ffa300")
        # self.add_wire_type("Label", "#00e436")
        
        # self.add_morphism("Encoder", "Learnable", ["Image"], ["Latent"])
        # self.add_morphism("Decoder", "Learnable", ["Latent"], ["Image"])

    def clear(self):
        self.wire_types.clear()
        self.morphisms.clear()
        self.relations.clear()

    def add_wire_type(self, name: str, color: str, is_monoidal: bool = False):
        wt = WireType(name, color, is_monoidal)
        self.wire_types[name] = wt
        return wt

    def add_morphism(self, name: str, type_name: str, inputs: List[Dict[str, str]], outputs: List[Dict[str, str]]):
        m = Morphism(name, type_name, inputs, outputs)
        self.morphisms[name] = m
        return m

    def add_relation(self, name: str, m1: str, m2: str, divergence: str):
        r = Relation(name, m1, m2, divergence)
        self.relations[name] = r
        return r
