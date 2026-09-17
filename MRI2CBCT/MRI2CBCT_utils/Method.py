from abc import abstractmethod

# ===== Logging Configuration =====
from ADTLib.logging_setup import get_logger
from ADTLib.method import ADTMethod, DicomMethod

logger = get_logger("MRI2CBCT")


class Method(ADTMethod, DicomMethod):
    # Les dossiers d'entree dependent de l'outil : un seul pour ASO et ALI, deux
    # timepoints pour AREG et MRI2CBCT, patients et matrices pour AutoMatrix. La
    # forme variadique dit cela sans mentir sur l'arite -- l'ABC de MRI2CBCT en
    # annoncait deux la ou ses six sous-classes en prennent un. Chaque
    # implementation declare l'arite qu'elle attend vraiment.
    @abstractmethod
    def TestScan(self, *scan_folders):
        """Verify if the input folder seems good (have everything required to run the mode selected), if something is wrong the function return string with error message

        This function is called when the user want to import scan

        Args:
            scan_folder (str): path of folder with scan

        Returns:
            str and bool: Return str with error message if something is wrong and a boolean to indicate if there is a message
        pass
        """


