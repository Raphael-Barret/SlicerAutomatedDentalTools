from abc import abstractmethod
from ADTLib.method import ADTMethod


class Method(ADTMethod):
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
            patient_folder (str): path of folder with scans
            matrix_folder (str): path of folder with matrices

        Returns:
            str or None: Return str with error message if something is wrong, else return None
        pass
        """
        