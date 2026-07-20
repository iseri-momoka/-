"""
KNN Search (K-Nearest Neighbors)
================================
Uses scipy.spatial.KDTree for efficient nearest neighbor search.

Given a point cloud (Nx3) and a parameter K, finds the K nearest neighbors
for each point. The first neighbor is always the point itself (distance 0).

Usage:
    python knn_search.py <input_csv> <K> [output_json]

Input CSV format:
    x1,y1,z1
    x2,y2,z2
    ...

Output: JSON with neighbor indices and distances for each point.
"""

import sys
import os
import json
import numpy as np
from scipy.spatial import KDTree


def knn_search(points, k):
    """
    Find K nearest neighbors for each point.

    Parameters
    ----------
    points : ndarray (N, 3)
        Input point cloud.
    k : int
        Number of nearest neighbors (including self).

    Returns
    -------
    indices : ndarray (N, K)
        Indices of K nearest neighbors.
    distances : ndarray (N, K)
        Distances to K nearest neighbors.
    """
    tree = KDTree(points)
    distances, indices = tree.query(points, k=k)

    return indices, distances


def main():
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: knn_search.py <input_csv> <K> [output_json]"}))
        sys.exit(1)

    input_path = sys.argv[1]
    k = int(sys.argv[2])

    if not os.path.exists(input_path):
        print(json.dumps({"error": f"File not found: {input_path}"}))
        sys.exit(1)

    if k < 1:
        print(json.dumps({"error": f"K must be >= 1, got {k}"}))
        sys.exit(1)

    points = np.loadtxt(input_path, delimiter=',')
    if points.ndim != 2 or points.shape[1] != 3:
        print(json.dumps({"error": f"Expected Nx3 array, got shape {points.shape}"}))
        sys.exit(1)

    n = points.shape[0]
    if k > n:
        k = n

    indices, distances = knn_search(points, k)

    result = {
        "num_points": n,
        "K": k,
        "indices": indices.tolist(),
        "distances": distances.tolist(),
        "summary": {
            "mean_nearest_distance": float(np.mean(distances[:, 1])) if k > 1 else 0.0,
            "max_nearest_distance": float(np.max(distances[:, 1])) if k > 1 else 0.0,
            "mean_kth_distance": float(np.mean(distances[:, -1])),
            "max_kth_distance": float(np.max(distances[:, -1]))
        }
    }

    if len(sys.argv) >= 4:
        output_path = sys.argv[3]
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        print(f"KNN results written to {output_path}")
    else:
        # Print summary only (full output is large)
        summary_out = {
            "num_points": result["num_points"],
            "K": result["K"],
            "summary": result["summary"],
            "first_5_indices": indices[:5].tolist(),
            "first_5_distances": distances[:5].tolist()
        }
        print(json.dumps(summary_out, indent=2))


if __name__ == '__main__':
    main()
