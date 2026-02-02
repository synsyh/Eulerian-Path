import networkx as nx
import numpy as np

class GraphBuilder:
    def __init__(self, skeleton):
        self.skeleton = skeleton
        self.height, self.width = skeleton.shape
        self.graph = nx.MultiGraph()

    def build_graph(self):
        """
        Convert skeleton to NetworkX graph.
        Nodes: Junctions and Endpoints.
        Edges: Paths between nodes.
        """
        # 1. Identify all 1-pixels
        y_idxs, x_idxs = np.where(self.skeleton)
        pixels = set(zip(y_idxs, x_idxs))
        
        # 2. Identify Junctions and Endpoints
        junctions = []
        endpoints = []
        
        for y, x in pixels:
            neighbors = self._get_neighbors(y, x)
            count = len(neighbors)
            
            if count == 1:
                endpoints.append((y, x))
            elif count > 2:
                junctions.append((y, x))
                
        # Special case: Simple loop (0 endpoints, 0 junctions)
        # We need to arbitrarily pick a node if the skeleton exists but has no features.
        if not junctions and not endpoints and pixels:
             # Just pick an arbitrary start point
             endpoints.append(list(pixels)[0])

        all_nodes = set(junctions + endpoints)
        
        # Add nodes to graph
        for node in all_nodes:
            self.graph.add_node(node, type='junction' if node in junctions else 'endpoint')

        # 3. Trace edges between nodes
        visited_pixels = set()
        
        for node in all_nodes:
            # For each neighbor of a node, trace the path until we hit another node
            start_neighbors = self._get_neighbors(*node)
            
            for neighbor in start_neighbors:
                if neighbor in visited_pixels:
                    continue # This part of the path is already handled
                
                # Start tracing
                path = [node, neighbor]
                current = neighbor
                prev = node
                
                # Walk until we hit a node or a dead end
                while current not in all_nodes:
                    visited_pixels.add(current)
                    
                    neighbors = self._get_neighbors(*current)
                    # Filter out the pixel we just came from
                    next_steps = [n for n in neighbors if n != prev]
                    
                    if not next_steps:
                        break # Dead end (should be an endpoint node, but just in case)
                    
                    # In a clean skeleton, there should be exactly 1 next step unless we hit a junction
                    # However, strictly speaking, `current` is not a junction, so it has 2 neighbors total (prev and next)
                    # If it has >2 neighbors, it WOULD be in `all_nodes` (junction).
                    
                    prev = current
                    current = next_steps[0]
                    path.append(current)
                
                # `current` is now the end node (or should be)
                if current in all_nodes:
                    # In MultiGraph, we allow multiple edges between nodes if they are distinct paths.
                    # The `visited_pixels` logic ensures we don't re-trace the EXACT SAME path pixels twice.
                    # So we just add the edge.
                    
                    # Calculate length (Euclidean estimation or pixel count)
                    length = len(path) # Simple pixel count
                    self.graph.add_edge(node, current, weight=length, path=path)

        return self.graph

    def merge_close_nodes(self, distance_threshold=3.0):
        """
        Merge nodes that are very close to each other (e.g. fragments of the same intersection).
        Priority: Merge boolean 'junction' nodes first.
        """
        # Repeat until no more changes
        while True:
            # Find all edges shorter than threshold
            to_merge = []
            for u, v, data in self.graph.edges(data=True):
                # Calculate Euclidean distance between pixels u and v
                dist = np.sqrt((u[0] - v[0])**2 + (u[1] - v[1])**2)
                if dist < distance_threshold:
                    # We only want to merge if they are effectively the same structural point.
                    # Usually this happens at complex intersections.
                    to_merge = (u, v)
                    break
            
            if not to_merge:
                break
                
            u, v = to_merge
            # Merge v into u
            # new_node = u
            # contract_node(G, u, v) merges v into u
            self.graph = nx.contracted_nodes(self.graph, u, v, self_loops=False)

    def prune_graph(self, min_path_length=5):
        """
        Remove small spurs (short edges ending in a degree-1 node).
        """
        # Iteratively remove degree-1 nodes with short edges
        changed = True
        while changed:
            changed = False
            # Make a copy to iterate
            nodes = list(self.graph.nodes())
            for node in nodes:
                try:
                    if self.graph.degree(node) == 1:
                        neighbor = list(self.graph.neighbors(node))[0]
                        edge_data = self.graph.get_edge_data(node, neighbor)
                        if edge_data['weight'] < min_path_length:
                            self.graph.remove_node(node) # This also removes the edge
                            changed = True
                except (nx.NetworkXError, KeyError):
                    # Node might have been removed or changed content
                    # Node might have been removed or changed content
                    continue

    def _get_neighbors(self, y, x):
        """
        Return list of 8-connected neighbors that are True in the skeleton.
        """
        neighbors = []
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dy == 0 and dx == 0:
                    continue
                ny, nx = y + dy, x + dx
                if 0 <= ny < self.height and 0 <= nx < self.width:
                    if self.skeleton[ny, nx]:
                        neighbors.append((ny, nx))
        return neighbors
