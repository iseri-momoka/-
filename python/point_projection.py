"""
Point-to-Plane Projection
==========================
Reference: pntplane_projection.m

Given a set of 3D points and plane parameters (A, B, C, D) where
the plane equation is: Ax + By + Cz + D = 0,
compute the orthogonal projection of each point onto the plane.

Usage:
    python point_projection.py <input_csv> <A> <B> <C> <D> [output_csv]

Input CSV format:
    x1,y1,z1
    x2,y2,z2
    ...

Output: projected point coordinates.
"""

import sys
import os
import json
import numpy as np


def project_points_to_plane(points, A, B, C, D):
    """
    Project 3D points orthogonally onto plane Ax + By + Cz + D = 0.

    Parameters
    ----------
    points : ndarray (N, 3)
        Input point cloud.
    A, B, C, D : float
        Plane parameters.

    Returns
    -------
    projected : ndarray (N, 3)
        Projected point coordinates.
    """
    # Build coefficient matrix
    a11 = B * B + C * C
    a12 = -A * B
    a13 = -A * C
    a21 = -A * B
    a22 = A * A + C * C
    a23 = -B * C
    a31 = -A * C
    a32 = -B * C
    a33 = A * A + B * B

    a_matrix = np.array([
        [a11, a12, a13],
        [a21, a22, a23],
        [a31, a32, a33]
    ])

    b_vector = np.array([-A * D, -B * D, -C * D])

    # Normalize by (A^2 + B^2 + C^2) for numerical stability
    norm_sq = A * A + B * B + C * C
    if norm_sq > 1e-30:
        a_matrix /= norm_sq
        b_vector /= norm_sq

    # Project: p_proj = a_matrix * p + b_vector
    # points: (N, 3) -> projected: (N, 3)
    projected = (a_matrix @ points.T).T + b_vector

    return projected


def main():
    if len(sys.argv) < 6:
        print(json.dumps({"error": "Usage: point_projection.py <input_csv> <A> <B> <C> <D> [output_csv]"}))
        sys.exit(1)

    input_path = sys.argv[1]
    A = float(sys.argv[2])
    B = float(sys.argv[3])
    C = float(sys.argv[4])
    D = float(sys.argv[5])

    if not os.path.exists(input_path):
        print(json.dumps({"error": f"File not found: {input_path}"}))
        sys.exit(1)

    points = np.loadtxt(input_path, delimiter=',')
    if points.ndim != 2 or points.shape[1] != 3:
        print(json.dumps({"error": f"Expected Nx3 array, got shape {points.shape}"}))
        sys.exit(1)

    projected = project_points_to_plane(points, A, B, C, D)

    result = {
        "plane_params": {"A": A, "B": B, "C": C, "D": D},
        "num_points": int(points.shape[0]),
        "projected_points": projected.tolist()
    }

    if len(sys.argv) >= 7:
        output_path = sys.argv[6]
        # Save projected points as CSV
        np.savetxt(output_path, projected, delimiter=',',
                   header='x,y,z', comments='')
        print(f"Projected points written to {output_path}")
    else:
        # Print summary + first 10 points
        summary = {
            "plane_params": result["plane_params"],
            "num_points": result["num_points"],
            "first_10_projected": projected[:10].tolist()
        }
        print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
