from abc import ABC, abstractmethod

# ===== Logging Configuration =====
from ADTLib.logging_setup import get_logger
from ADTLib.io.fs import search as search_files
from ADTLib.io.landmarks import ListLandmarksJson as list_landmarks_json

logger = get_logger("ASO_Method")


class Method(ABC):
    def __init__(self, widget):
        self.widget = widget
        self.diccheckbox = {}
        self.diccheckbox2 = {}

    @abstractmethod
    def NumberScan(self, scan_folder: str):
        """
            Count the number of patient in folder
        Args:
            scan_folder (str): folder path with Scan


        Return:
            int : return the number of patient.
        """
        pass

    @abstractmethod
    def TestScan(self, scan_folder: str) -> str:
        """Verify if the input folder seems good (have everything required to run the mode selected), if something is wrong the function return string with error message

        This function is called when the user want to import scan

        Args:
            scan_folder (str): path of folder with scan

        Returns:
            str or None: Return str with error message if something is wrong, else return None
        pass
        """

    @abstractmethod
    def TestReference(self, ref_folder: str) -> str:
        """Verify if the reference folder contains reference gold files with landmarks and scans, if True return None and if False return str with error message to user

        Args:
            ref_folder (str): folder path with gold landmark

        Return :
            str or None : display str to user like warning
        """

        pass

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
    def TestCheckbox(self) -> str:
        pass

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
    def DicLandmark(self):
        """
        return dic landmark like this:
        dic = {'teeth':{
                        'Lower':['LR6','LR5',...],
                        'Upper':['UR6',...]
                        },
                'Landmark':{
                        'Occlusual':['O',...],
                        'Cervical':['R',...]
                        }
                }
        """

        pass

    @abstractmethod
    def existsLandmark(self, pathfile: str, pathref: str, pathmodel: str):
        """return dictionnary. when the value of the landmark in dictionnary is true, the landmark is in input folder and in gold folder
        Args:
            pathfile (str): path

        Return :
        dict : exemple dic = {'O':True,'UL6':False,'UR1':False,...}
        """
        pass

    @abstractmethod
    def Suggest(self):
        pass

    @abstractmethod
    def getTestFileList(self):
        """Return a tuple with both the name and the Download link of the test files

        tuple = ('name','link')
        """
        pass

    @abstractmethod
    def getReferenceList(self):
        """
        Return a dictionnary with both the name and the Download link of the references

        dict = {'name1':'link1','name2':'link2',...}

        """
        pass

    @abstractmethod
    def getSegOrModelList(self):
        """
        Return a tuple with both the name and the Download link of the Seg or Or model

        tuple = ('name','link')

        """
        pass

    @abstractmethod
    def getALIModelList(self):
        """
        Return a tuple with both the name and the Download link for ALI model

        tuple = ('name','link')

        """
        pass

    def getcheckbox(self):
        return self.diccheckbox

    def setcheckbox(self, checkboxes):
        self.diccheckbox = checkboxes

    def getcheckbox2(self):
        return self.diccheckbox2

    def setcheckbox2(self, checkboxes):
        self.diccheckbox2 = checkboxes

    def search(self, path, *args):
        """Délégué à ADTLib ; la signature est gardée pour les appelants."""
        return search_files(path, *args)

    def ListLandmarksJson(self, json_file):
        """Délégué à ADTLib."""
        return list_landmarks_json(json_file)

    def getTestFileListDCM(self):
        """Return a tuple with both the name and the Download link of the test files but only for DCM files (AREG CBCT)
        tuple = ('name','link')
        """
        pass

    def TestScanDCM(self, scan_folder: str) -> str:
        """Verify if the input folder seems good (have everything required to run the mode selected), if something is wrong the function return string with error message for DCM as input

        This function is called when the user want to import scan

        Args:
            scan_folder (str): path of folder with scan

        Returns:
            str or None: Return str with error message if something is wrong, else return None
        """
        pass

    def NumberScanDCM(self, scan_folder: str):
        """
            Count the number of patient in folder for DCM as input
        Args:
            scan_folder (str): folder path with Scan

        Return:
            int : return the number of patient.
        """
        pass
