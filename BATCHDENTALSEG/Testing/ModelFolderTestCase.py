"""What the shared model folder is allowed to do.

Resources/ML holds every bundle the module can run, and three separate
mechanisms used to treat it as though it held one: nnUNet was handed the
folder and picked a bundle by glob order, the dependency checker asked
"are the weights here?" of the whole folder, and a download cleared all of
it. These tests pin the three down, and the resampling swap that reads a
bundle's plans without ever writing to it.

They build fake bundles rather than use the real ones: a test that needs
782 MB of weights downloaded first is a test nobody runs.
"""

import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock


from BATCHDENTALSEGLib.PythonDependencyChecker import (
    DENTALSEGMENTATOR_DATASET,
    PythonDependencyChecker,
)
from BATCHDENTALSEGLib.SegmentationWidget import SegmentationWidget

CONFIGURATION = "nnUNetTrainer__nnUNetPlans__3d_fullres"

#: What the shipped plans say for the probabilities: the stock resampler,
#: order 1. The swap is allowed exactly here and nowhere else.
STOCK_PROBABILITY_KWARGS = {"is_seg": False, "order": 1, "order_z": 0, "force_separate_z": None}


def write_bundle(root, dataset_name, with_weights=True, probability_kwargs=None):
    """A model bundle on disk, shaped the way nnUNet expects to find one."""
    configuration = Path(root).joinpath(dataset_name, CONFIGURATION)
    configuration.mkdir(parents=True, exist_ok=True)
    with open(configuration.joinpath("dataset.json"), "w") as handle:
        json.dump({"labels": {"background": 0, "Mandible": 1}, "file_ending": ".nii.gz"}, handle)
    plans = {
        "configurations": {
            "3d_fullres": {
                "spacing": [0.4, 0.4, 0.4],
                "resampling_fn_data": "resample_data_or_seg_to_shape",
                "resampling_fn_probabilities": "resample_data_or_seg_to_shape",
                "resampling_fn_probabilities_kwargs":
                    dict(STOCK_PROBABILITY_KWARGS if probability_kwargs is None
                         else probability_kwargs),
            }
        }
    }
    with open(configuration.joinpath("plans.json"), "w") as handle:
        json.dump(plans, handle)
    if with_weights:
        fold = configuration.joinpath("fold_0")
        fold.mkdir(exist_ok=True)
        fold.joinpath("checkpoint_final.pth").write_bytes(b"not really a checkpoint")
    return configuration


class ModelPathTestCase(unittest.TestCase):
    """Every model names its own bundle."""

    def setUp(self):
        # Not deleted on teardown: PythonQt hands the C++ widget back to Qt
        # and a later frame of the spinner would reach freed memory.
        self.widget = SegmentationWidget(logic=MagicMock())

    def test_every_model_resolves_to_its_own_bundle(self):
        models = ["DentalSegmentator", "PediatricDentalsegmentator",
                  "NasoMaxillaDentSeg", "UniversalLabDentalsegmentator"]
        paths = {name: self.widget._modelBasePath(name) for name in models}
        self.assertEqual(len(set(paths.values())), len(models),
                         f"two models share a bundle: {paths}")

    def test_dentalsegmentator_does_not_get_the_shared_folder(self):
        # Handed Resources/ML, nnUNet takes the first dataset.json its glob
        # returns. Once the universal weights are there, that is Dataset002:
        # asking for DentalSegmentator ran the 56 class model in silence.
        shared = self.widget.nnUnetFolder()
        resolved = self.widget._modelBasePath("DentalSegmentator")
        self.assertNotEqual(Path(resolved), Path(shared))
        self.assertEqual(Path(resolved).parent.name, DENTALSEGMENTATOR_DATASET)

    def test_the_model_list_offers_exactly_the_models_we_can_resolve(self):
        offered = [self.widget.modelComboBox.itemText(i)
                   for i in range(self.widget.modelComboBox.count)]
        for name in offered:
            self.assertNotEqual(Path(self.widget._modelBasePath(name)),
                                Path(self.widget.nnUnetFolder()),
                                f"{name} falls back to the shared folder")


