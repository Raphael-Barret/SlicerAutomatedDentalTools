
#slicer_add_python_unittest(SCRIPT ${MODULE_NAME}ModuleTest.py)

# La description d interface portee par chaque methode : les valeurs sont
# celles que la chaine de `if/elif` du widget decidait.
slicer_add_python_unittest(SCRIPT test_ui_description.py)
