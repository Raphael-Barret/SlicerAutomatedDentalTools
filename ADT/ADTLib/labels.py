"""Quel tableau de points porte les numéros de dents d'un maillage.

`GetLabelSurface` et `isLabelSurface` existaient en cinq exemplaires, methodes
de cinq classes `vtkTeeth` elles-mêmes recopiées (`ASO_IOS_utils/icp.py`,
`FlexReg_utils/util.py`, `FlexReg_Method/util.py`,
`FlexReg_Method/vtkSegTeeth.py`, `AREG_IOS_utils/vtkSegTeeth.py`).

Quatre des cinq portaient le même défaut : la boucle écrivait
`out = Preference` puis faisait `continue` au lieu de `break`, si bien que le
tour suivant écrasait aussitôt la valeur trouvée. Le nom demandé n'était donc
rendu que s'il se trouvait être le **dernier** tableau du maillage ; sinon la
fonction rendait celui d'après. Un maillage portant `Universal_ID` puis
`Normals` faisait chercher les dents dans les normales. Seule la copie
d'`ASO_IOS_utils` avait `break`, et c'est elle qui est retenue : dans les
quatre autres, l'affectation `out = Preference` ne servait à rien, ce qui suffit
à dire ce qui était voulu.

Ne dépend que de l'interface vtk du maillage reçu : importable depuis
l'environnement Conda comme depuis Slicer.
"""


def array_names(surf):
    """Les noms des tableaux de données de points portés par `surf`."""
    point_data = surf.GetPointData()
    return [point_data.GetArrayName(i) for i in range(point_data.GetNumberOfArrays())]


def has_label_array(surf, name):
    """`surf` porte-t-il un tableau de points nommé `name` ?"""
    return name in array_names(surf)


def label_array(surf, preference="Universal_ID"):
    """Le tableau à utiliser comme numérotation des dents.

    `preference` s'il est là, sinon le dernier tableau du maillage, sinon
    `None` s'il n'y en a aucun. Le repli sur le dernier n'a rien d'évident,
    mais c'est ce que faisaient les cinq copies et rien n'indique laquelle
    serait la bonne : le changer demanderait de trancher, pas de refactorer.
    """
    names = array_names(surf)
    if not names:
        return None
    return preference if preference in names else names[-1]
