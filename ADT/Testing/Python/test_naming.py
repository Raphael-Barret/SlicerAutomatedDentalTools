# The identifier read off a file name, checked against the six chains it
# replaces. Standard library only: no scan, no Slicer, no GPU.
#
# The cases below are not invented. OLD_CHAIN is the chain those six sites
# carried, transcribed marker for marker, and the first test runs both over a
# corpus of names in the shapes the pipelines actually produce. If the two ever
# disagree, the refactor changed what a patient is called -- which silently
# stops a T1 scan from pairing with its T2.
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

# ADTLib, que les paquets importent desormais : une suite de tests est un
# point d entree comme un autre, rien ne l a mis sur sys.path avant elle.
_ADT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "ADT")
if os.path.isdir(_ADT):
    sys.path.insert(0, _ADT)

from ADTLib.naming import patient_id, PATIENT_ID_MARKERS  # noqa: E402


def OLD_CHAIN(basename):
    """The chain as it stood in the six sites, written out."""
    return (
        basename.split("_Scan")[0]
        .split("_scan")[0]
        .split("_Or")[0]
        .split("_OR")[0]
        .split("_MAND")[0]
        .split("_MD")[0]
        .split("_MAX")[0]
        .split("_MX")[0]
        .split("_CB")[0]
        .split("_lm")[0]
        .split("_T2")[0]
        .split("_T1")[0]
        .split("_Cl")[0]
        .split(".")[0]
    )


CORPUS = [
    "P001_T1.nii.gz", "P001_T2.nii.gz", "P001_Scan_T1.nii.gz",
    "P001_scan.nrrd", "P001_Or.nii.gz", "P001_OR.nii.gz",
    "P001_MAND_T1.nii.gz", "P001_MD.nii.gz", "P001_MAX_T2.nii.gz",
    "P001_MX.nii.gz", "P001_CB_T1.nii.gz", "P001_lm.json",
    "P001_Cl.nii.gz", "P001_Scanreg.nii.gz", "P001_T1_MAND_Or.nii.gz",
    "MG_scan_T1.nii.gz", "Dupont_03_T2_Scan.nii.gz", "P001.vtk",
    "P001_T3.nii.gz", "P001_T4.nii.gz", "sub-01_ses-T1_CBCT.nii.gz",
    "P001_seg_T1.nii.gz", "A_B_C_T1_Scan.nii.gz", "P001_T1_lm_MAX.json",
    "plain", "", "_T1.nii.gz", "P001..nii.gz",
]


class PatientIdTest(unittest.TestCase):

    def test_matches_the_chain_it_replaces_on_every_name(self):
        for name in CORPUS:
            with self.subTest(name=name):
                self.assertEqual(patient_id(name), OLD_CHAIN(name))

    def test_a_longer_marker_is_cut_before_the_shorter_one_inside_it(self):
        """_Scanreg must not lose its tail to _Scan, nor _MAND to _MD."""
        self.assertEqual(patient_id("P001_Scanreg.nii.gz"), "P001")
        self.assertEqual(patient_id("P001_MAND.nii.gz"), "P001")
        order = list(PATIENT_ID_MARKERS)
        for longer, shorter in (("_MAND", "_MD"), ("_MAX", "_MX")):
            self.assertLess(order.index(longer), order.index(shorter))

    def test_the_two_timepoints_of_a_patient_give_the_same_id(self):
        self.assertEqual(patient_id("P001_T1.nii.gz"), patient_id("P001_T2.nii.gz"))

    def test_a_third_timepoint_does_not_pair_yet(self):
        """Documents the known limit rather than pretending it is fixed."""
        self.assertNotEqual(patient_id("P001_T3.nii.gz"), patient_id("P001_T4.nii.gz"))
        self.assertEqual(patient_id("P001_T3.nii.gz"), "P001_T3")


if __name__ == "__main__":
    unittest.main()
