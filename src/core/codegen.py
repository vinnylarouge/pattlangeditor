import json
from .graph import Graph, Node, Wire
from .signature import Signature

class CodeGenerator:
    def __init__(self, signature: Signature, graph: Graph, choices: dict):
        self.signature = signature
        self.graph = graph
        self.choices = choices
        self.wires_dims = choices["wires"]
        self.morphisms_code = choices["morphisms"]
        self.general = choices["general"]

    def generate_notebook(self) -> str:
        cells = []
        
        # 1. Setup Cell
        setup_code = """import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")
"""
        cells.append(self.create_code_cell(setup_code))
        
        # 2. Model Definition Cell
        model_code = self.generate_model_class()
        cells.append(self.create_code_cell(model_code))
        
        # 3. Training Loop Cell
        train_code = self.generate_training_loop()
        cells.append(self.create_code_cell(train_code))
        
        notebook = {
            "cells": cells,
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3"
                }
            },
            "nbformat": 4,
            "nbformat_minor": 4
        }
        return json.dumps(notebook, indent=2)

    def create_code_cell(self, source):
        return {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": source.splitlines(keepends=True)
        }

    def generate_model_class(self) -> str:
        # Topological sort for forward pass
        sorted_nodes = self.topological_sort()
        
        code = "class GeneratedModel(nn.Module):\n"
        code += "    def __init__(self):\n"
        code += "        super().__init__()\n"
        
        # Define submodules (Learnable morphisms)
        # We need to instantiate them.
        # If a morphism is used multiple times, do we share weights or not?
        # Graph nodes are instances. If they share the same morphism name, 
        # usually in this editor "Morphism" is the type/definition.
        # So "Encoder" is a definition. If I drop two "Encoder"s, are they shared?
        # In a diagram editor, usually nodes are instances.
        # But if I want shared weights, I might need a specific "Shared" flag or reuse the same name?
        # For now, let's assume unique instances per node unless explicitly shared (not implemented).
        # OR: The user defines "Encoder" code. We instantiate it for each node.
        
        for node_id, node in self.graph.nodes.items():
            if node.type_name == "Learnable":
                # Get code from choices
                impl = self.morphisms_code.get(node.name, "nn.Identity()")
                # We need to resolve "?" dimensions if present
                # This is complex without type inference. 
                # For now, assume user replaced ? with numbers in the dialog.
                safe_name = f"{node.name}_{node_id[-4:]}".replace("-", "_") # Unique name
                code += f"        self.{safe_name} = {impl}\n"
                
        code += "\n    def forward(self, x):\n"
        code += "        # Data flow tracking\n"
        code += "        # Assuming single input 'x' for now or dictionary?\n"
        code += "        # Let's use a dictionary for wires\n"
        code += "        wires = {}\n"
        
        # Find input nodes (no incoming wires) or specific "Input" nodes?
        # We don't have explicit "Input" nodes in the graph structure yet, 
        # usually inputs are just open ports or specific Data nodes.
        # Let's assume there's a node named "Input" or we take arguments.
        # Simpler: Just pass a dict of inputs matching the graph's open inputs.
        
        code += "        if isinstance(x, dict):\n"
        code += "            wires.update(x)\n"
        code += "        else:\n"
        code += "            # Fallback: assign x to first open input found (risky)\n"
        code += "            pass\n\n"
        
        for node_id in sorted_nodes:
            node = self.graph.nodes[node_id]
            
            # Gather inputs
            args = []
            for port in node.inputs:
                # Find wire connected to this port
                wire_found = False
                for wire in self.graph.wires.values():
                    if wire.target_node_id == node_id and wire.target_port_name == port.name:
                        args.append(f"wires['{wire.id}']")
                        wire_found = True
                        break
                if not wire_found:
                    # Open input
                    args.append(f"wires.get('input_{node.name}_{port.name}', torch.zeros(1))") # Placeholder
            
            # Call
            safe_name = f"{node.name}_{node_id[-4:]}".replace("-", "_")
            
            if node.type_name == "Learnable":
                call = f"self.{safe_name}({', '.join(args)})"
            elif node.type_name == "Function":
                impl = self.morphisms_code.get(node.name, "F.relu")
                call = f"{impl}({', '.join(args)})"
            else:
                call = f"wires['{args[0]}']" if args else "None" # Pass through?
            
            # Assign outputs
            # Assuming single output for now or tuple unpacking
            if len(node.outputs) == 1:
                # Find wire connected to output
                # Actually we store result by wire ID connected to output?
                # Or just store by output port ID?
                # We need to know which wire originates here.
                out_wire_ids = []
                for wire in self.graph.wires.values():
                    if wire.source_node_id == node_id and wire.source_port_name == node.outputs[0].name:
                        out_wire_ids.append(wire.id)
                
                if out_wire_ids:
                    # Assign result to all connected wires (implicit copy)
                    for wid in out_wire_ids:
                        code += f"        wires['{wid}'] = {call}\n"
                else:
                    # No output wire, just compute
                    code += f"        _ = {call}\n"
            else:
                # Multiple outputs (tuple)
                # TODO: Handle tuple unpacking
                pass
                
        code += "        return wires\n"
        return code

    def generate_training_loop(self) -> str:
        bs = self.general.get("batch_size", "32")
        lr = self.general.get("lr", "0.001")
        epochs = self.general.get("epochs", "10")
        optim_name = self.general.get("optimizer", "Adam")
        
        code = f"""# Hyperparameters
BATCH_SIZE = {bs}
LR = {lr}
EPOCHS = {epochs}

model = GeneratedModel().to(device)
optimizer = optim.{optim_name}(model.parameters(), lr=LR)
criterion = nn.MSELoss() # Default

# Dummy Data
# TODO: Generate based on input/output dimensions
x_train = torch.randn(100, 10) # Placeholder
y_train = torch.randn(100, 10) # Placeholder

dataset = TensorDataset(x_train, y_train)
loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)

print("Starting training...")
for epoch in range(EPOCHS):
    total_loss = 0
    for x, y in loader:
        x, y = x.to(device), y.to(device)
        
        optimizer.zero_grad()
        # Wrap input in dict if needed by model
        outputs = model({{'input_0': x}}) 
        # Extract output
        # pred = outputs['wire_id_of_output']
        # loss = criterion(pred, y)
        loss = torch.tensor(0.0, requires_grad=True) # Placeholder
        
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
        
    print(f"Epoch {{epoch+1}}/{{EPOCHS}}, Loss: {{total_loss/len(loader)}}")
"""
        return code

    def topological_sort(self):
        # Simple Kahn's algorithm
        # Build adjacency
        adj = {n: [] for n in self.graph.nodes}
        in_degree = {n: 0 for n in self.graph.nodes}
        
        for wire in self.graph.wires.values():
            u = wire.source_node_id
            v = wire.target_node_id
            if u in adj and v in in_degree:
                adj[u].append(v)
                in_degree[v] += 1
                
        queue = [n for n in self.graph.nodes if in_degree[n] == 0]
        result = []
        
        while queue:
            u = queue.pop(0)
            result.append(u)
            
            for v in adj[u]:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)
                    
        return result
