"""Ce que chaque famille d'outils accepte dans son `Process`, déclaré une fois.

Le contrat `Process(**kwargs)` est le même mot dans les six `Method.py`, mais
personne ne sait ce que chacun attend : les clés n'apparaissent qu'au fond des
corps, sous la forme `kwargs["..."]`. Quatre cent soixante-treize accès, aucune
liste nulle part, aucune vérification, et une faute de frappe qui ne se voit
qu'à l'exécution, sur le chemin où elle est lue.

Ici chaque famille déclare ses champs. Trois choses en découlent : la liste
existe et se lit d'un coup d'œil, une clé inconnue est refusée **à la
construction** plutôt qu'ignorée, et l'éditeur sait compléter.

Pourquoi un témoin d'absence plutôt que des valeurs par défaut
--------------------------------------------------------------
Les appelants passent volontairement des sous-ensembles différents : un
`TestProcess` n'a pas besoin de ce qu'il faut à `Process`, et les auxiliaires
internes d'AREG se contentent de deux ou trois clés. Donner un défaut à tout
transformerait donc la panne d'aujourd'hui -- `KeyError` sur la clé absente --
en une valeur vide qui traverse le traitement sans rien dire.

Un champ non fourni vaut donc `MISSING`, et le lire lève `KeyError` avec le nom
du champ : **exactement l'erreur d'avant, au même moment, avec le même
message**. Le passage à la dataclass n'ajoute aucune tolérance ; il ajoute
seulement la déclaration et le refus des clés inconnues.

Les seuls champs à vraie valeur par défaut sont ceux que le code lisait déjà
avec `kwargs.get("...", défaut)` : le défaut déclaré ici est celui qui y était
écrit, et `check_request_swap.py` refuse la conversion s'ils diffèrent.

Bibliothèque standard seulement.
"""
from dataclasses import dataclass, fields
from typing import Any


class _Missing:
    """Valeur d'un champ que l'appelant n'a pas fourni."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self):
        return "<non fourni>"

    def __bool__(self):
        raise KeyError(
            "un champ non fourni est testé comme booléen : donner la clé, "
            "ou déclarer un défaut sur le champ")


MISSING = _Missing()


@dataclass
class ProcessRequest:
    """Ce que tout outil reçoit. Les familles ajoutent leurs propres champs."""

    input_folder: str = MISSING
    output_folder: str = MISSING
    log_path: str = MISSING

    def __getattribute__(self, name):
        value = object.__getattribute__(self, name)
        if value is MISSING:
            # Le même KeyError que `kwargs["name"]` levait avant, pour que rien
            # ne change pour l'appelant qui l'attrapait -- ou ne l'attrapait pas.
            raise KeyError(name)
        return value

    def given(self, name):
        """Le champ a-t-il été fourni ? Sans lever, contrairement à l'accès."""
        return object.__getattribute__(self, name) is not MISSING

    def with_(self, **changes):
        """Une copie de la requête, quelques champs remplacés.

        `dataclasses.replace` ne convient pas ici : il relit tous les champs
        pour reconstruire l'objet, y compris ceux qui n'ont pas été fournis --
        et les lire lève, ce qui est précisément le but. Cette copie-ci lit les
        valeurs brutes, témoin d'absence compris.
        """
        raw = {f.name: object.__getattribute__(self, f.name) for f in fields(self)}
        raw.update(changes)
        return type(self)(**raw)

    def provided(self):
        """Les noms des champs effectivement fournis."""
        return sorted(f.name for f in fields(self) if self.given(f.name))


@dataclass
class ASORequest(ProcessRequest):
    """Les clés que lisent les quatre méthodes d'ASO."""

    gold_folder: str = MISSING
    add_in_namefile: str = MISSING
    dic_checkbox: Any = MISSING
    is_dicom_input: str = MISSING
    model_folder_ali: str = MISSING
    model_folder_segor: str = MISSING
    smallFOV: str = MISSING


@dataclass
class ALIRequest(ProcessRequest):
    """Les clés que lisent les deux méthodes d'ALI."""

    model_folder: str = MISSING
    lm_type: Any = MISSING
    teeth: Any = MISSING
    teeth_mg: Any = "None"          # lu par `kwargs.get`, defaut conserve tel quel
    is_dicom_input: str = MISSING


@dataclass
class AREGRequest(ProcessRequest):
    """Les clés que lisent les trois familles d'AREG, et leurs auxiliaires.

    `input_folder` n'y sert pas : AREG raisonne sur deux temps, T1 et T2.
    """

    input_t1_folder: str = ""
    input_t2_folder: str = ""
    input_t1_mask: str = MISSING
    input_t2_landmarks: str = MISSING
    model_folder_1: str = MISSING
    model_folder_2: str = MISSING
    model_folder_3: str = MISSING
    add_in_namefile: str = MISSING
    is_dicom_input: str = MISSING
    dic_checkbox: Any = MISSING
    merge_seg: Any = MISSING
    OrientReference: str = MISSING
    ApproxStep: Any = MISSING
    slicerDownload: Any = MISSING
    LabelSeg: Any = MISSING
    mgl_landmarks: str = ""
    patch_radius: str = "5.0"
    reg_type: Any = None            # ces trois-la etaient lus par `kwargs.get` :
                                    # le defaut declare ici est celui qui y etait


@dataclass
class VFACERequest(ProcessRequest):
    """Les clés que lit `CreateListProcess`, le point d'entrée unique de VFACE."""

    gold_folder: str = MISSING
    t2_folder: str = MISSING
    measurements_folder: str = MISSING
    model_folder: str = MISSING
    model_folder_ali: str = MISSING
    model_vface: str = MISSING
    mirror_matrix: Any = MISSING
    mode: str = MISSING
    mode2: str = MISSING
    reg_type: str = MISSING
    bool_quantification: Any = MISSING
    bool_visualization: Any = MISSING
