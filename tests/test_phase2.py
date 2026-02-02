import unittest
import networkx as nx
from src.eulerian_logic import EulerianPathFinder

class TestPhase2(unittest.TestCase):
    def test_perfect_loop_circuit(self):
        # A triangle
        G = nx.MultiGraph()
        G.add_edge(1, 2)
        G.add_edge(2, 3)
        G.add_edge(3, 1)
        
        finder = EulerianPathFinder(G)
        self.assertEqual(finder.analyze(), 'circuit')
        self.assertTrue(nx.is_eulerian(G))
        
        # Make Eulerian should do nothing
        G2 = finder.make_eulerian()
        self.assertEqual(len(G2.edges()), 3)

    def test_single_path(self):
        # A line 1-2-3
        G = nx.MultiGraph()
        G.add_edge(1, 2)
        G.add_edge(2, 3)
        
        finder = EulerianPathFinder(G)
        self.assertEqual(finder.analyze(), 'path')
        self.assertFalse(nx.is_eulerian(G))
        self.assertTrue(nx.is_semieulerian(G))
        
        # Make Eulerian should do nothing (unless forced)
        G2 = finder.make_eulerian()
        self.assertEqual(len(G2.edges()), 2)

    def test_double_wall_complex(self):
        # A T-shape (Star graph with center 0 and leaves 1, 2, 3)
        # Odd nodes: 1, 2, 3 (degree 1) and 0 (degree 3). Total 4 odd nodes.
        G = nx.MultiGraph()
        G.add_edge(0, 1)
        G.add_edge(0, 2)
        G.add_edge(0, 3)
        
        finder = EulerianPathFinder(G)
        self.assertEqual(finder.analyze(), 'non-eulerian')
        
        # Should apply double wall
        G_euler = finder.make_eulerian()
        
        # Now every edge should be doubled. Total edges 3 -> 6
        self.assertEqual(len(G_euler.edges()), 6)
        
        # Degrees should all be even
        # Node 0: 6 (originally 3)
        # Node 1: 2 (originally 1)
        for n in G_euler.nodes():
            self.assertTrue(G_euler.degree(n) % 2 == 0)
            
        self.assertTrue(nx.is_eulerian(G_euler))

if __name__ == '__main__':
    unittest.main()
