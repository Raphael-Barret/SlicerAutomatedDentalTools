"""Le contrat que les modules partagent, et les capacités qu'ils composent.

Six modules déclaraient leur propre `Method(ABC)` : 934 lignes dont la plus
grande part n'était pas du code mais des contrats répétés. Mesurés côte à côte,
ils ne se recouvrent pas au hasard -- trois grappes ressortent, nettes :

    noyau      ASO AREG ALI MRI2CBCT MedX AutoMatrix   Process, TestProcess,
                                                        NumberScan, search
    repères    ASO AREG ALI                            7 méthodes
    cases      ASO AREG                                5 méthodes
    DICOM      ASO AREG ALI MRI2CBCT                   3 méthodes

(MedX figure dans cette mesure parce qu'il était là quand elle a été prise ; il
a depuis été archivé dans la branche `archive/medx` et retiré de l'arbre.)

D'où un noyau et des mixins, plutôt qu'une classe unique où MedX aurait hérité
de `getcheckbox` et de `DicLandmark`. Un module compose ce qu'il offre vraiment ;
ce qu'il déclare reste vrai.

Ce qui n'est PAS ici, et pourquoi : `TestScan` et `TestModel` ont des arités
franchement différentes d'un outil à l'autre (jusqu'à quatre arguments chez
AREG), et `getModelUrl` renvoie une sélection propre à chaque outil. Les
remonter demanderait de trancher un comportement, pas de déplacer du code.
"""
from abc import ABC, abstractmethod

from ADTLib.io.fs import search as search_files
from ADTLib.io.landmarks import ListLandmarksJson as list_landmarks_json


class ADTMethod(ABC):
    """Ce que les six modules ont en commun, et rien de plus."""

    def __init__(self, widget):
        self.widget = widget
        self.diccheckbox = {}
        self.diccheckbox2 = {}

    @abstractmethod
    def Process(self, **kwargs):
        """Launch extension"""

        pass

    @abstractmethod
    def TestProcess(self, **kwargs) -> str:
        """Check if everything is OK before launching the process, if something is wrong return string with all error



        Returns:
            str or None: return None if there no problem with input of the process, else return str with all error
        """
        pass

    @abstractmethod
    def NumberScan(self, *scan_folders):
        """
            Count the number of patient in folder
        Args:
            scan_folder_t1 (str): folder path with Scan for T1
            scan_folder_t2 (str): folder path with Scan for T2

        Return:
            int : return the number of patient.
        """
        pass

    def search(self, path, *args):
        """Délégué à ADTLib ; la signature est gardée pour les appelants."""
        return search_files(path, *args)


class LandmarkMethod(ABC):
    """Les outils qui manipulent des points de repère : ASO, AREG, ALI."""

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
    def getALIModelList(self):
        """
                Return a tuple with both the name and the Download link for ALI model
        else:
                    name, url = self.ActualMeth.getTestFileList()

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
    def getTestFileList(self):
        """Return a tuple with both the name and the Download link of the test files

        tuple = ('name','link')
        """
        pass

    @abstractmethod
    def TestReference(self, ref_folder: str) -> str:
        """Verify if the reference folder contains reference gold files with landmarks and scans, if True return None and if False return str with error message to user

        Args:
            ref_folder (str): folder path with gold landmark

        Return :
            str or None : display str to user like warning
        """

        pass

    def ListLandmarksJson(self, json_file):
        """Délégué à ADTLib."""
        return list_landmarks_json(json_file)


class CheckboxMethod(ABC):
    """Les outils dont l'interface porte des cases à cocher : ASO, AREG."""

    @abstractmethod
    def TestCheckbox(self) -> str:
        pass

    def getcheckbox(self):
        return self.diccheckbox

    def setcheckbox(self, checkboxes):
        self.diccheckbox = checkboxes

    def getcheckbox2(self):
        return self.diccheckbox2

    def setcheckbox2(self, checkboxes):
        self.diccheckbox2 = checkboxes


class DicomMethod(ABC):
    """Les outils qui acceptent du DICOM en entrée."""

    def NumberScanDCM(self, *scan_folders):
        """
            Count the number of patient in folder for DCM as input
        Args:
            scan_folder_t1 (str): folder path with Scan for T1
            scan_folder_t2 (str): folder path with Scan for T2

        Return:
            int : return the number of patient.
        """
        pass

    def TestScanDCM(self, *scan_folders) -> str:
        """Verify if the input folder seems good (have everything required to run the mode selected), if something is wrong the function return string with error message for DCM as input

        This function is called when the user want to import scan

        Args:
            scan_folder (str): path of folder with scan

        Returns:
            str or None: Return str with error message if something is wrong, else return None
        """
        pass

    def getTestFileListDCM(self):
        """Return a tuple with both the name and the Download link of the test files but only for DCM files (AREG CBCT)
        tuple = ('name','link')
        """
        pass
