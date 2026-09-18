"""Les adresses de publication, écrites une fois.

Ce module ne dit pas *quels* modèles un outil propose -- cette sélection lui
appartient et diffère d'un outil à l'autre, c'est pourquoi les dictionnaires
`getModelUrl` restent chez eux. Il ne porte que les **bases de release**, celles
qui se répétaient à l'identique : publier une nouvelle version demandait de
retrouver 32 littéraux pour la seule release des modèles ADT.

Bibliothèque standard seulement.
"""

#: Release portant les modèles de repères et de segmentation de l'extension.
#: Changer de version se fait ici, et nulle part ailleurs.
ADT_MODELS = (
    "https://github.com/DCBIA-OrthoLab/SlicerAutomatedDentalTools"
    "/releases/download/v0.1-v2.0_models"
)

#: L'installeur WSL2 que les modules proposent quand WSL manque, ou que ses
#: bibliothèques système manquent. Le lien était recopié dans six modules, et
#: deux fois dans chacun.
WSL2_INSTALLER = (
    "https://github.com/DCBIA-OrthoLab/SlicerAutomatedDentalTools"
    "/releases/download/wsl2_windows/installer_WSL2.zip"
)


#: Les modèles de plans de référence d'ASO_CBCT, que quatre modules proposent.
#: Seize littéraux portaient cette base ; la sélection, elle, reste chez chacun.
ASO_CBCT_GOLD = (
    "https://github.com/lucanchling/ASO_CBCT/releases/download/v01_goldmodels"
)

#: Les références et modèles d'ASO_IOS, partagés par ALI, ASO et AREG.
ASO_IOS_GOLD = "https://github.com/HUTIN1/ASO/releases/download/v1.0.0"

#: Les jeux d'essai publiés par Slicer, utilisés par `registerSampleData`.
SLICER_TESTING_DATA = (
    "https://github.com/Slicer/SlicerTestingData/releases/download/SHA256"
)
