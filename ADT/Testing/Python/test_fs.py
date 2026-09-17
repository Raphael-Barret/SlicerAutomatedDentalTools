# Ce que `search` rend, et les deux differences qui ont survecu aux quinze copies.
#
# Les deux parametres ne sont pas des options de confort : chacun correspond a
# un site d'origine dont le comportement aurait change sans lui. `sort` pour les
# trois qui triaient -- l'ordre de traitement des patients en depend -- et
# `files_only` pour le seul qui ecartait les repertoires.
import os
import sys
import tempfile
import unittest

# ADTLib, que les paquets importent desormais : une suite de tests est un
# point d entree comme un autre, rien ne l a mis sur sys.path avant elle.
_ADT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "ADT")
if os.path.isdir(_ADT):
    sys.path.insert(0, _ADT)

from ADTLib.io.fs import search  # noqa: E402


class SearchTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def touch(self, *parts):
        path = os.path.join(self.tmp.name, *parts)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, "w").close()
        return path

    def names(self, result, key):
        return sorted(os.path.basename(p) for p in result[key])

    def test_each_extension_gets_its_own_key(self):
        self.touch("a.json")
        self.touch("b.nrrd")
        found = search(self.tmp.name, "json", ".nrrd")
        self.assertEqual(self.names(found, "json"), ["a.json"])
        self.assertEqual(self.names(found, ".nrrd"), ["b.nrrd"])

    def test_a_list_argument_is_flattened(self):
        self.touch("a.json")
        self.touch("b.nii.gz")
        found = search(self.tmp.name, "json", [".nii.gz", ".nrrd"])
        self.assertEqual(sorted(found), [".nii.gz", ".nrrd", "json"])
        self.assertEqual(self.names(found, ".nii.gz"), ["b.nii.gz"])
        self.assertEqual(found[".nrrd"], [])

    def test_the_tree_is_walked_recursively(self):
        self.touch("T1", "P1", "scan.nrrd")
        self.assertEqual(self.names(search(self.tmp.name, ".nrrd"), ".nrrd"),
                         ["scan.nrrd"])

    def test_sort_orders_each_list(self):
        for name in ("c.nrrd", "a.nrrd", "b.nrrd"):
            self.touch(name)
        found = search(self.tmp.name, ".nrrd", sort=True)
        self.assertEqual([os.path.basename(p) for p in found[".nrrd"]],
                         ["a.nrrd", "b.nrrd", "c.nrrd"])

    def test_without_sort_a_directory_ending_in_the_key_is_returned(self):
        """Le comportement des quatorze copies qui ne filtraient pas : un
        dossier nomme patient.nrrd compte comme un scan."""
        os.makedirs(os.path.join(self.tmp.name, "patient.nrrd"))
        self.touch("scan.nrrd")
        self.assertEqual(self.names(search(self.tmp.name, ".nrrd"), ".nrrd"),
                         ["patient.nrrd", "scan.nrrd"])

    def test_files_only_drops_it(self):
        """Ce que faisait la variante d'ASO_IOS_utils/data_file.py."""
        os.makedirs(os.path.join(self.tmp.name, "patient.nrrd"))
        self.touch("scan.nrrd")
        found = search(self.tmp.name, ".nrrd", files_only=True)
        self.assertEqual(self.names(found, ".nrrd"), ["scan.nrrd"])

    def test_an_extension_nothing_matches_gives_an_empty_list_not_a_missing_key(self):
        self.assertEqual(search(self.tmp.name, ".vtk"), {".vtk": []})

    def test_no_argument_gives_an_empty_dictionary(self):
        self.touch("a.json")
        self.assertEqual(search(self.tmp.name), {})


if __name__ == "__main__":
    unittest.main()
