# Un repere qu'ALI CBCT n'a pas trouve doit se voir.
#
# Quand `Agent.Search` rend -1, aucun `AddPredictedLandmark` n'est fait : le
# repere est simplement ABSENT du `.mrk.json` de sortie. Rien ne distingue
# alors un repere qu'on n'a pas demande d'un repere que la recherche n'a pas
# su placer, et le seul signe etait une ligne d'avertissement perdue au
# milieu du journal du CLI.
#
# Desormais la liste part dans un fichier pose a cote des predictions, avec
# la raison pour chacun, et un bloc encadre part sur la sortie du CLI.
import json
import os
import shutil
import sys
import tempfile
import types
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.normpath(os.path.join(_HERE, "..", "..", ".."))
for _path in (os.path.join(_ROOT, "ADT"), os.path.join(_ROOT, "ALI_CBCT")):
    if os.path.isdir(_path) and _path not in sys.path:
        sys.path.insert(0, _path)

# Voir test_ali_cbct_bounds : dicom2nifti ne s'importe pas hors de Slicer.
sys.modules.setdefault("dicom2nifti", types.ModuleType("dicom2nifti"))

# `ALI_CBCT/ALI_CBCT.py`, le point d'entree, et non le dossier du meme nom :
# c'est le dossier qui est sur sys.path, pas la racine du depot.
from ALI_CBCT import _report_missing_landmarks  # noqa: E402


class MissingLandmarkReportTest(unittest.TestCase):

    def setUp(self):
        self.out = tempfile.mkdtemp(prefix="ali_cbct_missing_")

    def tearDown(self):
        shutil.rmtree(self.out, ignore_errors=True)

    def test_nothing_is_written_when_nothing_is_missing(self):
        self.assertIsNone(_report_missing_landmarks("C_0001_T1.nii.gz", {},
                                                    self.out))
        self.assertEqual(os.listdir(self.out), [])

    def test_the_report_sits_next_to_the_predictions(self):
        """Meme dossier, meme prefixe de patient que les .mrk.json."""
        path = _report_missing_landmarks(
            "C_0001_T1.nii.gz", {"Me": "never settled"}, self.out)
        self.assertEqual(os.path.basename(path), "C_0001_T1_lm_NotFound.json")
        self.assertEqual(os.path.dirname(path), self.out)

    def test_it_names_every_landmark_and_why(self):
        missing = {"Me": "never settled within its budget of 1000 steps",
                   "Gn": "no model for it in the model folder"}
        path = _report_missing_landmarks("C_0001_T1.nii.gz", missing, self.out)
        with open(path, encoding="utf-8") as handle:
            report = json.load(handle)

        self.assertEqual(report["patient"], "C_0001_T1.nii.gz")
        self.assertEqual({entry["landmark"] for entry in report["not_found"]},
                         {"Me", "Gn"})
        for entry in report["not_found"]:
            self.assertEqual(entry["reason"], missing[entry["landmark"]])

    def test_the_cli_output_names_them_too(self):
        """Le journal du CLI est ce que Slicer montre pendant la course."""
        with self.assertLogs("ADT.ALI_CBCT", level="WARNING") as logged:
            _report_missing_landmarks("C_0001_T1.nii.gz",
                                      {"Me": "never settled"}, self.out)
        text = "\n".join(logged.output)
        self.assertIn("NOT PLACED", text)
        self.assertIn("Me", text)
        self.assertIn("never settled", text)

    def test_an_unwritable_folder_does_not_sink_the_run(self):
        """Les predictions deja ecrites valent mieux qu'une pile d'appels."""
        blocked = os.path.join(self.out, "un-fichier")
        with open(blocked, "w", encoding="utf-8") as handle:
            handle.write("pas un dossier")
        with self.assertLogs("ADT.ALI_CBCT", level="WARNING") as logged:
            path = _report_missing_landmarks(
                "C_0001_T1.nii.gz", {"Me": "never settled"},
                os.path.join(blocked, "sortie"))
        self.assertIsNone(path)
        self.assertIn("Me", "\n".join(logged.output))


if __name__ == "__main__":
    unittest.main()
