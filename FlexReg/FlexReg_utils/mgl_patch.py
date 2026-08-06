# Build the lower registration patch from the mucogingival landmarks predicted
# by ALI_IOS, with a height the user sets tooth by tooth.
#
# The upper arch is registered on a patch drawn over the palate. The mandible
# has no such plateau, but it has the mucogingival line: the 13 MG landmarks run
# along the arch, a B-spline joins them, and the band of surface around that
# curve plays the same role.
#
# Two properties matter for the result to be usable, and a third for it to be
# editable:
#   - every sample of the curve is snapped onto the mesh, because a curve
#     interpolated between landmarks leaves the surface in the concavities
#     between teeth;
#   - the band grows along the surface, never through it, so a buccal patch
#     cannot appear on the lingual side where the ridge is thin;
#   - the height is carried by the landmarks and interpolated in between, so
#     moving one point only reshapes the patch around it.
import logging
import sys

import numpy as np
import vtk
from vtk.util.numpy_support import numpy_to_vtk, vtk_to_numpy

logger = logging.getLogger("FlexReg_mgl_patch")

# Landmark names of the MG model, in arch order. L0MG is the midline (tooth 25),
# so the right side is shifted by one against the tooth numbers.
MGL_ORDER = ['LL6MG', 'LL5MG', 'LL4MG', 'LL3MG', 'LL2MG', 'LL1MG', 'L0MG',
             'LR1MG', 'LR2MG', 'LR3MG', 'LR4MG', 'LR5MG', 'LR6MG']

# Name of the point array the patch is written to, matching what AREG_IOS reads.
MGL_ARRAY_NAME = "Bottom_MGL"
MGL_PREVIEW_ARRAY_NAME = "Bottom_MGLPreview"

DEFAULT_HEIGHT = 5.0        # mm of surface on each side of the line
MIN_HEIGHT = 0.5
MAX_HEIGHT = 20.0
SAMPLES_PER_SEGMENT = 25    # spline samples between two consecutive landmarks

# Universal_ID labels of the lower teeth. The crowns move between the two
# timepoints, so they must never end up inside the patch.
LOWER_TOOTH_LABELS = range(18, 32)


def ReadLandmarks(path):
    """Read a Slicer markups json as {label: position}."""
    import json
    with open(path) as f:
        data = json.load(f)
    return {point["label"]: np.array(point["position"], dtype=float)
            for point in data["markups"][0]["controlPoints"]
            if point.get("position")}


def OrderedLandmarks(landmarks):
    """MG landmark names and positions in arch order.

    Returns (names, positions). Missing teeth are skipped rather than fatal: a
    scan where ALI could not place every point still yields a usable curve.
    """
    names = [name for name in MGL_ORDER if name in landmarks]
    if len(names) < 3:
        raise ValueError(
            f"Fewer than 3 MG landmarks found, expected names such as "
            f"{MGL_ORDER[:3]}, got {sorted(landmarks)}"
        )
    return names, np.array([landmarks[name] for name in names], dtype=float)


def LocalFrames(points):
    """Buccal and apical unit vectors at each landmark.

    The apical axis is the normal of the plane the landmarks lie in, so it does
    not depend on how the scan happens to be oriented in world space. The buccal
    axis is perpendicular to both that normal and the local arch tangent, and is
    flipped where needed so it always points away from the arch.

    Returns (buccal, apical) with buccal of shape (N, 3) and apical of shape (3,).
    """
    centre = points.mean(axis=0)
    centred = points - centre
    # smallest singular direction of a ribbon of points is its plane normal
    apical = np.linalg.svd(centred)[2][2]
    apical = apical / np.linalg.norm(apical)

    tangents = np.gradient(points, axis=0)
    buccal = np.cross(tangents, apical)
    norms = np.linalg.norm(buccal, axis=1, keepdims=True)
    buccal = buccal / np.where(norms < 1e-9, 1.0, norms)

    outward = centred - np.outer(centred @ apical, apical)
    flip = np.sum(buccal * outward, axis=1) < 0
    buccal[flip] *= -1.0
    return buccal, apical


def OrientApical(apical, points, tooth_points):
    """Return the apical axis signed away from the crowns.

    The plane normal has an arbitrary sign; the teeth tell which way is up, so
    apical is the direction leading away from them.
    """
    if tooth_points is None or len(tooth_points) == 0:
        return apical
    if np.dot(tooth_points.mean(axis=0) - points.mean(axis=0), apical) > 0:
        return -apical
    return apical


def SplineThroughPoints(points, samples_per_segment=SAMPLES_PER_SEGMENT):
    """Sample a spline passing through `points`.

    Returns (samples, weights) where weights[i] holds, for each sample, how much
    it belongs to each landmark: the sample sits between two landmarks and the
    pair of weights says where. That is what lets a height set on one landmark
    fade into its neighbours instead of stepping.
    """
    vtk_points = vtk.vtkPoints()
    for point in points:
        vtk_points.InsertNextPoint(*point)

    spline = vtk.vtkParametricSpline()
    spline.SetPoints(vtk_points)
    spline.ClosedOff()

    n_samples = max(2, (len(points) - 1) * samples_per_segment + 1)
    source = vtk.vtkParametricFunctionSource()
    source.SetParametricFunction(spline)
    source.SetUResolution(n_samples - 1)
    source.Update()

    samples = vtk_to_numpy(source.GetOutput().GetPoints().GetData())

    # Arc position of every sample, expressed in landmark index units. The
    # spline is sampled evenly in its parameter, which passes through the
    # landmarks at regular intervals.
    positions = np.linspace(0.0, len(points) - 1.0, len(samples))
    return samples, positions


