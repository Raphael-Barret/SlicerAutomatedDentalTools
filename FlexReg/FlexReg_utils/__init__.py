# These re-exports are a convenience for code running inside Slicer, where vtk
# and numpy are available. The package is also imported from the lean shapeaxi
# conda environment -- FlexReg_utils.install_pytorch needs nothing but the
# standard library -- and that environment has no vtk, so pulling these in
# unconditionally made every import of any submodule fail there.
try:
    from .util import ToothNoExist, NoSegmentationSurf
    from .orientation import orientation_f
except ImportError:
    pass
