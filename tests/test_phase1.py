import unittest
import numpy as np
import networkx as nx
from src.image_processor import ImageProcessor
from src.graph_builder import GraphBuilder

class TestPhase1(unittest.TestCase):
    def setUp(self):
        # Create a synthetic image: A black cross on white background (standard drawing)
        # 20x20 image, uint8, background 255
        self.img = np.full((20, 20), 255, dtype=np.uint8)
        # Vertical line (black)
        self.img[2:18, 10] = 0
        # Horizontal line (crossing at 2:18, 10)
        self.img[10, 2:18] = 0
        
        # Note: skeletonize might result in slightly different pixels depending on the algorithm,
        # but a cross should have 4 endpoints and 1 junction (center).

    def test_pipeline(self):
        # 1. Processing
        processor = ImageProcessor(image_array=self.img)
        processor.preprocess()
        skeleton = processor.get_skeleton()
        
        # 2. Graph Build
        builder = GraphBuilder(skeleton)
        G = builder.build_graph()
        
        print(f"Nodes: {G.nodes()}")
        print(f"Edges: {G.edges()}")
        
        # 3. Assertions
        # We expect 5 nodes: 1 center (degree 4), 4 tips (degree 1)
        # OR, depending on skeletonization artifacts, it might be slightly complex,
        # but let's check general topology.
        
        degrees = [d for n, d in G.degree()]
        dict_degrees = dict(G.degree())
        
        # Count endpoints (degree 1)
        endpoints = [n for n, d in G.degree() if d == 1]
        # Count junctions (degree > 2)
        junctions = [n for n, d in G.degree() if d > 2]
        
        print(f"Endpoints: {len(endpoints)}")
        print(f"Junctions: {len(junctions)}")

        # Allow for some small variation but generally expectations:
        self.assertTrue(len(endpoints) >= 3, "Should have at least 3 endpoints (likely 4)")
        self.assertTrue(len(junctions) >= 1, "Should have at least 1 junction")
        
        # Test pruning (optional manual check)
        builder.prune_graph(min_path_length=2)
        
    def test_merge_nodes(self):
        # Create a builder with a dummy skeleton (won't be used directly for this test)
        # We will manually populate the graph to test the merge logic
        dummy_skel = np.zeros((10,10))
        builder = GraphBuilder(dummy_skel)
        
        # Add two very close nodes (dist = 1.0)
        n1 = (5, 5)
        n2 = (5, 6)
        builder.graph.add_node(n1, type='junction')
        builder.graph.add_node(n2, type='junction')
        builder.graph.add_edge(n1, n2, weight=1)
        
        # Add a neighbor to n2 so it's not isolated
        n3 = (8, 8) 
        builder.graph.add_node(n3, type='endpoint')
        builder.graph.add_edge(n2, n3, weight=5)
        
        print(f"Before merge: {len(builder.graph.nodes())} nodes")
        self.assertEqual(len(builder.graph.nodes()), 3)
        
        # Merge
        builder.merge_close_nodes(distance_threshold=2.0)
        
        print(f"After merge: {len(builder.graph.nodes())} nodes")
        self.assertEqual(len(builder.graph.nodes()), 2)
        
        # Check that edge exists from the merged node to n3
        # The remaining node should be n1 or n2.
        remaining = list(builder.graph.nodes())
        self.assertIn(n3, remaining)
        self.assertTrue(builder.graph.has_edge(remaining[0], remaining[1]))


if __name__ == '__main__':
    unittest.main()
