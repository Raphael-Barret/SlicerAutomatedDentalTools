"""Trouver les fichiers d'un dossier par extension.

`search` existait en quinze exemplaires, en six variantes. Douze d'entre eux se
ramènent à cette seule fonction : six étaient une méthode `search(self, ...)`,
trois la même chose en fonction libre -- identiques à l'octet près une fois le
`self` retiré -- et trois ne différaient que par un `sorted()` autour du
résultat, d'où le paramètre `sort`.

Les trois derniers divergent réellement (celui de `data_file.py` filtre en plus,
celui de VFACE et celui d'ALI_CBCT ont un autre corps) et restent chez eux.

Bibliothèque standard seulement : appelé depuis l'environnement Conda.
"""
import glob
import os


def search(path, *args, sort=False):
    """Les fichiers de `path` groupés par extension demandée.

    Renvoie un dictionnaire dont chaque clé est un élément de `args` et la
    valeur la liste des fichiers de `path` qui se terminent par cette clé.
    Une liste passée dans `args` est aplatie.

        search(path, 'json', ['.nii.gz', '.nrrd'])
        {'json': ['path/a.json', ...], '.nii.gz': [...], '.nrrd': [...]}

    `sort` rend chaque liste triée : trois des douze sites d'origine le
    faisaient, et l'ordre de parcours des patients en dépend chez eux.
    """
    arguments = []
    for arg in args:
        if isinstance(arg, list):
            arguments.extend(arg)
        else:
            arguments.append(arg)

    found = {
        key: [
            match
            for match in glob.iglob(
                os.path.normpath("/".join([path, "**", "*"])), recursive=True
            )
            if match.endswith(key)
        ]
        for key in arguments
    }
    return {key: sorted(v) for key, v in found.items()} if sort else found
