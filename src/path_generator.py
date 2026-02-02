import networkx as nx
from src.eulerian_walker import AngularWalker

class PathGenerator:
    def __init__(self, graph):
        self.graph = graph

    def generate_path(self):
        """
        Generate a sequence of points (pixels) representing the continuous path.
        Uses AngularWalker to optimize for smoothest turns.
        Returns:
            list of (y, x) tuples.
        """
        # 1. Check if Eulerian or Semi-Eulerian
        if not nx.is_eulerian(self.graph) and not nx.is_semieulerian(self.graph):
             raise ValueError("Graph is not Eulerian/Semi-Eulerian. Apply 'Double Wall' first.")

        # 2. Use AngularWalker to find best path
        walker = AngularWalker(self.graph)
        full_pixel_path = walker.find_path()
                
        return full_pixel_path
