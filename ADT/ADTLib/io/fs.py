"""Trouver les fichiers d'un dossier par extension.

`search` existait en quinze exemplaires, en six variantes. Toutes s'y ramènent
maintenant, et les deux seules différences de fond sont devenues des paramètres :

- six étaient une méthode `search(self, ...)`, trois la même chose en fonction
  libre -- identiques à l'octet près une fois le `self` retiré ;
- trois entouraient le résultat d'un `sorted()`, d'où `sort`. L'ordre de
  parcours des patients en dépend chez elles ;
- celle de `ASO_IOS_utils/data_file.py` écartait en plus ce qui n'est pas un
  fichier, d'où `files_only`. Un dossier dont le nom finit par l'extension
  cherchée -- `patient.nrrd/` -- est compté comme un scan par les quatorze
  autres. C'est sans doute un défaut partout, mais personne n'en a jamais vu
  l'effet, alors le comportement d'origine reste celui par défaut et seul
  l'appelant qui demandait le filtre continue de l'obtenir.

Celle de VFACE ne rangeait pas le résultat de la même façon -- un seul parcours
de l'arbre, trié, puis réparti par clé -- mais rend exactement ce que rend
`sort=True`.

Bibliothèque standard seulement : appelé depuis l'environnement Conda.
"""
import glob
import os


def search(path, *args, sort=False, files_only=False):
    """Les fichiers de `path` groupés par extension demandée.

    Renvoie un dictionnaire dont chaque clé est un élément de `args` et la
    valeur la liste des fichiers de `path` qui se terminent par cette clé.
    Une liste passée dans `args` est aplatie.

        search(path, 'json', ['.nii.gz', '.nrrd'])
        {'json': ['path/a.json', ...], '.nii.gz': [...], '.nrrd': [...]}

    `sort` rend chaque liste triée : trois des quinze sites d'origine le
    faisaient, et l'ordre de parcours des patients en dépend chez eux.

    `files_only` écarte les répertoires dont le nom se termine par la clé : un
    seul site d'origine le faisait.
    """
    arguments = []
    for arg in args:
        if isinstance(arg, list):
            arguments.extend(arg)
        else:
            arguments.append(arg)

    # Un chemin vide donnait le motif `/**/*` : glob repartait de la racine du
    # disque et Slicer se figeait. On l'atteint en lancant AREG IOS avec le
    # champ « Registration Model Folder » vide (AREG_Method/IOS.py). Un dossier
    # inexistant rendait deja un resultat vide -- glob n'y trouve rien -- donc
    # c'est le meme contrat qu'on applique ici, sans parcourir quoi que ce soit.
    if not path or not os.path.isdir(path):
        return {key: [] for key in arguments}

    entries = list(
        glob.iglob(os.path.normpath("/".join([path, "**", "*"])), recursive=True)
    )
    if files_only:
        entries = [entry for entry in entries if os.path.isfile(entry)]
    if sort:
        entries.sort()

    return {key: [entry for entry in entries if entry.endswith(key)] for key in arguments}
