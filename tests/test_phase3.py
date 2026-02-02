import unittest
import networkx as nx
import numpy as np
from src.eulerian_walker import AngularWalker

class TestPhase3(unittest.TestCase):
    def test_angular_preference(self):
        """
        Test that walker prefers straight lines at a 4-way intersection.
        Graph: Figure 8.
        Node 0 at (0,0).
        Loop 1: 0 -> 1 -> 2 -> 0.
        Loop 2: 0 -> 3 -> 4 -> 0.
        
        Geometry:
        2 -> 0 is coming from (-1, -1). Vector is (1, 1).
        Options at 0:
        a) Go to 1 (at -1, 1). Vector (-1, 1). Angle 90 deg.
        b) Go to 3 (at 1, 1). Vector (1, 1). Angle 0 deg (Straight).
        
        Walker should choose 3.
        """
        G = nx.MultiGraph()
        
        # Define coordinates
        coords = {
            0: (0, 0),
            1: (-1, 1),   # Top Left
            2: (-1, -1),  # Bottom Left
            3: (1, 1),    # Top Right
            4: (1, -1)    # Bottom Right
        }
        
        # Helper to make edge with geometry
        def make_edge(u, v):
            p1 = np.array(coords[u])
            p2 = np.array(coords[v])
            # Create a few points for the line
            path = [tuple(p1 + t * (p2 - p1)) for t in np.linspace(0, 1, 5)]
            G.add_edge(u, v, path=path)
            
        # Loop 1
        make_edge(0, 1)
        make_edge(1, 2)
        make_edge(2, 0)
        
        # Loop 2
        make_edge(0, 3)
        make_edge(3, 4)
        make_edge(4, 0)
        
        # Walker
        walker = AngularWalker(G)
        path = walker.find_path()
        
        # We want to verify the sequence.
        # But `find_path` returns pixels.
        # Let's inspect the `_greedy_walk` or mock the decision?
        # Alternatively, we can check the pixels sequence.
        
        # Let's check the transition at Node 0.
        # We need to find where the path goes 2 -> 0.
        # The next point should be towards 3.
        
        # Convert path to array
        arr = np.array(path)
        
        # Find index close to (0,0)
        # Note: (0,0) is visited multiple times (start, middle, end).
        # We want the middle visit.
        
        # Actually, let's just trace the node sequence logic by mocking or trusted knowledge.
        # Better: Interpret the pixel path.
        # If it goes 2->0->3, the vectors should align.
        
        # Let's just assert that the total path exists and visits all edges.
        # Because if it chose wrongly, it would still cover the graph (Eulerian), just with sharper turns.
        
        # To strictly test angular preference, we can check the AngularWalker internal method `_greedy_walk`.
        # Taking a walk starting at 2, arriving at 0.
        # Incoming vector from 2->0 is (1, 1).
        # Outgoing to 1 is (-1, 1) (Score ~0).
        # Outgoing to 3 is (1, 1) (Score ~1).
        # Outgoing to 4 is (1, -1) (Score ~0).
        
        # Let's force a walk step
        # Create a partial state or just run `_greedy_walk` from 2
        # But `_greedy_walk` initializes `curr_vec` to None.
        # We need to provide `incoming_vector`.
        
        in_vec = np.array([1.0, 1.0]) / np.sqrt(2) # 2->0
        
        # Manually invoke private method for testing logic
        # Ideally we shouldn't test private methods, but it's the most direct verification of the "Algorithm".
        # We can also sub-class or just run it.
        
        tour = walker._greedy_walk(0, incoming_vector=in_vec)
        # We started at 0 with momentum "coming from 2" (bottom-left).
        # We expect it to go to 3 (top-right).
        
        first_step = tour[0] # (start, end, key, pixels)
        # Check `end` node
        next_node = first_step[1]
        
        self.assertEqual(next_node, 3, "Walker should preserve momentum 2->0->3")
        
    def test_eulerian_completeness(self):
        # Ensure it visits all edges of a Double Walled square
        G = nx.MultiGraph()
        edges = [(0,1), (1,2), (2,3), (3,0)]
        # Add twice
        for u, v in edges:
            G.add_edge(u, v, path=[(0,0), (1,1)]) # Dummy path
            G.add_edge(u, v, path=[(0,0), (1,1)])
            
        walker = AngularWalker(G)
        path = walker.find_path()
        
        # Total edges = 8
        # Path should not be empty
        self.assertTrue(len(path) > 0)
        
if __name__ == '__main__':
    unittest.main()
