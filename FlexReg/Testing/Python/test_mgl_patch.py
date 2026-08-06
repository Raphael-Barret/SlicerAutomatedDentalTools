# Invariants of the lower-arch MGL patch engine, checked on a synthetic mesh so
# the suite needs no patient scan and no GPU.
#
# Two of these guard bugs that were live during development and were both
# invisible on screen -- the patch still looked plausible, it was simply the
# wrong size:
#   - an edge graph built from the raw triangle list adds every interior edge
#     twice, doubling its length and halving the reach of the patch;
#   - a height raised on one landmark must not be swallowed where its spline
#     samples land on a vertex a shorter neighbour also claims.
#
# Run with:  python -m unittest discover FlexReg/Testing/Python
import os
import sys
import unittest

import numpy as np
import vtk
from vtk.util.numpy_support import numpy_to_vtk

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "FlexReg_utils"))

import mgl_patch  # noqa: E402


GRID_STEP = 1.0  # mm between neighbouring vertices of the test plane


def FlatMesh(half_size=20, step=GRID_STEP):
    """A flat triangulated square in z=0, vertices `step` mm apart.

    Geodesic distance across it is Euclidean, which is what makes the reach of
    the patch something the test can predict in closed form.
    """
    coords = np.arange(-half_size, half_size + step, step)
    nx = len(coords)
    xs, ys = np.meshgrid(coords, coords, indexing="ij")
    vertices = np.column_stack([xs.ravel(), ys.ravel(), np.zeros(xs.size)])

    points = vtk.vtkPoints()
    points.SetData(numpy_to_vtk(vertices, deep=True))
    polydata = vtk.vtkPolyData()
    polydata.SetPoints(points)

    cells = vtk.vtkCellArray()
    for i in range(nx - 1):
        for j in range(nx - 1):
            a, b = i * nx + j, i * nx + j + 1
            c, d = (i + 1) * nx + j, (i + 1) * nx + j + 1
            for triangle in ((a, b, d), (a, d, c)):
                cells.InsertNextCell(3)
                for point_id in triangle:
                    cells.InsertCellPoint(point_id)
    polydata.SetPolys(cells)
    return polydata, vertices


def ArchLandmarks(span=12.0):
    """The 13 MG landmarks on a shallow in-plane arc.

    Deliberately curved: three collinear points leave the plane the landmarks
    lie in undefined, and with it the apical axis derived from it.
    """
    xs = np.linspace(-span, span, len(mgl_patch.MGL_ORDER))
    ys = xs ** 2 / 60.0 - 2.0
    return {name: np.array([x, y, 0.0])
            for name, x, y in zip(mgl_patch.MGL_ORDER, xs, ys)}


def ReachAround(vertices, labels, builder, index):
    """How far the patch extends from one landmark, over the mesh it owns.

    Measured per landmark rather than across the arch, because a neighbour's
    band can reach the same distance and hide a height that was lost here.
    """
    landmarks = builder._landmarks
    selected = vertices[labels > 0.5]
    if not len(selected):
        return 0.0
    to_each = np.linalg.norm(selected[:, None, :] - landmarks[None, :, :], axis=2)
    owned = selected[to_each.argmin(axis=1) == index]
    if not len(owned):
        return 0.0
    return float(np.linalg.norm(owned - landmarks[index], axis=1).max())


def BandHalfWidth(vertices, labels, x_centre, window=0.6):
    """Extent of the patch across the arch, in the slice of mesh at `x_centre`.

    The band straddles the curve, so this is measured from the curve outwards
    on the wider of the two sides.
    """
    column = np.abs(vertices[:, 0] - x_centre) < window
    selected = column & (labels > 0.5)
    if not selected.any():
        return 0.0
    curve_y = x_centre ** 2 / 60.0 - 2.0
    return float(np.abs(vertices[selected][:, 1] - curve_y).max())


class OrderedLandmarksTest(unittest.TestCase):
    def test_orders_along_the_arch_not_by_json_order(self):
        landmarks = ArchLandmarks()
        shuffled = {name: landmarks[name] for name in reversed(mgl_patch.MGL_ORDER)}
        names, _ = mgl_patch.OrderedLandmarks(shuffled)
        self.assertEqual(names, mgl_patch.MGL_ORDER)

    def test_a_scan_missing_some_landmarks_still_yields_a_curve(self):
        landmarks = ArchLandmarks()
        for name in ("LL6MG", "LR4MG", "LR6MG"):
            del landmarks[name]
        names, positions = mgl_patch.OrderedLandmarks(landmarks)
        self.assertEqual(len(names), len(mgl_patch.MGL_ORDER) - 3)
        self.assertEqual(len(positions), len(names))

    def test_too_few_landmarks_is_an_error_naming_what_was_expected(self):
        with self.assertRaises(ValueError) as caught:
            mgl_patch.OrderedLandmarks({"LL6MG": np.zeros(3), "L0MG": np.ones(3)})
        self.assertIn("LL6MG", str(caught.exception))


class EdgeGraphTest(unittest.TestCase):
    """The reach of the patch is only as trustworthy as the edge lengths."""

    def setUp(self):
        self.polydata, self.vertices = FlatMesh(half_size=4)
        self.builder = mgl_patch.MGLPatchBuilder()
        self.assertTrue(self.builder.prepare(self.polydata, ArchLandmarks(span=3.0)))

    def test_neighbouring_vertices_are_one_step_apart_not_two(self):
        graph = self.builder._graph
        nx = int(round(np.sqrt(len(self.vertices))))
        for a, b in ((0, 1), (0, nx), (5, 6)):
            self.assertAlmostEqual(graph[a, b], GRID_STEP, places=6,
                                   msg="interior edges counted twice")

    def test_graph_is_symmetric(self):
        difference = abs(self.builder._graph - self.builder._graph.T).max()
        self.assertAlmostEqual(difference, 0.0, places=9)


