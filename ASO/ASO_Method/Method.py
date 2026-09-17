from abc import abstractmethod

# ===== Logging Configuration =====
from ADTLib.logging_setup import get_logger
from ADTLib.method import ADTMethod, LandmarkMethod, CheckboxMethod, DicomMethod

logger = get_logger("ASO_Method")


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
    def Suggest(self):
        pass

    @abstractmethod
    def getSegOrModelList(self):
        """
        Return a tuple with both the name and the Download link of the Seg or Or model

        tuple = ('name','link')

        """
        pass
