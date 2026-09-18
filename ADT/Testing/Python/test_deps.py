# What `check_lib_installed` answers, and on which spelling of a constraint.
#
# The nine copies this replaces disagreed: two ignored the constraint entirely,
# one compared bare strings, one parsed a single operator by hand, one used
# packaging. The cases below pin the behaviour that was chosen -- constraints
# are applied -- and the two legacy spellings that still have to be understood,
# so that no call site has to be rewritten in the same change.
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

# ADTLib, que les paquets importent desormais : une suite de tests est un
# point d entree comme un autre, rien ne l a mis sur sys.path avant elle.
_ADT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "ADT")
if os.path.isdir(_ADT):
    sys.path.insert(0, _ADT)

from packaging.requirements import Requirement  # noqa: E402

from ADTLib.env.deps import check_lib_installed, normalise_spec, requirement  # noqa: E402


class NormaliseSpecTest(unittest.TestCase):

    def test_an_operator_is_kept_as_is(self):
        self.assertEqual(normalise_spec("pydicom", "==3.0.2"), ("pydicom", "==3.0.2"))
        self.assertEqual(normalise_spec("itk", ">=5.4.0"), ("itk", ">=5.4.0"))

    def test_a_bare_version_means_equality(self):
        """ALI wrote ('dicom2nifti', '2.6.2') and meant an exact version."""
        self.assertEqual(normalise_spec("dicom2nifti", "2.6.2"), ("dicom2nifti", "==2.6.2"))

    def test_a_constraint_carried_in_the_name_is_split_off(self):
        """MedX wrote the whole thing as the name: 'numpy<2.0.0'."""
        self.assertEqual(normalise_spec("numpy<2.0.0", None), ("numpy", "<2.0.0"))

    def test_no_constraint_stays_no_constraint(self):
        self.assertEqual(normalise_spec("einops", None), ("einops", None))

    def test_a_compound_constraint_survives(self):
        self.assertEqual(normalise_spec("torch", ">=2.8,<2.13"), ("torch", ">=2.8,<2.13"))


class CheckLibInstalledTest(unittest.TestCase):
    """Checked against a library that is certainly present: packaging itself."""

    def test_an_installed_library_with_no_constraint(self):
        self.assertTrue(check_lib_installed("packaging"))

    def test_a_library_that_is_not_installed(self):
        self.assertFalse(check_lib_installed("a-package-that-does-not-exist-anywhere"))

    def test_a_constraint_that_holds(self):
        self.assertTrue(check_lib_installed("packaging", ">=1.0"))

    def test_a_constraint_that_does_not_hold_is_refused(self):
        """This is the whole point: two of the nine copies answered True here."""
        self.assertFalse(check_lib_installed("packaging", ">=99999"))

    def test_an_exact_version_that_does_not_hold_is_refused(self):
        self.assertFalse(check_lib_installed("packaging", "==0.0.1"))

    def test_a_bare_version_that_does_not_hold_is_refused(self):
        self.assertFalse(check_lib_installed("packaging", "0.0.1"))

    def test_a_missing_library_is_not_an_exception(self):
        """install_function branches on the return value, never on a raise."""
        try:
            result = check_lib_installed("nnunet_version", "==2.8.0")
        except Exception as error:
            self.fail("raised instead of answering: %r" % (error,))
        self.assertFalse(result)


class RequirementTest(unittest.TestCase):
    """What gets handed to pip, for every spelling the call sites use.

    ALI and ASO glued `==` in unconditionally. That produced
    `dicom2nifti==>=2.6.2` as soon as one list entry carried an operator, and
    pip refuses it: `Invalid requirement`. The failure only shows on a machine
    that lacks the library -- a fresh install -- so it is exactly the case the
    developer machine never exercises.
    """

    # Ce que les trois modules passent reellement, releve dans le code :
    #   ALI/ALI.py list_libs_cbct / list_libs_ios
    #   ASO/ASO.py libs
    #   FlexReg/FlexReg.py list_libs
    CALL_SITES = [
        ("itk", None, "itk"),
        ("dicom2nifti", ">=2.6.2", "dicom2nifti>=2.6.2"),
        ("pydicom", "3.0.2", "pydicom==3.0.2"),
        ("torch", "2.2.0", "torch==2.2.0"),
        ("pytorch_lightning", None, "pytorch_lightning"),
        ("monai", "1.3.2", "monai==1.3.2"),
        ("monai", "==1.3.2", "monai==1.3.2"),
        ("numpy", "<2.0.0", "numpy<2.0.0"),
        ("numpy<2.0.0", None, "numpy<2.0.0"),
    ]

    def test_every_call_site_spelling(self):
        for lib, version, expected in self.CALL_SITES:
            self.assertEqual(requirement(lib, version), expected,
                             "%r + %r" % (lib, version))

    def test_pip_accepts_every_one_of_them(self):
        """The regression itself: `dicom2nifti==>=2.6.2` does not parse."""
        for lib, version, _ in self.CALL_SITES:
            text = requirement(lib, version)
            try:
                Requirement(text)
            except Exception as error:
                self.fail("pip would refuse %r: %s" % (text, error))

    def test_the_broken_form_is_indeed_broken(self):
        """Guards the test above from passing for the wrong reason."""
        with self.assertRaises(Exception):
            Requirement("dicom2nifti==>=2.6.2")

if __name__ == "__main__":
    unittest.main()
