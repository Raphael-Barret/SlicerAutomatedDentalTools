# Ce que `ReadSurf` et `WriteSurf` font, maintenant qu'il n'y en a plus qu'un.
#
# Les cinq copies de ReadSurf et les quatre de WriteSurf divergeaient. Les cas
# ci-dessous figent le comportement retenu, et en particulier les quatre points
# ou l'ancien comportement d'au moins une copie n'est pas conserve : un fichier
# absent, une extension inconnue, un maillage vide, et un `.vtp` qui recevait
# des octets VTK herites.
import os
import sys
import tempfile
import unittest

# ADTLib, que les paquets importent desormais : une suite de tests est un
# point d entree comme un autre, rien ne l a mis sur sys.path avant elle.
_ADT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "ADT")
if os.path.isdir(_ADT):
    sys.path.insert(0, _ADT)

import vtk  # noqa: E402

from ADTLib.io.surface import OFFReader, ReadSurf, WriteSurf  # noqa: E402


def a_triangle():
    """Le plus petit maillage non vide : trois points, une face."""
    points = vtk.vtkPoints()
    points.InsertNextPoint(0.0, 0.0, 0.0)
    points.InsertNextPoint(1.0, 0.0, 0.0)
    points.InsertNextPoint(0.0, 1.0, 0.0)
    triangle = vtk.vtkTriangle()
    for i in range(3):
        triangle.GetPointIds().SetId(i, i)
    cells = vtk.vtkCellArray()
    cells.InsertNextCell(triangle)
    surf = vtk.vtkPolyData()
    surf.SetPoints(points)
    surf.SetPolys(cells)
    return surf


OFF_TRIANGLE = """OFF
3 1 0
0.0 0.0 0.0
1.0 0.0 0.0
0.0 1.0 0.0
3 0 1 2
"""


class OFFReaderTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def write(self, text, name="mesh.off"):
        path = os.path.join(self.tmp.name, name)
        with open(path, "w") as f:
            f.write(text)
        return path

    def test_a_triangle_is_read_back(self):
        reader = OFFReader()
        reader.SetFileName(self.write(OFF_TRIANGLE))
        reader.Update()
        surf = reader.GetOutput()
        self.assertEqual(surf.GetNumberOfPoints(), 3)
        self.assertEqual(surf.GetNumberOfCells(), 1)
        self.assertEqual(surf.GetPoint(1), (1.0, 0.0, 0.0))

    def test_vertices_and_lines_are_read_too(self):
        reader = OFFReader()
        reader.SetFileName(self.write("OFF\n2 2 0\n0 0 0\n1 0 0\n1 0\n2 0 1\n"))
        reader.Update()
        self.assertEqual(reader.GetOutput().GetNumberOfPoints(), 2)

    def test_output_is_none_before_update(self):
        """Les deux copies affectaient des locales dans __init__, d'ou un
        AttributeError la ou None etait manifestement voulu."""
        self.assertIsNone(OFFReader().GetOutput())

    def test_a_bad_header_raises_a_real_exception(self):
        """`raise ("...")` leve une chaine, donc un TypeError qui masque le
        message. C'est un ValueError qui porte le nom du fichier."""
        reader = OFFReader()
        reader.SetFileName(self.write("NOTOFF\n0 0 0\n"))
        with self.assertRaises(ValueError) as caught:
            reader.Update()
        self.assertIn("Not a valid OFF header", str(caught.exception))


class ReadSurfTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.surf = a_triangle()

    def path(self, name):
        return os.path.join(self.tmp.name, name)

    def write_with(self, writer, name):
        path = self.path(name)
        writer.SetFileName(path)
        writer.SetInputData(self.surf)
        writer.Update()
        return path

    def test_reads_vtk(self):
        path = self.write_with(vtk.vtkPolyDataWriter(), "a.vtk")
        self.assertEqual(ReadSurf(path).GetNumberOfPoints(), 3)

    def test_reads_vtp(self):
        path = self.write_with(vtk.vtkXMLPolyDataWriter(), "a.vtp")
        self.assertEqual(ReadSurf(path).GetNumberOfPoints(), 3)

    def test_reads_stl(self):
        path = self.write_with(vtk.vtkSTLWriter(), "a.stl")
        self.assertEqual(ReadSurf(path).GetNumberOfPoints(), 3)

    def test_reads_off_everywhere(self):
        """Deux des cinq copies -- FlexReg_CLI et AREG_IOS -- ne lisaient pas
        l'OFF du tout, alors que leurs jumelles le lisaient."""
        path = self.path("a.off")
        with open(path, "w") as f:
            f.write(OFF_TRIANGLE)
        self.assertEqual(ReadSurf(path).GetNumberOfPoints(), 3)

    def test_the_extension_is_matched_whatever_its_case(self):
        path = self.write_with(vtk.vtkPolyDataWriter(), "a.VTK")
        self.assertEqual(ReadSurf(path).GetNumberOfPoints(), 3)

    def test_a_missing_file_raises_instead_of_reading_an_empty_mesh(self):
        """Les lecteurs vtk rendent un maillage vide sans rien dire : l'erreur
        ne se voyait qu'au recalage, plusieurs etapes plus loin."""
        with self.assertRaises(FileNotFoundError):
            ReadSurf(self.path("absent.vtk"))

    def test_an_unknown_extension_raises_instead_of_unboundlocal(self):
        path = self.path("a.xyz")
        open(path, "w").close()
        with self.assertRaises(ValueError):
            ReadSurf(path)

    def test_an_empty_mesh_raises(self):
        path = self.path("empty.vtk")
        writer = vtk.vtkPolyDataWriter()
        writer.SetFileName(path)
        writer.SetInputData(vtk.vtkPolyData())
        writer.Update()
        with self.assertRaises(ValueError):
            ReadSurf(path)


class WriteSurfTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.surf = a_triangle()

    def test_the_infix_lands_before_the_extension(self):
        out = WriteSurf(self.surf, self.tmp.name, "A2_Seg.vtk", "Or")
        self.assertEqual(os.path.basename(out), "A2_SegOr.vtk")
        self.assertTrue(os.path.exists(out))

    def test_the_infix_is_optional(self):
        """ASO appelait sans, avec trois arguments."""
        out = WriteSurf(self.surf, self.tmp.name, "A2.vtk")
        self.assertEqual(os.path.basename(out), "A2.vtk")

    def test_only_the_file_name_of_a_full_path_is_used(self):
        out = WriteSurf(self.surf, self.tmp.name, "/data/patients/P1/A2.vtk")
        self.assertEqual(out, os.path.join(self.tmp.name, "A2.vtk"))

    def test_a_vtp_gets_xml_bytes_not_legacy_ones(self):
        """Trois copies sur quatre ecrivaient du VTK herite sous un nom .vtp."""
        out = WriteSurf(self.surf, self.tmp.name, "A2.vtp")
        with open(out, "rb") as f:
            head = f.read(64)
        self.assertIn(b"<?xml", head)
        self.assertEqual(ReadSurf(out).GetNumberOfPoints(), 3)

    def test_an_unknown_extension_falls_back_to_vtk_name_included(self):
        out = WriteSurf(self.surf, self.tmp.name, "A2.stl")
        self.assertEqual(os.path.basename(out), "A2.vtk")

    def test_a_missing_parent_directory_is_created(self):
        """os.mkdir echouait des que le parent manquait."""
        nested = os.path.join(self.tmp.name, "out", "T1")
        out = WriteSurf(self.surf, nested, "A2.vtk")
        self.assertTrue(os.path.exists(out))

    def test_writing_twice_into_the_same_folder_is_fine(self):
        """os.mkdir etait garde par un os.path.exists : deux processus qui
        ecrivent dans le meme dossier pouvaient tomber sur FileExistsError."""
        WriteSurf(self.surf, self.tmp.name, "A2.vtk")
        WriteSurf(self.surf, self.tmp.name, "A3.vtk")

    def test_what_was_written_reads_back(self):
        out = WriteSurf(self.surf, self.tmp.name, "A2.vtk")
        self.assertEqual(ReadSurf(out).GetNumberOfPoints(), 3)


if __name__ == "__main__":
    unittest.main()
