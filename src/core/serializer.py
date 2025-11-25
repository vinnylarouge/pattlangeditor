import json
from dataclasses import asdict
from .graph import Graph, Node, Wire, Port
from .signature import Signature, WireType, Morphism, Relation

class Serializer:
    @staticmethod
    def to_json(signature: Signature, graph: Graph) -> str:
        data = {
            "signature": {
                "wire_types": {k: asdict(v) for k, v in signature.wire_types.items()},
                "morphisms": {k: asdict(v) for k, v in signature.morphisms.items()},
                "relations": {k: asdict(v) for k, v in signature.relations.items()}
            },
            "graph": {
                "nodes": {k: asdict(v) for k, v in graph.nodes.items()},
                "wires": {k: asdict(v) for k, v in graph.wires.items()}
            }
        }
        return json.dumps(data, indent=2)

    @staticmethod
    def from_json(json_str: str) -> tuple[Signature, Graph]:
        data = json.loads(json_str)
        
        # Reconstruct Signature
        sig = Signature()
        sig_data = data.get("signature", {})
        
        for k, v in sig_data.get("wire_types", {}).items():
            sig.wire_types[k] = WireType(**v)
            
        for k, v in sig_data.get("morphisms", {}).items():
            sig.morphisms[k] = Morphism(**v)
            
        for k, v in sig_data.get("relations", {}).items():
            sig.relations[k] = Relation(**v)
            
        # Reconstruct Graph
        graph = Graph()
        graph_data = data.get("graph", {})
        
        for k, v in graph_data.get("nodes", {}).items():
            # Reconstruct Ports separately or let Node init handle it?
            # Node init creates empty lists. We need to populate them.
            # asdict converts nested dataclasses (Ports) to dicts.
            # So v["inputs"] is a list of dicts.
            
            inputs_data = v.pop("inputs", [])
            outputs_data = v.pop("outputs", [])
            
            node = Node(**v)
            # Restore ports
            node.inputs = [Port(**p) for p in inputs_data]
            node.outputs = [Port(**p) for p in outputs_data]
            
            graph.nodes[k] = node
            
        for k, v in graph_data.get("wires", {}).items():
            graph.wires[k] = Wire(**v)
            
        return sig, graph
