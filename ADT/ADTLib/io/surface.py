"""Lire et écrire un maillage de surface, en un seul endroit.

`ReadSurf` existait en cinq exemplaires et `WriteSurf` en quatre, et contrairement
aux fonctions déjà partagées ici, **ceux-là avaient divergé**. Les différences
mesurées, et ce qui a été retenu :

`ReadSurf`
  - `ASO/IOS_utils/Reader.py` et `ASO_IOS_utils/utils.py` calculaient `fname` à
    partir de `basename(path)`. Le fichier `.mtl` d'un `.obj` était donc cherché
    dans le **répertoire courant**, pas à côté du maillage : la branche « avec
    matériau » ne se déclenchait pour ainsi dire jamais. Les trois autres
    gardaient le chemin complet, et c'est ce qui est retenu.
  - Ces deux mêmes copies posaient le chemin des textures dans un `if/else` dont
    les deux branches calculaient la même valeur — du code mort issu d'un
    copier-coller. Retenu : la forme des trois autres, qui ne pose le chemin
    `../images` que s'il existe.
  - `.off` n'était lu que par trois des cinq. Il l'est maintenant par toutes.
  - Une extension inconnue renvoyait `surf` jamais affecté, donc un
    `UnboundLocalError` opaque, dans trois copies sur cinq. `AREG_IOS` et
    `ALI_IOS` levaient déjà `ValueError` : retenu.
  - Un fichier absent ne faisait rien lever : les lecteurs VTK renvoient un
    maillage vide en silence, et l'erreur n'apparaissait que bien plus loin,
    dans le recalage. `ALI_IOS` vérifiait déjà l'existence et le nombre de
    points : retenu pour tout le monde. **C'est le seul changement qui peut
    faire échouer un traitement qui « passait » avant** — il échouait déjà, plus
    tard et sans dire pourquoi.

`WriteSurf`
  - `ASO_IOS_utils` choisissait le rédacteur d'après l'extension ; les autres
    écrivaient toujours du VTK hérité *sous le nom d'origine*, donc des octets
    VTK dans un fichier nommé `.vtp` ou `.obj`. Retenu : le rédacteur suit
    l'extension, et une extension sans rédacteur connu force `.vtk`, nom compris.
  - `os.mkdir` (trois copies) échoue si le parent manque et sur un dossier créé
    entre-temps par un autre processus : `os.makedirs(..., exist_ok=True)`.
  - Celle d'ASO ne prenait pas de `inname` et forçait `.vtk` quoi qu'il arrive.
    Le seul appel concerné convertit un maillage pour la segmentation, et c'est
    bien un `.vtk` qu'il veut : il le demande maintenant explicitement dans le
    nom qu'il passe, plutôt que la fonction le décide pour tous.

Importé depuis l'environnement Conda par les CLI : vtk suffit, Slicer et Qt ne
sont pas requis.
"""
import os

import vtk

from ADTLib.logging_setup import get_logger

logger = get_logger(__name__)


class OFFReader:
    """Lecteur OFF minimal, avec l'interface des lecteurs vtk.

    Les deux exemplaires (`ASO/IOS_utils/Reader.py`, `ASO_IOS_utils/OFFReader.py`)
    étaient identiques au caractère près, préambule de journalisation mis à part.
    Deux défauts corrigés au passage :

    - `__init__` affectait des variables locales `FileName` et `Output` au lieu
      des attributs, si bien qu'un `GetOutput()` avant `Update()` levait
      `AttributeError` au lieu de renvoyer `None` ;
    - un en-tête invalide faisait `raise ("Not a valid OFF header")`, c'est-à-dire
      lever une chaîne : `TypeError: exceptions must derive from BaseException`,
      qui masque le vrai message.
    """

    def __init__(self):
        self.FileName = None
        self.Output = None

    def SetFileName(self, file_name):
        self.FileName = file_name

    def GetOutput(self):
        return self.Output

    def Update(self):
        with open(self.FileName) as file:
            if "OFF" != file.readline().strip():
                raise ValueError(f"Not a valid OFF header: {self.FileName}")

            n_verts, n_faces, _ = tuple(
                [int(s) for s in file.readline().strip().split(" ")]
            )

            surf = vtk.vtkPolyData()
            points = vtk.vtkPoints()
            cells = vtk.vtkCellArray()

            for _ in range(n_verts):
                p = [float(s) for s in file.readline().strip().split(" ")]
                points.InsertNextPoint(p[0], p[1], p[2])

            for _ in range(n_faces):
                t = [int(s) for s in file.readline().strip().split(" ")]

                if t[0] == 1:
                    vertex = vtk.vtkVertex()
                    vertex.GetPointIds().SetId(0, t[1])
                    cells.InsertNextCell(vertex)
                elif t[0] == 2:
                    line = vtk.vtkLine()
                    line.GetPointIds().SetId(0, t[1])
                    line.GetPointIds().SetId(1, t[2])
                    cells.InsertNextCell(line)
                elif t[0] == 3:
                    triangle = vtk.vtkTriangle()
                    triangle.GetPointIds().SetId(0, t[1])
                    triangle.GetPointIds().SetId(1, t[2])
                    triangle.GetPointIds().SetId(2, t[3])
                    cells.InsertNextCell(triangle)

            surf.SetPoints(points)
            surf.SetPolys(cells)

            self.Output = surf


