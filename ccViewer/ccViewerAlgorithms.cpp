// ============================================================================
// ccViewerAlgorithms.cpp
// Native C++ implementations of 4 point-cloud processing tools
// Translated from MATLAB sources in method/
// ============================================================================

#include "ccViewerAlgorithms.h"

// CCCoreLib
#include <DgmOctree.h>
#include <Neighbourhood.h>
#include <Jacobi.h>
#include <SquareMatrix.h>
#include <ReferenceCloud.h>
#include <GenericProgressCallback.h>
#include <GeometricalAnalysisTools.h>

// qCC_db
#include <ccPointCloud.h>
#include <ccHObjectCaster.h>
#include <ScalarField.h>

#include <cmath>
#include <algorithm>
#include <set>
#include <vector>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

// ============================================================================
// Anonymous namespace — internal helpers
// ============================================================================
namespace {

// ---------- Simple KNN via octree ----------
// Returns indices of the K nearest neighbors of queryPoint in cloud.
// Uses DgmOctree::findPointNeighbourhood which fills a ReferenceCloud.
std::vector<unsigned> knnSearch(CCCoreLib::DgmOctree* octree,
                                ccPointCloud* cloud,
                                unsigned queryIndex,
                                int K)
{
    std::vector<unsigned> result;
    if (!octree || !cloud || K <= 0 || queryIndex >= cloud->size())
        return result;

    const CCVector3* queryPt = cloud->getPoint(queryIndex);

    // Determine octree level for neighborhood extraction
    // Use a rough estimate: find level that gives ~K+1 points per cell
    unsigned char level = 1;
    {
        CCVector3 diag = octree->getOctreeMaxs() - octree->getOctreeMins();
        double vol = diag.x * diag.y * diag.z;
        double ptsPerCell = static_cast<double>(cloud->size());
        for (unsigned char l = 1; l <= 12; ++l)
        {
            double cells = std::pow(8.0, static_cast<double>(l));
            if (ptsPerCell / cells < static_cast<double>(K) * 2.0)
            {
                level = l;
                break;
            }
        }
        if (level < 1) level = 1;
    }

    CCCoreLib::ReferenceCloud refCloud(cloud);
    unsigned maxNN = static_cast<unsigned>(K + 1); // +1 to include query point itself
    double maxSquareDist = 0;

    unsigned found = octree->findPointNeighbourhood(
        queryPt, &refCloud, maxNN, level, maxSquareDist);

    if (found > 0)
    {
        result.reserve(found);
        for (unsigned j = 0; j < found; ++j)
        {
            unsigned idx = refCloud.getPointGlobalIndex(j);
            if (idx != queryIndex) // exclude the query point itself
                result.push_back(idx);
        }
    }

    return result;
}

// ---------- Sphere neighborhood via octree ----------
std::vector<unsigned> sphereNeighbors(CCCoreLib::DgmOctree* octree,
                                      ccPointCloud* cloud,
                                      unsigned queryIndex,
                                      double radius,
                                      unsigned char level)
{
    std::vector<unsigned> result;
    if (!octree || !cloud || radius <= 0.0 || queryIndex >= cloud->size())
        return result;

    const CCVector3* center = cloud->getPoint(queryIndex);
    CCCoreLib::DgmOctree::NeighboursSet neighbours;
    int count = octree->getPointsInSphericalNeighbourhood(
        *center, static_cast<PointCoordinateType>(radius), neighbours, level);

    result.reserve(static_cast<std::size_t>(count));
    for (const auto& pd : neighbours)
        result.push_back(pd.pointIndex);

    return result;
}

// ---------- TLS plane fitting on a subset of points ----------
// Fits plane ax+by+cz=d (CCCoreLib convention) to the given point indices.
// Returns true on success, outputs normal and d.
bool fitPlaneTLS(ccPointCloud* cloud,
                 const std::vector<unsigned>& indices,
                 CCVector3& normal, double& d)
{
    if (indices.size() < 3) return false;

    CCCoreLib::ReferenceCloud refCloud(cloud);
    for (unsigned idx : indices)
        refCloud.addPointIndex(idx);

    CCCoreLib::Neighbourhood nh(&refCloud);
    const PointCoordinateType* planeEq = nh.getLSPlane();
    if (!planeEq) return false;

    normal = CCVector3(planeEq[0], planeEq[1], planeEq[2]);
    d = static_cast<double>(planeEq[3]);
    return true;
}

// ---------- PCA: max-eigenvalue direction of a point subset ----------
// Implements sphere_PCA.m: returns the eigenvector with the LARGEST eigenvalue.
bool computeMaxEigenDirection(ccPointCloud* cloud,
                              const std::vector<unsigned>& indices,
                              CCVector3& maxDir, CCVector3& centroid)
{
    if (indices.size() < 3) return false;

    // Compute centroid
    centroid = CCVector3(0, 0, 0);
    for (unsigned idx : indices)
        centroid += *cloud->getPoint(idx);
    centroid /= static_cast<PointCoordinateType>(indices.size());

    // Build 3x3 covariance-like matrix: sum((P_i - centroid) * (P_i - centroid)^T)
    double cov[3][3] = {{0,0,0},{0,0,0},{0,0,0}};
    for (unsigned idx : indices)
    {
        CCVector3 diff = *cloud->getPoint(idx) - centroid;
        cov[0][0] += static_cast<double>(diff.x) * diff.x;
        cov[0][1] += static_cast<double>(diff.x) * diff.y;
        cov[0][2] += static_cast<double>(diff.x) * diff.z;
        cov[1][1] += static_cast<double>(diff.y) * diff.y;
        cov[1][2] += static_cast<double>(diff.y) * diff.z;
        cov[2][2] += static_cast<double>(diff.z) * diff.z;
    }
    cov[1][0] = cov[0][1];
    cov[2][0] = cov[0][2];
    cov[2][1] = cov[1][2];

    // Build SquareMatrix for Jacobi
    CCCoreLib::SquareMatrixd mat(3);
    for (unsigned r = 0; r < 3; ++r)
        for (unsigned c = 0; c < 3; ++c)
            mat.setValue(r, c, cov[r][c]);

    CCCoreLib::SquareMatrixd eigVectors;
    std::vector<double> eigValues;
    if (!CCCoreLib::Jacobi<double>::ComputeEigenValuesAndVectors(
            mat, eigVectors, eigValues, true))
        return false;

    double maxEigVal;
    double maxEigVec[3];
    if (!CCCoreLib::Jacobi<double>::GetMaxEigenValueAndVector(
            eigVectors, eigValues, maxEigVal, maxEigVec))
        return false;

    maxDir = CCVector3(
        static_cast<PointCoordinateType>(maxEigVec[0]),
        static_cast<PointCoordinateType>(maxEigVec[1]),
        static_cast<PointCoordinateType>(maxEigVec[2]));

    return true;
}

// ---------- 3D point to plane projection ----------
// Projects points onto plane defined by normal (unit) and d: normal·p = d
CCVector3 projectPointToPlane(const CCVector3& p,
                              const CCVector3& normal, double d)
{
    double n2 = static_cast<double>(normal.norm2());
    if (n2 < 1e-30) return p;
    double t = (static_cast<double>(p.dot(normal)) - d) / n2;
    return CCVector3(
        static_cast<PointCoordinateType>(p.x - t * normal.x),
        static_cast<PointCoordinateType>(p.y - t * normal.y),
        static_cast<PointCoordinateType>(p.z - t * normal.z));
}

// ---------- Rotation matrix from normal1 to normal2 (quaternion method) ----------
// Returns a 3x3 matrix R such that R * normal1 ≈ normal2 (row-major in R[9]).
bool rotationFromTwoNormals(const CCVector3& n1, const CCVector3& n2, double R[9])
{
    CCVector3 v1 = n1; v1.normalize();
    CCVector3 v2 = n2; v2.normalize();

    // Identity case
    if ((v1 - v2).norm() < 1e-12)
    {
        R[0]=1; R[1]=0; R[2]=0;
        R[3]=0; R[4]=1; R[5]=0;
        R[6]=0; R[7]=0; R[8]=1;
        return true;
    }

    // Opposite case
    if ((v1 + v2).norm() < 1e-12)
    {
        R[0]=-1; R[1]=0;  R[2]=0;
        R[3]=0;  R[4]=-1; R[5]=0;
        R[6]=0;  R[7]=0;  R[8]=-1;
        return true;
    }

    CCVector3 axis = v1.cross(v2);
    axis.normalize();
    double halfAngle = std::acos(static_cast<double>(v1.dot(v2))) / 2.0;

    double qw = std::cos(halfAngle);
    double qx = std::sin(halfAngle) * axis.x;
    double qy = std::sin(halfAngle) * axis.y;
    double qz = std::sin(halfAngle) * axis.z;

    // Quaternion to 3x3 rotation matrix
    double q00 = qw*qw, q11 = qx*qx, q22 = qy*qy, q33 = qz*qz;
    double q03 = qw*qz, q13 = qx*qz, q23 = qy*qz;
    double q02 = qw*qy, q12 = qx*qy, q01 = qw*qx;

    R[0] = q00 + q11 - q22 - q33;  R[1] = 2.0*(q12 - q03);         R[2] = 2.0*(q13 + q02);
    R[3] = 2.0*(q12 + q03);         R[4] = q00 - q11 + q22 - q33;  R[5] = 2.0*(q23 - q01);
    R[6] = 2.0*(q13 - q02);         R[7] = 2.0*(q23 + q01);         R[8] = q00 - q11 - q22 + q33;

    return true;
}

} // anonymous namespace

