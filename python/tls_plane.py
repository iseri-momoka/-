"""
TLS Plane Fitting (Total Least Squares)
========================================
Reference: TLS_Plane.m

Given a 3D point cloud (Nx3), compute the best-fit plane using SVD-based
Total Least Squares.

The plane equation is: ax + by + cz + d = 0
Output: (a, b, c, d)

Usage:
    python tls_plane.py <input_csv> [output_csv]

Input CSV format:
    x1,y1,z1
    x2,y2,z2
    ...
    xN,yN,zN

If output_csv is provided, writes the result (a,b,c,d) to file.
Otherwise prints to stdout as JSON: {"a": ..., "b": ..., "c": ..., "d": ...}
"""

import sys
import os
import json
import numpy as np


def tls_plane_fit(points):
    """
    Fit a plane to 3D points using Total Least Squares (SVD).

    Parameters
    ----------
    points : ndarray (N, 3)
        Input point cloud.

    Returns
    -------
    a, b, c, d : float
        Plane parameters: ax + by + cz + d = 0
        (a, b, c) is the unit normal vector.
    """
    n = points.shape[0]
    mean_pt = np.mean(points, axis=0)  # (3,)
    M = points - mean_pt                # (N, 3)

    # SVD of M^T * M (3x3 matrix)
    MtM = M.T @ M
    U, S, Vt = np.linalg.svd(MtM)

    # The normal is the singular vector corresponding to the smallest singular value
    # U[:, 2] for a 3x3 SVD (singular values in descending order)
    a = float(U[0, 2])
    b = float(U[1, 2])
    c = float(U[2, 2])

    # Compute d from mean point
    d = -float(np.dot(mean_pt, np.array([a, b, c])))

    return a, b, c, d


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: tls_plane.py <input_csv> [output_csv]"}))
        sys.exit(1)

    input_path = sys.argv[1]
    if not os.path.exists(input_path):
        print(json.dumps({"error": f"File not found: {input_path}"}))
        sys.exit(1)

    # Load point cloud from CSV
    points = np.loadtxt(input_path, delimiter=',')
    if points.ndim != 2 or points.shape[1] != 3:
        print(json.dumps({"error": f"Expected Nx3 array, got shape {points.shape}"}))
        sys.exit(1)

    a, b, c, d = tls_plane_fit(points)

    result = {
        "a": a,
        "b": b,
        "c": c,
        "d": d,
        "equation": f"{a:.6f}x + {b:.6f}y + {c:.6f}z + {d:.6f} = 0",
        "num_points": int(points.shape[0])
    }

    if len(sys.argv) >= 3:
        output_path = sys.argv[2]
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        print(f"Result written to {output_path}")
    else:
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
