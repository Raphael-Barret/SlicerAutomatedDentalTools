#-----------------------------------------------------------------------------
set(MODULE_NAME CNE)

#-----------------------------------------------------------------------------
set(MODULE_PYTHON_SCRIPTS
  ${MODULE_NAME}.py
  )

# Les notes d'exemple sont copiees a l'execution depuis Resources/testfiles
# vers le dossier de telechargement de l'utilisateur (voir `CNE.py`). Elles
# manquaient au manifeste : le bouton d'exemple ne trouvait rien dans une
# install compilee.
set(MODULE_PYTHON_RESOURCES
  Resources/Icons/${MODULE_NAME}.png
  Resources/UI/${MODULE_NAME}.ui
  Resources/testfiles/input_TMJ/TMJ_note1.txt
  Resources/testfiles/input_TMJ/TMJ_note2.txt
  Resources/testfiles/input_Ortho/Ortho_note1.txt
  Resources/testfiles/input_Ortho/Ortho_note2.txt
  )

#-----------------------------------------------------------------------------
slicerMacroBuildScriptedModule(
  NAME ${MODULE_NAME}
  SCRIPTS ${MODULE_PYTHON_SCRIPTS}
  RESOURCES ${MODULE_PYTHON_RESOURCES}
  WITH_GENERIC_TESTS
  )

#-----------------------------------------------------------------------------
if(BUILD_TESTING)

  # Register the unittest subclass in the main script as a ctest.
  # Note that the test will also be available at runtime.
  slicer_add_python_unittest(SCRIPT ${MODULE_NAME}.py)

  # Additional build-time testing
  add_subdirectory(Testing)
endif()
