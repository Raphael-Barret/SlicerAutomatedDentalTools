import numpy as np
import vtk
import logging
import sys
from ADTLib.geometry import ApplyTransform, RotationMatrix, TransformDict, TransformList, TransformSurf  # noqa: F401  (re-exporte)

# ===== Logging Configuration =====
logger = logging.getLogger("ASO_IOS_Transformation")
logger.setLevel(logging.INFO)
logger.propagate = False
if logger.handlers:
    logger.handlers.clear()
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(name)s - %(levelname)s - (%(filename)s:%(lineno)d) - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


def RotateTransform(surf, transform):
    transformFilter = vtk.vtkTransformPolyDataFilter()
    transformFilter.SetTransform(transform)
    transformFilter.SetInputData(surf)
    transformFilter.Update()
    return transformFilter.GetOutput()


def TranslationDict(source, transform):
    """
    Apply translation to source dictionary of landmarks

    Parameters
    ----------
    source : Dictionary
        Dictionary containing the source landmarks.
    transform : numpy array
        Translation to be applied to the source.

    Returns
    -------
    Dictionary
        Dictionary containing the translated source landmarks.
    """
    sourcee = source.copy()
    for key in sourcee.keys():
        sourcee[key] = sourcee[key] + transform
    return sourcee

