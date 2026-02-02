import numpy as np

def get_path_tangent(path_pixels, from_start=True, num_points=5):
    """
    Calculate the tangent vector of a path at its start or end.
    
    Args:
        path_pixels (list or np.array): List of (y, x) pixels.
        from_start (bool): If True, calc vector pointing AWAY from start. 
                           If False, calc vector pointing INTO end? 
                           Wait, we always want the "outgoing" vector for the walker.
                           
                           If we are at Node U and walking edge E to Node V:
                           If path is stored U->V, we want vector at index 0 pointing to index N.
                           If path is stored V->U, we want vector at index 0 (which is V) pointing to index N?
                           
                           Let's simplify:
                           The walker is at `current_node` (pixel P0).
                           The path moves to `next_node` (pixel Pn).
                           We want the vector direction of the INITIAL SEGMENT of the walk.
                           
                           So we just take P[0] and P[k] (where k is small).
                           The vector is P[k] - P[0].
                           
        num_points (int): How many pixels ahead to look for tangent stability.
    
    Returns:
        np.array: Normalized vector (dy, dx).
    """
    if len(path_pixels) < 2:
        return np.array([0.0, 0.0])
    
    path = np.array(path_pixels)
    
    # We want vector from P[0] onwards.
    start_pt = path[0]
    
    # Check if path is long enough
    idx = min(len(path) - 1, num_points)
    end_pt = path[idx]
    
    # Vector
    vec = end_pt - start_pt # (dy, dx)
    
    norm = np.linalg.norm(vec)
    if norm == 0:
        return np.array([0.0, 0.0])
        
    return vec / norm

def calculate_angle_score(vec1, vec2):
    """
    Calculate alignment score between two normalized vectors.
    Range: [-1, 1].
    1.0 = Perfectly straight (0 degrees deviation).
    0.0 = 90 degrees turn.
    -1.0 = 180 degrees U-turn (worst).
    
    Args:
        vec1: Incoming vector (direction we were traveling).
        vec2: Outgoing vector (direction we want to travel).
        
    Returns:
        float: Dot product.
    """
    # Dot product of normalized vectors = cos(theta)
    # Cos(0) = 1 (Straight) -> Best
    # Cos(Pi) = -1 (U-turn) -> Worst
    return np.dot(vec1, vec2)