// ============================================================================
// Tool 1: Boundary Point Extract
// ============================================================================
ccPointCloud* boundaryExtract(ccPointCloud* cloud, int K, double angleThresholdDeg)
{
    if (!cloud || cloud->size() < static_cast<unsigned>(K + 2))
        return nullptr;

    unsigned n = cloud->size();
    if (K < 3) K = 3;

    // Build octree
    CCCoreLib::DgmOctree octree(cloud);
    octree.build(nullptr);

    // Find octree level for KNN
    CCVector3 diag = octree.getOctreeMaxs() - octree.getOctreeMins();
    double approxSpacing = std::cbrt(
        (static_cast<double>(diag.x) * diag.y * diag.z) / n);
    double searchRadius = approxSpacing * K * 2.0;
    unsigned char level = octree.findBestLevelForAGivenNeighbourhoodSizeExtraction(
        static_cast<PointCoordinateType>(searchRadius));

    std::vector<bool> isBoundary(n, false);
    double angleThresholdRad = angleThresholdDeg * M_PI / 180.0;

    for (unsigned i = 0; i < n; ++i)
    {
        // Get K+1 nearest neighbors (K neighbors + self)
        CCCoreLib::ReferenceCloud refCloud(cloud);
        unsigned maxNN = static_cast<unsigned>(K + 1);
        double maxSquareDist = 0;

        const CCVector3* queryPt = cloud->getPoint(i);
        unsigned found = octree.findPointNeighbourhood(
            queryPt, &refCloud, maxNN, level, maxSquareDist);

        if (found < 4) continue; // need at least 3 neighbors + self

        // Collect neighbor indices (exclude self)
        std::vector<unsigned> neighborIdx;
        neighborIdx.reserve(found);
        for (unsigned j = 0; j < found; ++j)
        {
            unsigned idx = refCloud.getPointGlobalIndex(j);
            if (idx != i)
                neighborIdx.push_back(idx);
        }
        if (neighborIdx.size() < 3) continue;

        // Fit TLS plane
        CCVector3 normal; double d_plane;
        if (!fitPlaneTLS(cloud, neighborIdx, normal, d_plane))
            continue;

        // Compute centroid of neighbors
        CCVector3 meanNeighbor(0, 0, 0);
        for (unsigned idx : neighborIdx)
            meanNeighbor += *cloud->getPoint(idx);
        meanNeighbor /= static_cast<PointCoordinateType>(neighborIdx.size());

        // Project neighbors onto plane
        std::vector<CCVector3> projPts;
        projPts.reserve(neighborIdx.size());
        for (unsigned idx : neighborIdx)
            projPts.push_back(projectPointToPlane(*cloud->getPoint(idx), normal, d_plane));

        // Project query point onto plane
        CCVector3 projQuery = projectPointToPlane(
            *cloud->getPoint(i), normal, d_plane);

        // X-axis: direction from projected query to farthest projected neighbor
        PointCoordinateType maxDist2 = 0;
        CCVector3 xAxis(1, 0, 0);
        for (const auto& pp : projPts)
        {
            PointCoordinateType d2 = (pp - projQuery).norm2();
            if (d2 > maxDist2)
            {
                maxDist2 = d2;
                xAxis = pp - projQuery;
            }
        }
        if (maxDist2 < 1e-20) continue;
        xAxis.normalize();

        // Y-axis: cross(normal, xAxis), normalized
        CCVector3 yAxis = normal.cross(xAxis);
        if (yAxis.norm2() < 1e-20) continue;
        yAxis.normalize();

        // Project neighbor-points into 2D (dot with xAxis, yAxis)
        std::vector<double> azimuths;
        azimuths.reserve(neighborIdx.size());
        for (const auto& pp : projPts)
        {
            CCVector3 rel = pp - projQuery;
            double px = static_cast<double>(rel.dot(xAxis));
            double py = static_cast<double>(rel.dot(yAxis));
            double az = std::atan2(py, px); // radians
            if (az < 0.0) az += 2.0 * M_PI;
            azimuths.push_back(az);
        }

        // Sort azimuths and find max angular gap
        std::sort(azimuths.begin(), azimuths.end());
        double maxGap = 0.0;
        for (std::size_t j = 0; j + 1 < azimuths.size(); ++j)
        {
            double gap = azimuths[j + 1] - azimuths[j];
            if (gap > maxGap) maxGap = gap;
        }
        // Wrap-around gap
        double wrapGap = azimuths.front() + 2.0 * M_PI - azimuths.back();
        if (wrapGap > maxGap) maxGap = wrapGap;

        if (maxGap > angleThresholdRad)
            isBoundary[i] = true;
    }

    // Build output cloud
    ccPointCloud* result = new ccPointCloud(cloud->getName() + QString(".boundary"));
    unsigned boundaryCount = 0;
    for (unsigned i = 0; i < n; ++i)
        if (isBoundary[i]) ++boundaryCount;

    if (boundaryCount == 0 || !result->reserve(boundaryCount))
    {
        delete result;
        return nullptr;
    }

    for (unsigned i = 0; i < n; ++i)
    {
        if (isBoundary[i])
            result->addPoint(*cloud->getPoint(i));
    }

    // Copy colors if available
    if (cloud->hasColors() && result->reserveTheRGBTable())
    {
        for (unsigned i = 0; i < n; ++i)
        {
            if (isBoundary[i])
                result->addColor(cloud->getPointColor(i));
        }
        result->showColors(true);
    }

    return result;
}

