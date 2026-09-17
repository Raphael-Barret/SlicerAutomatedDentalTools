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

from ADTLib.env.deps import check_lib_installed, normalise_spec  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
