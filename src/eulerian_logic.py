import networkx as nx
import copy

class EulerianPathFinder:
    def __init__(self, graph):
        # working on a copy to avoid mutating the original until intended
        self.graph = copy.deepcopy(graph)

    def count_odd_nodes(self):
        """
        Return count and list of nodes with odd degree.
        """
        odd_nodes = [v for v, d in self.graph.degree() if d % 2 == 1]
        return len(odd_nodes), odd_nodes

    def analyze(self):
        """
        Determine the type of Eulerian path possible:
        - 'circuit': 0 odd nodes (e.g. circle)
        - 'path': 2 odd nodes (e.g. line)
        - 'non-eulerian': >2 odd nodes (e.g. T-junction)
        """
        count, _ = self.count_odd_nodes()
        if count == 0:
            return 'circuit'
        elif count == 2:
            return 'path'
        else:
            return 'non-eulerian'

    def make_eulerian(self, force_double_wall=False):
        """
        Make the graph Eulerian.
        Strategy:
        1. If 'circuit' or 'path' and NOT force_double_wall: Do nothing.
        2. If 'non-eulerian' OR force_double_wall: Apply Double Wall transformation.
           Duplicate every edge. All degrees become even.
        
        Returns:
            The modified MultiGraph which is now Eulerian.
        """
        analysis = self.analyze()
        
        if analysis == 'non-eulerian' or force_double_wall:
            # Apply Double Wall: Duplicate every edge
            # For every u,v edge, add another one.
            # We iterate over a list of edges since we are modifying the graph
            original_edges = list(self.graph.edges(data=True, keys=True))
            
            for u, v, key, data in original_edges:
                # Add a parallel edge
                # We do not strictly need to reverse the path pixels yet, 
                # but physically the printer goes forward then backward.
                # Since the graph is undirected, we just add the edge.
                # When optimizing path later, we will handle traversal direction.
                
                # Clone data
                new_data = copy.deepcopy(data)
                # Optionally mark as 'double_wall_pair' if needed later
                new_data['type'] = 'double_wall'
                
                self.graph.add_edge(u, v, **new_data)
                
        return self.graph

    def is_eulerian(self):
        return nx.is_eulerian(self.graph)

    def is_semi_eulerian(self):
        return nx.is_semieulerian(self.graph)