// ============================================================================
// Tool 2: Fold Point Extract
// ============================================================================
ccPointCloud* foldExtract(ccPointCloud* cloud, double radius,
                          double PL_threshold, double DP_DS, int rank_dis_threshold)
{
    if (!cloud || cloud->size() < 5)
        return nullptr;

    unsigned n = cloud->size();
    if (rank_dis_threshold < 1) rank_dis_threshold = 3;

    // Build octree
    CCCoreLib::DgmOctree octree(cloud);
    octree.build(nullptr);

    unsigned char level = octree.findBestLevelForAGivenNeighbourhoodSizeExtraction(
        static_cast<PointCoordinateType>(radius));

    // Precompute sphere neighborhoods for all points
    std::vector<std::vector<unsigned>> allNeighbors(n);
    for (unsigned i = 0; i < n; ++i)
    {
        allNeighbors[i] = sphereNeighbors(&octree, cloud, i, radius, level);
    }

    // Detect fold points
    std::set<unsigned> foldSet;

    for (unsigned i = 0; i < n; ++i)
    {
        const auto& neighborIdx = allNeighbors[i];
        if (neighborIdx.size() < 6) continue;

        // Step 1: PCA plane — max eigenvector direction
        CCVector3 maxDir, centroid;
        if (!computeMaxEigenDirection(cloud, neighborIdx, maxDir, centroid))
            continue;
        double d_plane = static_cast<double>(centroid.dot(maxDir));

        // Step 2: Project neighbors onto PCA plane
        std::vector<CCVector3> projPts;
        projPts.reserve(neighborIdx.size());
        for (unsigned idx : neighborIdx)
            projPts.push_back(projectPointToPlane(*cloud->getPoint(idx), maxDir, d_plane));

        // Step 3: Rotate to align maxDir with [0,0,1]
        double R[9];
        rotationFromTwoNormals(maxDir, CCVector3(0, 0, 1), R);

        std::vector<CCVector3> rotatedPts;
        rotatedPts.reserve(projPts.size());
        for (const auto& pp : projPts)
        {
            double px = R[0]*pp.x + R[1]*pp.y + R[2]*pp.z;
            double py = R[3]*pp.x + R[4]*pp.y + R[5]*pp.z;
            rotatedPts.push_back(CCVector3(
                static_cast<PointCoordinateType>(px),
                static_cast<PointCoordinateType>(py), 0));
        }

        // Step 4: Find farthest pair in 2D (X,Y)
        unsigned m = static_cast<unsigned>(rotatedPts.size());
        double maxPairDist = 0;
        unsigned fIdx1 = 0, fIdx2 = 0;
        for (unsigned a = 0; a < m; ++a)
        {
            for (unsigned b = a + 1; b < m; ++b)
            {
                double dx = static_cast<double>(rotatedPts[a].x - rotatedPts[b].x);
                double dy = static_cast<double>(rotatedPts[a].y - rotatedPts[b].y);
                double dist = dx*dx + dy*dy;
                if (dist > maxPairDist)
                {
                    maxPairDist = dist;
                    fIdx1 = a; fIdx2 = b;
                }
            }
        }
        if (maxPairDist < 1e-20) continue;

        // Step 5: Fit 2D line through farthest pair (least squares for 2 points = exact)
        double x1 = rotatedPts[fIdx1].x, y1_ = rotatedPts[fIdx1].y;
        double x2 = rotatedPts[fIdx2].x, y2_ = rotatedPts[fIdx2].y;
        double slope, intercept;
        if (std::abs(x2 - x1) > 1e-20)
        {
            slope = (y2_ - y1_) / (x2 - x1);
            intercept = y1_ - slope * x1;
        }
        else
        {
            slope = 1e10; // nearly vertical
            intercept = x1;
        }

        // Step 6: Point-to-line distances & side test
        std::vector<double> distances;
        distances.reserve(m);
        int rightCount = 0, leftCount = 0;
        double distSum = 0.0;

        for (const auto& rp : rotatedPts)
        {
            double x = rp.x, y = rp.y;
            double dist;
            double side;

            if (slope < 1e9)
            {
                dist = std::abs(slope * x - y + intercept) / std::sqrt(slope*slope + 1.0);
                side = slope * x + intercept - y;
            }
            else
            {
                dist = std::abs(x - intercept);
                side = x - intercept;
            }

            distances.push_back(dist);
            distSum += dist;
            if (side > 0) ++rightCount;
            else if (side < 0) ++leftCount;
            // side == 0: point lies on the line, don't count to either side
        }

        double meanDist = distSum / m;
        double variance = 0.0;
        for (double d : distances)
            variance += (d - meanDist) * (d - meanDist);
        double PL_std = std::sqrt(variance / m);

        // Step 7: Fold condition
        bool sideImbalance = (rightCount > DP_DS * leftCount) ||
                             (leftCount > DP_DS * rightCount);
        if (sideImbalance && PL_std > PL_threshold)
        {
            // Get top rank_dis_threshold farthest points
            std::vector<double> sortedDist = distances;
            std::sort(sortedDist.begin(), sortedDist.end(), std::greater<double>());
            double threshold = (rank_dis_threshold < static_cast<int>(sortedDist.size()))
                ? sortedDist[rank_dis_threshold]
                : sortedDist.back();

            for (unsigned j = 0; j < m; ++j)
            {
                if (distances[j] >= threshold)
                    foldSet.insert(neighborIdx[j]);
            }
        }
    }

    // Build output cloud
    ccPointCloud* result = new ccPointCloud(cloud->getName() + QString(".fold"));
    if (foldSet.empty() || !result->reserve(static_cast<unsigned>(foldSet.size())))
    {
        delete result;
        return nullptr;
    }

    for (unsigned idx : foldSet)
        result->addPoint(*cloud->getPoint(idx));

    // Copy colors
    if (cloud->hasColors() && result->reserveTheRGBTable())
    {
        for (unsigned idx : foldSet)
            result->addColor(cloud->getPointColor(idx));
        result->showColors(true);
    }

    return result;
}