def InterpolateHeights(heights, positions):
    """Height at each spline sample, linearly interpolated between landmarks."""
    return np.interp(positions, np.arange(len(heights)), heights)


class MGLPatchBuilder:
    """Turns landmark offsets and heights into a patch, fast enough to drag.

    The per-scan work -- reading the mesh, building the edge graph, locating the
    teeth -- is done once by prepare(). Each compute() then only moves the
    landmarks, redraws the spline and walks the graph, which is what makes a
    live preview possible.
    """

    def __init__(self):
        self.clear()

    def clear(self):
        self.ready = False
        self.error = None
        self._points = None
        self._graph = None
        self._tooth_mask = None
        self._landmarks = None
        self._names = []

    def prepare(self, polydata, landmarks):
        """Cache what does not change while the user drags. True on success."""
        try:
            self._names, self._landmarks = OrderedLandmarks(landmarks)
        except ValueError as error:
            self.error = str(error)
            self.ready = False
            return False

        self._points = vtk_to_numpy(polydata.GetPoints().GetData())
        self._graph = self._buildGraph(polydata)
        self._tooth_mask = self._buildToothMask(polydata)
        self._locator = vtk.vtkPointLocator()
        self._locator.SetDataSet(polydata)
        self._locator.BuildLocator()

        tooth_points = self._points[self._tooth_mask] if self._tooth_mask.any() else None
        buccal, apical = LocalFrames(self._landmarks)
        self._buccal = buccal
        self._apical = OrientApical(apical, self._landmarks, tooth_points)

        self.ready = True
        self.error = None
        return True

    def _buildGraph(self, polydata):
        """Edge graph of the mesh, one entry per edge.

        Every interior edge belongs to two triangles, and a sparse matrix built
        from the raw list would add those duplicates together, silently doubling
        the length of most edges and halving the reach of the patch.
        """
        from scipy.sparse import coo_matrix

        faces = vtk_to_numpy(polydata.GetPolys().GetData()).reshape(-1, 4)[:, 1:]
        edges = np.vstack([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]])
        edges = np.unique(np.sort(edges, axis=1), axis=0)

        lengths = np.linalg.norm(self._points[edges[:, 0]] - self._points[edges[:, 1]], axis=1)
        n_points = len(self._points)
        return coo_matrix(
            (np.r_[lengths, lengths],
             (np.r_[edges[:, 0], edges[:, 1]], np.r_[edges[:, 1], edges[:, 0]])),
            shape=(n_points, n_points),
        ).tocsr()

    def _buildToothMask(self, polydata):
        """True where a vertex belongs to a crown, False on the gingiva."""
        point_data = polydata.GetPointData()
        for name in ("Universal_ID", "PredictedID", "UniversalID"):
            scalars = point_data.GetScalars(name) or point_data.GetArray(name)
            if scalars is not None:
                return np.isin(vtk_to_numpy(scalars), list(LOWER_TOOTH_LABELS))

        logger.warning("No teeth segmentation on the mesh, the patch is not kept off the crowns")
        return np.zeros(len(self._points), dtype=bool)

    def names(self):
        return list(self._names)

    def movedLandmarks(self, buccal_offsets, apical_offsets):
        """Landmark positions after the offsets the user dialled in."""
        moved = self._landmarks.copy()
        moved = moved + self._buccal * np.asarray(buccal_offsets, dtype=float)[:, None]
        moved = moved + np.outer(np.asarray(apical_offsets, dtype=float), self._apical)
        return moved

    def compute(self, buccal_offsets, apical_offsets, heights, exclude_teeth=True):
        """Patch labels for the current settings, as a 0/1 array over the mesh.

        Each vertex is reached from the nearest spline sample; the height that
        sample carries is the one it is judged against, so a tall stretch and a
        short stretch can sit side by side on the same curve.
        """
        from scipy.sparse.csgraph import dijkstra

        moved = self.movedLandmarks(buccal_offsets, apical_offsets)
        samples, positions = SplineThroughPoints(moved)
        sample_heights = InterpolateHeights(np.asarray(heights, dtype=float), positions)

        seeds, seed_heights = [], []
        seen = {}
        for sample, height in zip(samples, sample_heights):
            point_id = self._locator.FindClosestPoint(sample)
            if point_id in seen:
                # one vertex can serve several samples: keep the tallest, so a
                # height raised anywhere is never swallowed by a neighbour
                seed_heights[seen[point_id]] = max(seed_heights[seen[point_id]], height)
                continue
            seen[point_id] = len(seeds)
            seeds.append(point_id)
            seed_heights.append(height)

        seeds = np.asarray(seeds)
        seed_heights = np.asarray(seed_heights)

        distances, _, sources = dijkstra(
            self._graph, directed=False, indices=seeds,
            limit=float(seed_heights.max()), min_only=True, return_predecessors=True,
        )

        reached = np.isfinite(distances)
        inside = np.zeros(len(self._points), dtype=bool)
        if reached.any():
            # sources holds the seed vertex each node was reached from
            seed_index = {seed: i for i, seed in enumerate(seeds)}
            source_ids = sources[reached]
            heights_here = np.array([seed_heights[seed_index[s]] for s in source_ids])
            inside[np.flatnonzero(reached)] = distances[reached] <= heights_here

        if exclude_teeth:
            inside &= ~self._tooth_mask

        return inside.astype(np.float32), samples

    def toArray(self, labels, name=MGL_ARRAY_NAME):
        """Wrap patch labels as a named vtk array."""
        array = numpy_to_vtk(labels.astype(np.float32), deep=True)
        array.SetName(name)
        return array
