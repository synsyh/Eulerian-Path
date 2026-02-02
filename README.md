
# Eulerian Path Generator

A Python toolkit for converting raster images (like drawings or shapes) into continuous, non-overlapping Eulerian paths. This is ideal for applications like 3D printing (continuous extrusion), pen plotting, or single-line art.

## Features

- **Image Preprocessing**: Converts input images to binary skeletons.
- **Graph Construction**: Builds a mathematical graph from pixel skeletons, identifying junctions and endpoints.
- **Eulerian Transformation**: Analyzes the graph and ensures an Eulerian path exists (using the "Double Wall" technique for robust coverage).
- **Smooth Path Generation**: Uses an Angular Walker to generate smooth, continuous paths that minimize sharp turns.
- **Visualization**: Animated visualization of the path generation process, including multi-color support for double-wall traversal.

## Installation

1.  Clone this repository.
2.  Install the required dependencies using pip:

    ```bash
    pip install -r requirements.txt
    ```

    *Recommended: use a virtual environment.*
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

## Usage

### Command Line
You can process a single image directly from the command line:

```bash
python process_image.py path/to/your/image.png --max_size 1024
```

This will generate a visualization result image (`_result.png`) in the current directory.

### Interactive Visualization (Jupyter Notebook)
For an interactive experience and to see the path construction animation:

1.  Start Jupyter Notebook:
    ```bash
    jupyter notebook
    ```
2.  Open `notebooks/visualization.ipynb`.
3.  Run the cells to load an image, process it, and view the animated path generation.

## Project Structure

- `src/`: Core logic modules.
  - `image_processor.py`: Image loading and skeletonization.
  - `graph_builder.py`: Conversion of skeletons to graph nodes/edges.
  - `eulerian_logic.py`: Graph analysis and Eulerian transformation algorithms.
  - `path_generator.py`: Continuous path walking logic.
- `notebooks/`: Jupyter notebooks for demos and visualization.
- `tests/`: Unit tests for verification.
- `samples/`: Sample input images (if available).

## Requirements

- Python 3.8+
- `numpy`
- `matplotlib`
- `networkx`
- `scikit-image`
- `opencv-python`
- `jupyter`