// ============================================================================
// Tool 3: Sphere Neighborhood
// ============================================================================
ccPointCloud* sphereNeighborhoodExtract(ccPointCloud* cloud, double radius,
                                        int queryPointIndex,
                                        unsigned& outCount, double& outAvgDist,
                                        double& outMinDist, double& outMaxDist)
{
    outCount = 0;
    outAvgDist = 0.0;
    outMinDist = 0.0;
    outMaxDist = 0.0;

    if (!cloud || cloud->size() == 0 || radius <= 0.0)
        return nullptr;

    // Build octree
    CCCoreLib::DgmOctree octree(cloud);
    octree.build(nullptr);

    unsigned char level = octree.findBestLevelForAGivenNeighbourhoodSizeExtraction(
        static_cast<PointCoordinateType>(radius));

    if (queryPointIndex >= 0 && static_cast<unsigned>(queryPointIndex) < cloud->size())
    {
        // Single-point query
        auto neighbors = sphereNeighbors(&octree, cloud,
            static_cast<unsigned>(queryPointIndex), radius, level);

        if (neighbors.empty())
            return nullptr;

        outCount = static_cast<unsigned>(neighbors.size());

        ccPointCloud* result = new ccPointCloud(
            cloud->getName() + QString(".neighbors_%1").arg(queryPointIndex));
        if (!result->reserve(outCount))
        {
            delete result;
            return nullptr;
        }

        const CCVector3* center = cloud->getPoint(queryPointIndex);
        double minD2 = 1e300, maxD2 = 0, sumD = 0;
        for (unsigned idx : neighbors)
        {
            result->addPoint(*cloud->getPoint(idx));
            double d2 = static_cast<double>((*cloud->getPoint(idx) - *center).norm2());
            if (d2 < minD2) minD2 = d2;
            if (d2 > maxD2) maxD2 = d2;
            sumD += std::sqrt(d2);
        }
        outAvgDist = sumD / outCount;
        outMinDist = std::sqrt(minD2);
        outMaxDist = std::sqrt(maxD2);

        // Copy colors
        if (cloud->hasColors() && result->reserveTheRGBTable())
        {
            for (unsigned idx : neighbors)
                result->addColor(cloud->getPointColor(idx));
            result->showColors(true);
        }

        return result;
    }
    else
    {
        // All-points statistics
        outCount = 0;
        double sumD = 0, minD = 1e300, maxD = 0;

        for (unsigned i = 0; i < cloud->size(); ++i)
        {
            auto neighbors = sphereNeighbors(&octree, cloud, i, radius, level);
            unsigned nc = static_cast<unsigned>(neighbors.size());
            outCount += nc;
            if (nc < minD) minD = static_cast<double>(nc);
            if (nc > maxD) maxD = static_cast<double>(nc);
            sumD += static_cast<double>(nc);
        }

        outAvgDist = sumD / cloud->size();
        outMinDist = minD;
        outMaxDist = maxD;
        return nullptr; // no cloud — caller shows message box
    }
}

