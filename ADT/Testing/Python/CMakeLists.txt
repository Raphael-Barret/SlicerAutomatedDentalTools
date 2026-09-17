
# The identifier read off a file name, checked against the six chains it
# replaces: standard library only, no scan and no Slicer.
slicer_add_python_unittest(SCRIPT test_naming.py)

# check_lib_installed : les contraintes de version, et les orthographes heritees.
slicer_add_python_unittest(SCRIPT test_deps.py)

# ReadSurf, WriteSurf et OFFReader : les cinq copies divergeaient, ces cas
# figent ce qui a ete retenu et les quatre comportements qui changent.
slicer_add_python_unittest(SCRIPT test_surface.py)
