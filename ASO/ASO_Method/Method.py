from abc import abstractmethod

# ===== Logging Configuration =====
from ADTLib.logging_setup import get_logger
from ADTLib.method import ADTMethod, LandmarkMethod, CheckboxMethod, DicomMethod

logger = get_logger("ASO_Method")


class Method(ADTMethod, LandmarkMethod, CheckboxMethod, DicomMethod):
    """Le contrat d'une methode d'ASO, et la description de son interface.

    Les quatre attributs ci-dessous disent ce que l'interface doit montrer
    quand cette methode est choisie. Ils vivaient auparavant dans le widget,
    sous la forme d'une chaine de `if/elif` sur des index de liste deroulante
    et d'un `isinstance` : l'abstraction existait, et les appelants la
    court-circuitaient. Ajouter une cinquieme methode demandait d'aller
    modifier le widget.

    Ce sont des donnees, pas des appels a Qt : la methode decrit, le widget
    applique. Rien ici n'importe `qt`, et les methodes restent utilisables
    hors interface.
    """

    #: page du `stackedWidget` a afficher
    stacked_page = 0
    #: ce que le widget range dans `self.type`
    scan_type = "CBCT"
    #: la liste deroulante du type d'entree CBCT est-elle montree
    shows_cbct_input = True
    #: texte de `label_7`, ou None pour laisser celui qui s'y trouve
    model_label = None
    #: la methode travaille-t-elle a partir d'un modele de segmentation
    #: (ce que testait `isinstance(meth, (Auto_IOS, Semi_IOS))`)
    uses_segmentation_model = False

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
