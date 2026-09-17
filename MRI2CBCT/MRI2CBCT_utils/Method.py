from abc import ABC, abstractmethod

# ===== Logging Configuration =====
from ADTLib.logging_setup import get_logger
from ADTLib.io.fs import search as search_files

logger = get_logger("MRI2CBCT")


class Method(ABC):
    def __init__(self, widget):
        self.widget = widget
        self.diccheckbox = {}
        self.diccheckbox2 = {}

    @abstractmethod
    def NumberScan(self, scan_folder_t1: str, scan_folder_t2: str):
        """
            Count the number of patient in folder
        Args:
            scan_folder_t1 (str): folder path with Scan for T1
            scan_folder_t2 (str): folder path with Scan for T2

        Return:
            int : return the number of patient.
        """
        pass

    @abstractmethod
    def TestScan(self, scan_folder_t1: str, scan_folder_t2):
        """Verify if the input folder seems good (have everything required to run the mode selected), if something is wrong the function return string with error message

        This function is called when the user want to import scan

        Args:
            scan_folder (str): path of folder with scan

        Returns:
            str and bool: Return str with error message if something is wrong and a boolean to indicate if there is a message
        pass
        """



    @abstractmethod
    def TestProcess(self, **kwargs) -> str:
        """Check if everything is OK before launching the process, if something is wrong return string with all error



        Returns:
            str or None: return None if there no problem with input of the process, else return str with all error
        """
        pass

    @abstractmethod
    def Process(self, **kwargs):
        """Launch extension"""

        pass

    def search(self, path, *args):
        """Délégué à ADTLib ; la signature est gardée pour les appelants."""
        return search_files(path, *args)
        


    def getTestFileListDCM(self):
        """Return a tuple with both the name and the Download link of the test files but only for DCM files (AREG CBCT)
        tuple = ('name','link')
        """
        pass

    def TestScanDCM(self, scan_folder_t1: str, scan_folder_t2) -> str:
        """Verify if the input folder seems good (have everything required to run the mode selected), if something is wrong the function return string with error message for DCM as input

        This function is called when the user want to import scan

        Args:
            scan_folder (str): path of folder with scan

        Returns:
            str or None: Return str with error message if something is wrong, else return None
        """
        pass

    def NumberScanDCM(self, scan_folder_t1: str, scan_folder_t2: str):
        """
            Count the number of patient in folder for DCM as input
        Args:
            scan_folder_t1 (str): folder path with Scan for T1
            scan_folder_t2 (str): folder path with Scan for T2

        Return:
            int : return the number of patient.
        """
        pass
    
    