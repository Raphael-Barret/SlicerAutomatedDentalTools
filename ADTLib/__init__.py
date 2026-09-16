"""Code shared by every module of the Automated Dental Tools extension.

Slicer puts each extension's `qt-scripted-modules` directory on `sys.path`, so
this package is reachable by a plain `import ADTLib` from any module of this
extension, from a scripted CLI, and -- once Slicer's module search paths are
published into it -- from inside the shapeaxi Conda environment. That last
route is what `ADTLib.env.install_pytorch` relies on: it is not imported by the
widgets, it is run as `python -m ADTLib.env.install_pytorch` by the Conda
interpreter.

Keep this file free of imports. Anything pulled in here runs in the lean Conda
environment too, which has neither vtk, nor qt, nor slicer; a single import of
one of those would break every submodule import there. Submodules that need
them import them themselves.
"""
