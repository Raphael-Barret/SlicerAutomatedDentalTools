from abc import ABC, abstractmethod


# ===== Logging Configuration =====
from ADTLib.logging_setup import get_logger
from ADTLib.io.fs import search as search_files

logger = get_logger("MedX_Method")

class Method(ABC):
    def __init__(self, widget):
        self.widget = widget

    @abstractmethod
    def NbScan(self, file_folder: str):
        """
            Count the number of patient in folder
        Args:
            file_folder (str): folder path with Clinical Notes

        Return:
            int : return the number of patient.
        """
        pass

    @abstractmethod
    def TestFile(self, file_folder: str) -> str:
        """Verify if the input folder seems good (have everything required to run the mode selected), if something is wrong the function return string with error message

        This function is called when the user want to import scan

        Args:
            file_folder (str): path of folder with Clinical Notes

        Returns:
            str or None: Return str with error message if something is wrong, else return None
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
    
    @abstractmethod
    def TestModel(self, model_folder: str) -> str:
        """Verify whether the model folder contains the right models used for MedX

        Args:
            model_folder (str): folder path with the model

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

    def search(self, path, *args):
        """Délégué à ADTLib ; la signature est gardée pour les appelants."""
        return search_files(path, *args)