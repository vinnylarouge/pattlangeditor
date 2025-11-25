from typing import List, Optional
from .graph import Graph
import copy

class StateManager:
    def __init__(self):
        self.history: List[Graph] = []
        self.current_index: int = -1
        self.current_graph: Graph = Graph()
        self.push_state() # Initial state

    def push_state(self):
        # Remove any forward history if we are in the middle of the stack
        if self.current_index < len(self.history) - 1:
            self.history = self.history[:self.current_index + 1]
        
        # Deep copy the current graph to save it
        self.history.append(copy.deepcopy(self.current_graph))
        self.current_index += 1

    def undo(self) -> Optional[Graph]:
        if self.current_index > 0:
            self.current_index -= 1
            self.current_graph = copy.deepcopy(self.history[self.current_index])
            return self.current_graph
        return None

    def redo(self) -> Optional[Graph]:
        if self.current_index < len(self.history) - 1:
            self.current_index += 1
            self.current_graph = copy.deepcopy(self.history[self.current_index])
            return self.current_graph
        return None
