"""
Rotation Matrix Computation
============================
Reference: Rotation_matrix.m

Computes the 3x3 rotation matrix that rotates normal vector v1 to align
with normal vector v2. Uses quaternion representation.

Usage:
    python rotation_matrix.py <x1> <y1> <z1> <x2> <y2> <z2>

Output: 3x3 rotation matrix in JSON format.
"""

import sys
import json
import numpy as np


def compute_rotation_matrix(normal1, normal2):
    """
    Compute rotation matrix from normal1 to normal2 using quaternions.

    Parameters
    ----------
    normal1 : array-like (3,)
        Source normal vector.
    normal2 : array-like (3,)
        Target normal vector.

    Returns
    -------
    R : ndarray (3, 3)
        Rotation matrix such that R @ normal1 ≈ normal2.
    """
    v1 = np.asarray(normal1, dtype=float).flatten()
    v2 = np.asarray(normal2, dtype=float).flatten()

    # Normalize to unit vectors
    nv1 = v1 / np.linalg.norm(v1)
    nv2 = v2 / np.linalg.norm(v2)

    # If vectors are equal, return identity
    if np.allclose(nv1, nv2):
        return np.eye(3)

    # If vectors are opposite, quaternion is (0, 0, 0, 0) → return -I
    if np.linalg.norm(nv1 + nv2) < 1e-12:
        q = np.array([0.0, 0.0, 0.0, 0.0])
    else:
        # Rotation axis (cross product)
        u = np.cross(nv1, nv2)
        u = u / np.linalg.norm(u)

        # Rotation angle
        theta = np.arccos(np.clip(np.dot(nv1, nv2), -1.0, 1.0)) / 2.0

        # Quaternion: (cos(theta), sin(theta) * u)
        q = np.zeros(4)
        q[0] = np.cos(theta)
        q[1] = np.sin(theta) * u[0]
        q[2] = np.sin(theta) * u[1]
        q[3] = np.sin(theta) * u[2]

    # Convert quaternion to rotation matrix (standard formula)
    # q = (w, x, y, z) where w is the scalar part
    w, x, y, z = q[0], q[1], q[2], q[3]

    R = np.array([
        [1 - 2*y*y - 2*z*z,     2*x*y - 2*w*z,         2*x*z + 2*w*y],
        [2*x*y + 2*w*z,         1 - 2*x*x - 2*z*z,     2*y*z - 2*w*x],
        [2*x*z - 2*w*y,         2*y*z + 2*w*x,         1 - 2*x*x - 2*y*y]
    ])

    return R


def main():
    if len(sys.argv) < 7:
        print(json.dumps({"error": "Usage: rotation_matrix.py <x1> <y1> <z1> <x2> <y2> <z2>"}))
        sys.exit(1)

    x1, y1, z1 = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3])
    x2, y2, z2 = float(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6])

    normal1 = np.array([x1, y1, z1])
    normal2 = np.array([x2, y2, z2])

    R = compute_rotation_matrix(normal1, normal2)

    # Verify
    nv1 = normal1 / np.linalg.norm(normal1)
    nv2 = normal2 / np.linalg.norm(normal2)
    rotated = R @ nv1
    error = np.linalg.norm(rotated - nv2)

    result = {
        "normal1": normal1.tolist(),
        "normal2": normal2.tolist(),
        "normal1_unit": nv1.tolist(),
        "normal2_unit": nv2.tolist(),
        "rotation_matrix": R.tolist(),
        "verification_error": float(error)
    }

    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