class PatchReachTest(unittest.TestCase):
    def setUp(self):
        self.polydata, self.vertices = FlatMesh()
        self.builder = mgl_patch.MGLPatchBuilder()
        self.assertTrue(self.builder.prepare(self.polydata, ArchLandmarks()))
        self.n = len(self.builder.names())
        self.zero = np.zeros(self.n)

    def patch(self, heights, **kwargs):
        labels, _ = self.builder.compute(self.zero, self.zero, heights, **kwargs)
        return labels

    def test_a_uniform_height_gives_a_band_of_that_height(self):
        for height in (3.0, 6.0):
            labels = self.patch(np.full(self.n, height))
            width = BandHalfWidth(self.vertices, labels, x_centre=0.0)
            # halved edges would put this at height/2, well under the lower bound
            self.assertGreater(width, 0.8 * height)
            self.assertLess(width, 1.25 * height)

    def test_raising_the_height_only_ever_grows_the_patch(self):
        small = self.patch(np.full(self.n, 3.0))
        large = self.patch(np.full(self.n, 6.0))
        self.assertTrue(np.all(large[small > 0.5] > 0.5))
        self.assertGreater(large.sum(), small.sum())

    def test_a_height_set_on_one_end_does_not_reshape_the_other(self):
        heights = np.full(self.n, 2.0)
        heights[:3] = 8.0  # the LL6..LL4 stretch, at negative x
        labels = self.patch(heights)
        tall = BandHalfWidth(self.vertices, labels, x_centre=-11.0)
        short = BandHalfWidth(self.vertices, labels, x_centre=11.0)
        self.assertGreater(tall, 5.0)
        self.assertLess(short, 4.0)
        self.assertGreater(tall, short + 2.0)

    def test_a_tall_landmark_is_not_swallowed_by_a_short_neighbour(self):
        # Dozens of spline samples land on the same vertex, and the tall
        # landmark is flanked by short ones, so the samples writing that vertex
        # arrive tall then short. Keeping the last one instead of the tallest
        # quietly delivers a fraction of the height that was asked for.
        tall = 12.0
        heights = np.full(self.n, 0.5)
        heights[self.n // 2] = tall
        labels = self.patch(heights)
        reach = ReachAround(self.vertices, labels, self.builder, self.n // 2)
        self.assertGreater(reach, 0.9 * tall)


class ToothExclusionTest(unittest.TestCase):
    """Crowns move between timepoints, so they must stay out of the patch."""

    def setUp(self):
        self.polydata, self.vertices = FlatMesh()
        labels = np.where(self.vertices[:, 1] > 0.0, 20, 0).astype(np.int16)
        array = numpy_to_vtk(labels, deep=True)
        array.SetName("Universal_ID")
        self.polydata.GetPointData().AddArray(array)
        self.crown = self.vertices[:, 1] > 0.0

        self.builder = mgl_patch.MGLPatchBuilder()
        self.assertTrue(self.builder.prepare(self.polydata, ArchLandmarks()))
        self.heights = np.full(len(self.builder.names()), 6.0)
        self.zero = np.zeros(len(self.builder.names()))

    def test_no_crown_vertex_is_labelled(self):
        labels, _ = self.builder.compute(self.zero, self.zero, self.heights)
        self.assertEqual(labels[self.crown].sum(), 0.0)
        self.assertGreater(labels.sum(), 0.0)

    def test_the_crowns_are_within_reach_when_not_excluded(self):
        labels, _ = self.builder.compute(self.zero, self.zero, self.heights,
                                         exclude_teeth=False)
        self.assertGreater(labels[self.crown].sum(), 0.0)


class OffsetTest(unittest.TestCase):
    def setUp(self):
        self.polydata, _ = FlatMesh()
        self.builder = mgl_patch.MGLPatchBuilder()
        self.assertTrue(self.builder.prepare(self.polydata, ArchLandmarks()))
        self.n = len(self.builder.names())
        self.zero = np.zeros(self.n)

    def test_no_offset_leaves_the_landmarks_where_ali_put_them(self):
        moved = self.builder.movedLandmarks(self.zero, self.zero)
        np.testing.assert_allclose(moved, self.builder._landmarks, atol=1e-9)

    def test_a_shared_offset_moves_every_landmark_the_same_distance(self):
        moved = self.builder.movedLandmarks(np.full(self.n, 2.0), self.zero)
        travelled = np.linalg.norm(moved - self.builder._landmarks, axis=1)
        np.testing.assert_allclose(travelled, 2.0, atol=1e-9)

    def test_moving_one_landmark_leaves_the_others_untouched(self):
        offsets = np.zeros(self.n)
        offsets[4] = 3.0
        moved = self.builder.movedLandmarks(offsets, self.zero)
        travelled = np.linalg.norm(moved - self.builder._landmarks, axis=1)
        self.assertAlmostEqual(travelled[4], 3.0, places=9)
        self.assertAlmostEqual(np.delete(travelled, 4).max(), 0.0, places=9)


class ArrayNamingTest(unittest.TestCase):
    def test_the_array_carries_the_name_areg_reads(self):
        builder = mgl_patch.MGLPatchBuilder()
        array = builder.toArray(np.ones(4, dtype=np.float32))
        self.assertEqual(array.GetName(), "Bottom_MGL")
        self.assertEqual(array.GetNumberOfTuples(), 4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
