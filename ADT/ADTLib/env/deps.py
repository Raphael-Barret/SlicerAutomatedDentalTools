"""Is a library present, and does it satisfy the constraint the module asked for.

Nine modules carried their own `check_lib_installed`, under three incompatible
answers to the same question:

  - AREG and FlexReg: `if required_version: pass` -- true as soon as the library
    is installed at all, whatever version. The constraint was decoration.
  - ALI: exact equality against a bare version string (`'2.6.2'`).
  - MedX: a hand-rolled regex over one operator.
  - MRI2CBCT: `packaging.SpecifierSet`, which handles every PEP 440 form.

The last one is the only one that is both correct and complete, so it is the one
kept here. Constraints are now actually applied, which is the point: the pins
that were silently ignored are what let torch and pytorch3d drift apart.

Two spellings from the old call sites are accepted so no list has to be rewritten
in the same breath: a bare version (`'2.6.2'`) means `'==2.6.2'`, and a constraint
carried inside the name (`'numpy<2.0.0'`) is split off.

Standard library plus `packaging`, which Slicer ships.
"""
import importlib.metadata
import logging
import re

from packaging.specifiers import SpecifierSet
from packaging.version import Version

logger = logging.getLogger(__name__)

_NAME_WITH_SPEC = re.compile(r"^\s*([A-Za-z0-9_.\-]+)\s*([<>=!~].*)$")
_BARE_VERSION = re.compile(r"^\s*[0-9][0-9A-Za-z.\-+*]*\s*$")


def normalise_spec(lib_name, required_version=None):
    """(name, specifier) from the spellings the call sites use.

    Returns the specifier as a PEP 440 string, or None when the call site asked
    for no particular version.
    """
    embedded = _NAME_WITH_SPEC.match(lib_name or "")
    if embedded:
        lib_name, carried = embedded.group(1), embedded.group(2).strip()
        required_version = required_version or carried
    if required_version and _BARE_VERSION.match(required_version):
        # '2.6.2' meant '==2.6.2' at the one call site that wrote it that way.
        required_version = "==" + required_version.strip()
    return lib_name.strip(), (required_version.strip() if required_version else None)


def check_lib_installed(lib_name, required_version=None):
    """Whether `lib_name` is installed and satisfies `required_version`."""
    lib_name, required_version = normalise_spec(lib_name, required_version)
    try:
        installed = Version(importlib.metadata.version(lib_name))
    except importlib.metadata.PackageNotFoundError:
        logger.info("%s is not installed", lib_name)
        return False
    except Exception as error:                      # métadonnées illisibles
        logger.warning("could not read the version of %s: %s", lib_name, error)
        return False

    if not required_version:
        return True
    if installed in SpecifierSet(required_version):
        return True
    logger.info("%s %s does not satisfy %s", lib_name, installed, required_version)
    return False


def torch_cuda_builds_agree(libs=("torch", "torchvision", "torchaudio")):
    """Whether the installed torch family was all built against the same CUDA.

    A torch and a torchvision from different CUDA minors import fine and fail
    later, deep inside a model, with an `undefined symbol`. AMASSS was the only
    module checking this; the check belongs with the others.
    """
    seen = set()
    for name in libs:
        try:
            version = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            return False
        if "cu" not in version:
            return False
        seen.add(version.split("cu")[1])
    return len(seen) == 1
