#pragma once

// ============================================================================
// ccViewerAlgorithms — 4 native C++ point-cloud processing tools
//
// These functions are called from ccviewer.cpp action handlers.
// Each function operates on a ccPointCloud and returns results via
// output parameters or a newly-allocated ccPointCloud (caller owns it).
// ============================================================================

#include <CCGeom.h>

class ccPointCloud;

// ---------------------------------------------------------------------------
// Tool 1: Boundary Point Extract  (boundary_extract2.m)
// ---------------------------------------------------------------------------
// Detects boundary points by analyzing the angular distribution of neighbors
// projected onto the local TLS plane. A point is a boundary candidate when
// the maximum angular gap between consecutive neighbors exceeds the threshold.
//
// @param  cloud              Input point cloud (NOT modified)
// @param  K                  Number of nearest neighbors (default ~30)
// @param  angleThresholdDeg  Angular gap threshold in degrees (default 120)
// @return                    Newly-allocated cloud containing boundary points,
//                            or nullptr on error. Caller takes ownership.
//
ccPointCloud* boundaryExtract(ccPointCloud* cloud, int K, double angleThresholdDeg);

// ---------------------------------------------------------------------------
// Tool 2: Fold Point Extract  (fold_extract_four2.m)
// ---------------------------------------------------------------------------
// Detects fold/crease points in the cloud using local PCA, projection,
// 2D line fitting, and side-imbalance analysis.
//
// @param  cloud              Input point cloud (NOT modified)
// @param  radius             Sphere neighborhood radius
// @param  PL_threshold       Std-dev threshold for point-to-line distances
// @param  DP_DS              Side-imbalance ratio threshold (default 4)
// @param  rank_dis_threshold Rank threshold for farthest-from-line points (default 3)
// @return                    Newly-allocated cloud containing fold points,
//                            or nullptr on error. Caller takes ownership.
//
ccPointCloud* foldExtract(ccPointCloud* cloud, double radius,
                          double PL_threshold, double DP_DS, int rank_dis_threshold);

// ---------------------------------------------------------------------------
// Tool 3: Sphere Neighborhood  (sphere_points.m)
// ---------------------------------------------------------------------------
// Extracts the spherical neighborhood of a specific query point, or returns
// a cloud containing all neighbors if queryPointIndex >= 0.
// If queryPointIndex < 0, the function only reports statistics (returns nullptr,
// caller should display a message box).
//
// @param  cloud            Input point cloud (NOT modified)
// @param  radius           Search radius
// @param  queryPointIndex  Index of the query point, or -1 for "all points" stats
// @return                  New cloud with neighbor points, or nullptr
//
ccPointCloud* sphereNeighborhoodExtract(ccPointCloud* cloud, double radius,
                                        int queryPointIndex,
                                        unsigned& outCount, double& outAvgDist,
                                        double& outMinDist, double& outMaxDist);

// ---------------------------------------------------------------------------
// Tool 4: Sphere PCA  (sphere_PCA.m)
// ---------------------------------------------------------------------------
// Computes per-point PCA normals (max-eigenvalue direction) from spherical
// neighborhoods. Results are stored as a new scalar field on the cloud.
//
// @param  cloud   Input point cloud (modified in-place: normals added)
// @param  radius  Sphere neighborhood radius
// @return         true on success, false on error
//
bool spherePCACompute(ccPointCloud* cloud, double radius);