def _read_obj_with_material(file_name, fname):
    """Un `.obj` accompagné de son `.mtl`, importé puis aplati en un maillage."""
    obj_import = vtk.vtkOBJImporter()
    obj_import.SetFileName(file_name)
    obj_import.SetFileNameMTL(fname + ".mtl")
    textures_path = os.path.normpath(os.path.dirname(fname) + "/../images")
    if os.path.exists(textures_path):
        obj_import.SetTexturePath(textures_path)
    obj_import.Read()

    actors = obj_import.GetRenderer().GetActors()
    actors.InitTraversal()
    append = vtk.vtkAppendPolyData()
    for _ in range(actors.GetNumberOfItems()):
        surf_actor = actors.GetNextActor()
        append.AddInputData(surf_actor.GetMapper().GetInputAsDataSet())
    append.Update()
    return append.GetOutput()


def ReadSurf(file_name):
    """Le maillage contenu dans `fileName`, quel qu'en soit le format.

    Formats lus : `.vtk`, `.vtp`, `.stl`, `.off`, `.obj` (avec son `.mtl` s'il
    est à côté). Lève `FileNotFoundError` si le fichier manque, `ValueError` si
    l'extension n'est pas reconnue ou si le maillage lu est vide — les lecteurs
    vtk renvoyant un maillage vide plutôt qu'une erreur, c'est le seul moyen de
    distinguer « illisible » de « vide ».
    """
    if not os.path.exists(file_name):
        raise FileNotFoundError(f"File does not exist: {file_name}")

    fname, extension = os.path.splitext(file_name)
    extension = extension.lower()

    if extension == ".obj" and os.path.exists(fname + ".mtl"):
        surf = _read_obj_with_material(file_name, fname)
    else:
        if extension == ".vtk":
            reader = vtk.vtkPolyDataReader()
        elif extension == ".vtp":
            reader = vtk.vtkXMLPolyDataReader()
        elif extension == ".stl":
            reader = vtk.vtkSTLReader()
        elif extension == ".off":
            reader = OFFReader()
        elif extension == ".obj":
            reader = vtk.vtkOBJReader()
        else:
            raise ValueError(
                f"Unsupported file format: {extension}. Supported formats: "
                f".vtk, .vtp, .stl, .off, .obj. File: {file_name}"
            )
        reader.SetFileName(file_name)
        reader.Update()
        surf = reader.GetOutput()

    if surf.GetNumberOfPoints() == 0:
        raise ValueError(f"Surface has no points: {file_name}")

    logger.debug("Read %d points from %s", surf.GetNumberOfPoints(), file_name)
    return surf


# Quelle extension va avec quel rédacteur. Ce qui n'y figure pas est écrit en
# VTK hérité, et le nom de sortie prend `.vtk` pour ne pas mentir sur son
# contenu -- c'est ce que faisait déjà la copie d'ASO_IOS.
_WRITERS = {
    ".vtk": vtk.vtkPolyDataWriter,
    ".vtp": vtk.vtkXMLPolyDataWriter,
    ".obj": vtk.vtkOBJWriter,
}


def WriteSurf(surf, output_folder, name, inname=""):
    """Écrit `surf` dans `output_folder`, sous le nom de `name` suffixé d'`inname`.

    `name` peut être un chemin complet : seule sa fin est utilisée.
    `inname` s'insère entre le nom et l'extension, d'où `A2_Seg.vtk` + `Or`
    qui donne `A2_SegOr.vtk`. Renvoie le chemin écrit.
    """
    name = os.path.basename(name)
    name, extension = os.path.splitext(name)
    extension = extension.lower()
    if extension not in _WRITERS:
        extension = ".vtk"

    os.makedirs(output_folder, exist_ok=True)
    output_path = os.path.join(output_folder, f"{name}{inname}{extension}")

    writer = _WRITERS[extension]()
    writer.SetFileName(output_path)
    writer.SetInputData(surf)
    writer.Update()

    # vtk signale un échec d'écriture par un code de retour que personne ne lit,
    # et le traitement continuait sur un fichier absent.
    if not os.path.exists(output_path):
        raise RuntimeError(f"WriteSurf failed: {output_path} was not created")

    logger.debug("Wrote %s (%d bytes)", output_path, os.path.getsize(output_path))
    return output_path
