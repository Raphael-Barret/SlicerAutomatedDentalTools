# Ce que les dataclasses de requete changent, et surtout ce qu elles ne
# changent PAS.
#
# Le point qui compte : un champ non fourni doit lever exactement ce que
# `kwargs["champ"]` levait -- meme type d erreur, meme message. Sans cela, le
# passage a la dataclass transformerait une panne franche en valeur vide qui
# traverse tout le traitement.
import os
import sys
import unittest

# ADTLib, que les paquets importent desormais : une suite de tests est un
# point d entree comme un autre, rien ne l a mis sur sys.path avant elle.
_ADT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "ADT")
if os.path.isdir(_ADT):
    sys.path.insert(0, _ADT)

from ADTLib.requests import (  # noqa: E402
    MISSING,
    ALIRequest,
    AREGRequest,
    ASORequest,
    ProcessRequest,
    VFACERequest,
)


class AbsentFieldTest(unittest.TestCase):

    def test_reading_a_field_nobody_gave_raises_what_the_dict_raised(self):
        """`kwargs["log_path"]` levait KeyError('log_path'). Idem ici."""
        request = ASORequest(input_folder="/in")
        with self.assertRaises(KeyError) as caught:
            _ = request.log_path
        self.assertEqual(caught.exception.args, ("log_path",))

    def test_the_same_error_as_a_plain_dict(self):
        kwargs = {"input_folder": "/in"}
        with self.assertRaises(KeyError) as from_dict:
            _ = kwargs["log_path"]
        with self.assertRaises(KeyError) as from_request:
            _ = ASORequest(input_folder="/in").log_path
        self.assertEqual(type(from_dict.exception), type(from_request.exception))
        self.assertEqual(from_dict.exception.args, from_request.exception.args)

    def test_a_field_that_was_given_reads_normally(self):
        self.assertEqual(ASORequest(input_folder="/in").input_folder, "/in")

    def test_given_answers_without_raising(self):
        request = ASORequest(input_folder="/in")
        self.assertTrue(request.given("input_folder"))
        self.assertFalse(request.given("log_path"))

    def test_provided_lists_only_what_was_given(self):
        request = ASORequest(input_folder="/in", output_folder="/out")
        self.assertEqual(request.provided(), ["input_folder", "output_folder"])

    def test_an_absent_field_refuses_to_be_a_boolean(self):
        """Le piege le plus discret : `if request.champ:` sur un champ absent
        repondrait False au lieu de lever, et le traitement continuerait."""
        with self.assertRaises(KeyError):
            bool(MISSING)


class UnknownKeyTest(unittest.TestCase):

    def test_a_key_the_family_does_not_declare_is_refused(self):
        """Avant, une faute de frappe a l appel etait silencieusement ignoree :
        la cle atterrissait dans le sac et personne ne la lisait."""
        with self.assertRaises(TypeError):
            ASORequest(input_folder="/in", ouput_folder="/typo")

    def test_a_key_of_another_family_is_refused_too(self):
        with self.assertRaises(TypeError):
            ALIRequest(input_t1_folder="/a")


class DefaultsTest(unittest.TestCase):

    def test_the_defaults_are_those_the_code_passed_to_kwargs_get(self):
        """Ces valeurs ne sont pas choisies : ce sont celles qui etaient
        ecrites dans les `kwargs.get(..., defaut)` remplaces."""
        self.assertEqual(AREGRequest().input_t1_folder, "")
        self.assertEqual(AREGRequest().input_t2_folder, "")
        self.assertEqual(AREGRequest().mgl_landmarks, "")
        self.assertEqual(AREGRequest().patch_radius, "5.0")
        self.assertIsNone(AREGRequest().reg_type)
        self.assertEqual(ALIRequest().teeth_mg, "None")


class WithTest(unittest.TestCase):

    def test_a_copy_replaces_what_is_asked_and_keeps_the_rest(self):
        request = AREGRequest(input_t1_folder="/t1", output_folder="/out")
        copy = request.with_(input_t1_folder="/seg")
        self.assertEqual(copy.input_t1_folder, "/seg")
        self.assertEqual(copy.output_folder, "/out")

    def test_a_copy_keeps_absent_fields_absent(self):
        """`dataclasses.replace` echouerait ici : il relit tous les champs."""
        copy = AREGRequest(output_folder="/out").with_(output_folder="/other")
        with self.assertRaises(KeyError):
            _ = copy.log_path

    def test_the_original_is_untouched(self):
        request = AREGRequest(input_t1_folder="/t1")
        request.with_(input_t1_folder="/seg")
        self.assertEqual(request.input_t1_folder, "/t1")


class FamiliesTest(unittest.TestCase):

    def test_every_family_shares_the_three_common_fields(self):
        for family in (ASORequest, ALIRequest, AREGRequest, VFACERequest):
            self.assertTrue(issubclass(family, ProcessRequest), family.__name__)
            for field in ("input_folder", "output_folder", "log_path"):
                self.assertTrue(hasattr(family(), "given"), family.__name__)
                self.assertFalse(family().given(field), f"{family.__name__}.{field}")


if __name__ == "__main__":
    unittest.main()