class TorchResamplingTestCase(unittest.TestCase):
    """The probability resampler is swapped, and only when it is safe to."""

    def setUp(self):
        self.widget = SegmentationWidget(logic=MagicMock())
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.configuration = write_bundle(self.tmp.name, "Dataset002_380CT")
        # The RAM guard is not what these tests are about; the volume and
        # the model name reach it through the same call, so it is answered
        # here and exercised in its own test.
        self.widget._torchResamplingFitsInRam = MagicMock(return_value=True)

    def parameter(self):
        from SlicerNNUNetLib import Parameter
        return Parameter(folds="0", modelPath=self.configuration, device="cuda")

    @staticmethod
    def probability_resampler(configuration_folder):
        with open(Path(configuration_folder).joinpath("plans.json")) as handle:
            configuration = json.load(handle)["configurations"]["3d_fullres"]
        return (configuration["resampling_fn_probabilities"],
                configuration.get("resampling_fn_probabilities_kwargs") or {})

    def test_the_mirror_names_the_torch_resampler(self):
        result = self.widget._withTorchProbabilityResampling(self.parameter(), MagicMock(), "any")
        name, kwargs = self.probability_resampler(result.modelPath)
        self.assertEqual(name, "resample_torch_fornnunet")
        self.assertEqual(kwargs["mode"], "linear")
        # A torch.device would not survive json.dump.
        self.assertIsInstance(kwargs["device"], str)

    def test_the_downloaded_bundle_is_never_written_to(self):
        # It lives in the extension's own source tree, and one of the two
        # bundles is tracked by git.
        before = self.probability_resampler(self.configuration)
        self.widget._withTorchProbabilityResampling(self.parameter(), MagicMock(), "any")
        self.assertEqual(self.probability_resampler(self.configuration), before)

    def test_the_mirror_keeps_the_two_names_nnunet_reads(self):
        # nnUNet derives -d and -tr/-p/-c from these two directory names.
        result = self.widget._withTorchProbabilityResampling(self.parameter(), MagicMock(), "any")
        mirror = Path(result.modelPath)
        self.assertEqual(mirror.name, CONFIGURATION)
        self.assertEqual(mirror.parent.name, "Dataset002_380CT")

    def test_the_weights_are_linked_not_copied(self):
        result = self.widget._withTorchProbabilityResampling(self.parameter(), MagicMock(), "any")
        fold = Path(result.modelPath).joinpath("fold_0")
        self.assertTrue(fold.exists())
        self.assertTrue(os.path.islink(fold), "the checkpoint was copied instead of linked")

    def test_other_orders_are_left_alone(self):
        # Order 1 is what torch 'linear' does. Anything else is a different
        # interpolation, and swapping it would change the segmentation.
        configuration = write_bundle(
            self.tmp.name, "Dataset999_other",
            probability_kwargs={"is_seg": False, "order": 3, "order_z": 0, "force_separate_z": None})
        from SlicerNNUNetLib import Parameter
        given = Parameter(folds="0", modelPath=configuration, device="cuda")
        result = self.widget._withTorchProbabilityResampling(given, MagicMock(), "any")
        self.assertEqual(Path(result.modelPath), Path(configuration))

    def test_a_custom_resampler_is_left_alone(self):
        configuration = write_bundle(self.tmp.name, "Dataset998_custom")
        plans_path = Path(configuration).joinpath("plans.json")
        plans = json.loads(plans_path.read_text())
        plans["configurations"]["3d_fullres"]["resampling_fn_probabilities"] = "no_resampling"
        plans_path.write_text(json.dumps(plans))
        from SlicerNNUNetLib import Parameter
        given = Parameter(folds="0", modelPath=configuration, device="cuda")
        result = self.widget._withTorchProbabilityResampling(given, MagicMock(), "any")
        self.assertEqual(Path(result.modelPath), Path(configuration))

    def test_the_swap_is_refused_when_the_ram_is_not_there(self):
        self.widget._torchResamplingFitsInRam = MagicMock(return_value=False)
        result = self.widget._withTorchProbabilityResampling(self.parameter(), MagicMock(), "any")
        self.assertEqual(Path(result.modelPath), Path(self.configuration))


class WeightFolderTestCase(unittest.TestCase):
    """A model's download concerns that model only."""

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.shared = Path(self.tmp.name)
        self.checker = PythonDependencyChecker(destWeightFolder=self.shared)

    def test_a_neighbour_bundle_does_not_pass_for_this_one(self):
        # The checker used to search the whole shared folder, so the
        # universal weights answered for DentalSegmentator's.
        write_bundle(self.shared, "Dataset002_380CT", with_weights=True)
        self.assertTrue(self.checker.areWeightsMissing())

    def test_its_own_weights_are_found(self):
        write_bundle(self.shared, DENTALSEGMENTATOR_DATASET, with_weights=True)
        self.assertFalse(self.checker.areWeightsMissing())

    def test_markers_without_weights_still_count_as_missing(self):
        write_bundle(self.shared, DENTALSEGMENTATOR_DATASET, with_weights=False)
        self.assertTrue(self.checker.areWeightsMissing())

    def test_extraction_does_not_leave_the_archive_behind(self):
        import zipfile
        bundle = write_bundle(self.shared, DENTALSEGMENTATOR_DATASET)
        archive = self.shared.joinpath("weights.zip")
        with zipfile.ZipFile(archive, "w") as handle:
            handle.write(bundle.joinpath("plans.json"),
                         f"{DENTALSEGMENTATOR_DATASET}/{CONFIGURATION}/plans.json")
        self.checker.extractWeightsToWeightsFolder(archive)
        self.assertFalse(archive.exists())


class BatchDentalSegModelFolderTest(unittest.TestCase):
    """Entry point for Slicer's own runner."""

    def runTest(self):
        suite = unittest.TestSuite()
        for case in (ModelPathTestCase, TorchResamplingTestCase, WeightFolderTestCase):
            suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(case))
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        self.assertTrue(result.wasSuccessful(), result.errors + result.failures)
