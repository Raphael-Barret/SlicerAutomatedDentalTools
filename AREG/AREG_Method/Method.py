from abc import abstractmethod
import os
import glob
import re
import shutil

# ===== Logging Configuration =====
from ADTLib.logging_setup import get_logger
from ADTLib.method import ADTMethod, LandmarkMethod, CheckboxMethod, DicomMethod

logger = get_logger("AREG_Method")


# Name of the conda environment SlicerDentalModelSeg installs its tools into.
SEGMENTATION_ENV = "shapeaxi"
SEGMENTATION_EXECUTABLE = "dentalmodelseg"


def FindDentalModelSeg():
    """Where dentalmodelseg actually is on this machine.

    The path built here used to be `<Slicer>/lib/Python/bin/dentalmodelseg`,
    which holds only when the tool was pip-installed into Slicer's own
    interpreter. That is not how SlicerDentalModelSeg installs it: it creates a
    conda environment, and its own module asks conda where the executable
    landed rather than assuming. Where the file is absent, CrownSegmentationcli
    runs it anyway and dies on FileNotFoundError -- which takes the whole
    registration with it, since the mucogingival flow segments the scans first.

    The historical path is still tried first, so an install that has it keeps
    behaving exactly as before, and it is what gets returned when nothing is
    found, so the failure a user sees does not change either.
    """
    import slicer

    historical = os.path.join(slicer.app.applicationDirPath(), "..",
                              "lib", "Python", "bin", SEGMENTATION_EXECUTABLE)
    if os.path.isfile(historical):
        return historical

    try:
        from CondaSetUp import CondaSetUpCall, CondaSetUpCallWsl
        import platform
        conda = (CondaSetUpCallWsl() if platform.system() == "Windows"
                 else CondaSetUpCall())
        answer = conda.condaRunCommand(["which", SEGMENTATION_EXECUTABLE],
                                       SEGMENTATION_ENV)
        found = re.search(r"Result: (.+)", answer or "")
        if found:
            path = found.group(1).strip().replace("\\n", "")
            if path:
                logger.info(f"Found {SEGMENTATION_EXECUTABLE} in the "
                            f"{SEGMENTATION_ENV} environment")
                return path
    except Exception as error:
        logger.warning(f"Could not ask conda for {SEGMENTATION_EXECUTABLE}: {error}")

    # Asking conda needs a live Slicer session; when there is none, look for
    # the environment on disk instead. This only ever returns a file that is
    # there, so it is a search rather than another assumption.
    beside = os.path.join(slicer.app.applicationDirPath(), "*conda*", "envs",
                          SEGMENTATION_ENV, "bin", SEGMENTATION_EXECUTABLE)
    for candidate in sorted(glob.glob(beside)):
        if os.path.isfile(candidate):
            logger.info(f"Found {SEGMENTATION_EXECUTABLE} at {candidate}")
            return candidate

    on_path = shutil.which(SEGMENTATION_EXECUTABLE)
    if on_path:
        return on_path

    logger.warning(f"{SEGMENTATION_EXECUTABLE} was not found; the segmentation "
                   "will report that its executable is missing")
    return historical


class Method(ADTMethod, LandmarkMethod, CheckboxMethod, DicomMethod):
    # Les dossiers d'entree dependent de l'outil : un seul pour ASO et ALI, deux
    # timepoints pour AREG et MRI2CBCT, patients et matrices pour AutoMatrix. La
    # forme variadique dit cela sans mentir sur l'arite -- l'ABC de MRI2CBCT en
    # annoncait deux la ou ses six sous-classes en prennent un. Chaque
    # implementation declare l'arite qu'elle attend vraiment.
    @abstractmethod
    def TestScan(self, *scan_folders) -> str:
        """Verify if the input folder seems good (have everything required to run the mode selected), if something is wrong the function return string with error message

        This function is called when the user want to import scan

        Args:
            scan_folder (str): path of folder with scan

        Returns:
            str or None: Return str with error message if something is wrong, else return None
        pass
        """

    @abstractmethod
    def TestModel(self, model_folder: str, lineEditName) -> str:
        """Verify whether the model folder contains the right models used for ALI and other AI tool

        Args:
            model_folder (str): folder path with different models

        Return :
            str or None : display str to user like warning
        """

        pass

    @abstractmethod
    def getModelUrl(self):
        """
        Return dictionnary contains the url for each model

        dict = {'name':{'type1':'url1','type2':'url2'},...}
        or
        dict = {'name':'url'}

        """
        pass

    def getReviewSteps(self, **kwargs) -> list:
        """Pauses this mode can offer, in the order the run reaches them.

        Declared without running Process(): the widget needs the list to build
        its checkboxes long before anything is computed, and Process() creates
        folders on the way.

        Returns:
            list: catalogue entries, each carrying its id
        """
        return []