// ============================================================================
// Tool 4: Sphere PCA
// ============================================================================
bool spherePCACompute(ccPointCloud* cloud, double radius)
{
    if (!cloud || cloud->size() < 3 || radius <= 0.0)
        return false;

    unsigned n = cloud->size();

    // Build octree
    CCCoreLib::DgmOctree octree(cloud);
    octree.build(nullptr);

    unsigned char level = octree.findBestLevelForAGivenNeighbourhoodSizeExtraction(
        static_cast<PointCoordinateType>(radius));

    // Create 3 scalar fields for the normal vector components (nx, ny, nz)
    int sfIdxNx = cloud->addScalarField("PCA_normal_x");
    int sfIdxNy = cloud->addScalarField("PCA_normal_y");
    int sfIdxNz = cloud->addScalarField("PCA_normal_z");

    if (sfIdxNx < 0 || sfIdxNy < 0 || sfIdxNz < 0)
        return false;

    CCCoreLib::ScalarField* sfNx = nullptr;
    CCCoreLib::ScalarField* sfNy = nullptr;
    CCCoreLib::ScalarField* sfNz = nullptr;

    // Get pointers to the newly created scalar fields
    unsigned sfCount = cloud->getNumberOfScalarFields();
    if (sfCount >= 3)
    {
        sfNx = static_cast<CCCoreLib::ScalarField*>(cloud->getScalarField(sfCount - 3));
        sfNy = static_cast<CCCoreLib::ScalarField*>(cloud->getScalarField(sfCount - 2));
        sfNz = static_cast<CCCoreLib::ScalarField*>(cloud->getScalarField(sfCount - 1));
    }

    if (!sfNx || !sfNy || !sfNz)
        return false;

    sfNx->resizeSafe(n);
    sfNy->resizeSafe(n);
    sfNz->resizeSafe(n);

    for (unsigned i = 0; i < n; ++i)
    {
        auto neighbors = sphereNeighbors(&octree, cloud, i, radius, level);

        if (neighbors.size() >= 5)
        {
            CCVector3 maxDir, centroid;
            if (computeMaxEigenDirection(cloud, neighbors, maxDir, centroid))
            {
                sfNx->setValue(i, static_cast<ScalarType>(maxDir.x));
                sfNy->setValue(i, static_cast<ScalarType>(maxDir.y));
                sfNz->setValue(i, static_cast<ScalarType>(maxDir.z));
                continue;
            }
        }

        // Default: zero normal
        sfNx->setValue(i, 0.0);
        sfNy->setValue(i, 0.0);
        sfNz->setValue(i, 0.0);
    }

    sfNx->computeMinAndMax();
    sfNy->computeMinAndMax();
    sfNz->computeMinAndMax();

    // Show normal X component as the active scalar field
    cloud->setCurrentDisplayedScalarField(sfCount - 3);
    cloud->showSF(true);

    return true;
}
