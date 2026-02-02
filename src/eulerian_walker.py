import networkx as nx
import numpy as np
from src.geometry_utils import get_path_tangent, calculate_angle_score

class AngularWalker:
    def __init__(self, graph):
        """
        Args:
            graph: NetworkX MultiGraph (Eulerian or Semi-Eulerian).
        """
        self.graph = graph
        # Store visited edges as (u, v, key) tuple where u <= v to handle undirected ness
        self.visited_edges = set() 
        self.num_edges = len(graph.edges())

    def find_path(self):
        """
        Find an Eulerian path/circuit with angular optimization.
        Returns:
            list of (y, x) pixels.
        """
        # 1. Identify Start Node
        odd_nodes = [v for v in self.graph.nodes() if self.graph.degree(v) % 2 == 1]
        start_node = odd_nodes[0] if odd_nodes else list(self.graph.nodes())[0]

        # 2. Start initial tour
        # The tour is a list of segments: [(start, end, key, pixels)]
        tour = self._greedy_walk(start_node)
        
        # 3. Splice additional cycles if graph is not fully traversed
        # We iterate until we covered all edges or can't extend further
        while len(self.visited_edges) < self.num_edges:
            splice_idx = -1
            splice_node = None
            
            # Find a node in the current tour that has unused edges
            # We check the start node of each segment, and the end node of the last segment
            candidates = [seg[0] for seg in tour] + [tour[-1][1]]
            
            found = False
            for idx, node in enumerate(candidates):
                if self._has_unused_edges(node):
                    splice_node = node
                    # If idx is len(tour), we append to end.
                    # If idx < len(tour), we splice BEFORE segment[idx]
                    splice_idx = idx
                    found = True
                    break
            
            if not found:
                break # Should not happen if graph is connected component
            
            # Start a sub-cycle from splice_node
            # To optimize smoothness, we look at the vector arriving at splice_node?
            # Or departing?
            # We want the sub-cycle to flow well.
            # Simplified: Just run greedy walk from there.
            sub_tour = self._greedy_walk(splice_node)
            
            if not sub_tour:
                break
                
            # Splice
            # tour = tour[:idx] + sub_tour + tour[idx:]
            if splice_idx >= len(tour):
                tour.extend(sub_tour)
            else:
                tour[splice_idx:splice_idx] = sub_tour
                
        # 4. Convert tour to pixel list
        full_pixels = []
        for i, (u, v, k, pixels) in enumerate(tour):
            if i == 0:
                full_pixels.extend(pixels)
            else:
                # Avoid duplicating the join point
                # Check if last pixel matches first pixel of new segment
                if np.array_equal(full_pixels[-1], pixels[0]):
                    full_pixels.extend(pixels[1:])
                else:
                    full_pixels.extend(pixels)
                    
        return full_pixels

    def _greedy_walk(self, start_node, incoming_vector=None):
        """
        Walks as far as possible from start_node using greedy angular choice.
        Returns list of segments.
        """
        path = []
        curr = start_node
        curr_vec = incoming_vector
        
        while True:
            # 1. Find all available outgoing edges
            options = []
            if curr not in self.graph: break
            
            for nbr in self.graph[curr]:
                # MultiGraph: iterate keys
                for key, data in self.graph[curr][nbr].items():
                    if not self._is_visited(curr, nbr, key):
                        options.append((nbr, key, data))
            
            if not options:
                break # Stuck or finished cycle
            
            # 2. Choose best option
            # If multiple choices, pick the one with best angular score
            best_option = None
            best_score = -2.0
            best_pixels = None
            best_out_vec = None
            
            for nbr, key, data in options:
                # Get pixels 
                raw_pixels = data.get('path')
                if raw_pixels is None:
                     raw_pixels = [curr, nbr]
                
                # Orient pixels U -> V
                pixels = list(raw_pixels)
                p_start = np.array(pixels[0])
                p_end = np.array(pixels[-1])
                
                # Check if we need to reverse
                # Distance from current node (curr) to start of pixels
                d1 = np.sum((p_start - np.array(curr))**2)
                d2 = np.sum((p_end - np.array(curr))**2)
                
                if d2 < d1:
                    pixels = pixels[::-1]
                
                # Calculate vector of this outgoing path
                out_vec = get_path_tangent(pixels, from_start=True)
                
                # Calculate score
                score = 0.0
                if curr_vec is not None:
                    score = calculate_angle_score(curr_vec, out_vec)
                else:
                    score = 0.0 # First step, no preference (or could use heuristic)
                
                if score > best_score:
                    best_score = score
                    best_option = (nbr, key)
                    best_pixels = pixels
                    best_out_vec = out_vec
            
            # 3. Commit
            next_node, best_key = best_option
            self._mark_visited(curr, next_node, best_key)
            path.append((curr, next_node, best_key, best_pixels))
            
            # Update state
            curr = next_node
            # New "Incoming" vector is the direction we just arrived from.
            # Which is the direction of the END of the segment.
            # Tangent at end of pixels, pointing towards end?
            # Yes, velocity preserved.
            # get_path_tangent(reversed, from_start=True) gives vector pointing backwards.
            # So negate it.
            exit_tangent = get_path_tangent(best_pixels[::-1], from_start=True)
            curr_vec = -exit_tangent
            
        return path

    def _is_visited(self, u, v, key):
        if u > v:
            u, v = v, u
        return (u, v, key) in self.visited_edges

    def _mark_visited(self, u, v, key):
        if u > v:
            u, v = v, u
        self.visited_edges.add((u, v, key))

    def _has_unused_edges(self, u):
        if u not in self.graph: return False
        for nbr in self.graph[u]:
            for key in self.graph[u][nbr]:
                 if not self._is_visited(u, nbr, key):
                     return True
        return False
