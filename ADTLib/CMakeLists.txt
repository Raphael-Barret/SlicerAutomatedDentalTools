#-----------------------------------------------------------------------------
# Shared Python code for every module of the extension.
#
# Built as a scripted module with no module of its own: the macro installs the
# listed files under qt-scripted-modules/ADTLib/, which Slicer has on sys.path,
# so `import ADTLib` works from any module, from a scripted CLI, and from the
# Conda environment once the search paths are published into it.
#
# Declared before its consumers in the top-level CMakeLists.txt.
#-----------------------------------------------------------------------------
set(MODULE_NAME ADTLib)

#-----------------------------------------------------------------------------
# Every file has to be listed: this is a manifest, nothing checks it against
# the source tree, and a file left out is simply absent from an installed
# build while it keeps working in a development tree.
set(MODULE_PYTHON_SCRIPTS
  ${MODULE_NAME}/__init__.py
  ${MODULE_NAME}/env/__init__.py
  ${MODULE_NAME}/env/install_pytorch.py
  ${MODULE_NAME}/format.py
)

#-----------------------------------------------------------------------------
slicerMacroBuildScriptedModule(
  NAME ${MODULE_NAME}
  SCRIPTS ${MODULE_PYTHON_SCRIPTS}
)
