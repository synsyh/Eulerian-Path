import argparse
import sys
import os
import matplotlib.pyplot as plt
import numpy as np
import networkx as nx

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.image_processor import ImageProcessor
from src.graph_builder import GraphBuilder
from src.eulerian_logic import EulerianPathFinder
from src.path_generator import PathGenerator

def process_file(file_path, max_size=1024):
    print(f"Processing file: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return

    # 1. Processing
    print("Step 1: Image Processing & Skeletonization...")
    processor = ImageProcessor(image_path=file_path, max_dimension=max_size)
    processor.preprocess()
    skeleton = processor.get_skeleton()
    
    # 2. Graph Building
    print("Step 2: Building Graph from Skeleton...")
    builder = GraphBuilder(skeleton)
    builder.build_graph()
    # Apply refinements
    if hasattr(builder, 'merge_close_nodes'):
        builder.merge_close_nodes(distance_threshold=5.0)
    builder.prune_graph(min_path_length=10)
    G = builder.graph
    
    print(f"    Raw Graph Nodes: {len(G.nodes())}")
    print(f"    Raw Graph Edges: {len(G.edges())}")

    # 3. Eulerian Logic
    print("Step 3: Analyzing Connectivity...")
    euler = EulerianPathFinder(G)
    status = euler.analyze()
    odd_count, _ = euler.count_odd_nodes()
    print(f"    Topology Status: {status.upper()} (Odd Nodes: {odd_count})")
    
    G_final = euler.make_eulerian(force_double_wall=False)
    print(f"    Target Graph Edges: {len(G_final.edges())}")
    
    # 4. Path Generation
    print("Step 4: Generating Continuous Path...")
    generator = PathGenerator(G_final)
    try:
        path = generator.generate_path()
        print(f"    Success! Path generated with {len(path)} pixels.")
    except Exception as e:
        print(f"    Error generating path: {e}")
        return

    # 5. Visualization (Static Plot)
    print("Step 5: Saving Visualization...")
    plt.figure(figsize=(10, 10))
    plt.imshow(skeleton, cmap='gray')
    
    path_arr = np.array(path)
    # Color mapping for path progress (Start=Blue -> End=Red)
    # This helps see the stitching
    plt.scatter(path_arr[:, 1], path_arr[:, 0], c=np.arange(len(path)), cmap='plasma', s=1, alpha=0.5)
    
    output_filename = os.path.basename(file_path) + "_result.png"
    plt.title(f"Processed: {os.path.basename(file_path)}\nPath Length: {len(path)} px")
    plt.savefig(output_filename)
    print(f"    Visualization saved to {output_filename}")
    
    # Optional: Save numpy path
    # np.save(file_path + ".npy", path_arr)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process an image into a continuous Eulerian path.")
    parser.add_argument("input_file", help="Path to the input image file (png, jpg, etc.)")
    parser.add_argument("--max_size", type=int, default=1024, help="Max dimension for image resizing (default: 1024)")
    
    args = parser.parse_args()
    process_file(args.input_file, args.max_size)
